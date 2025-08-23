# M:\volunteering\Curate.Fun\chatbot\Backend\retriever_module.py

import os
import pickle
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings # For Mixedbread AI embeddings
from langchain.schema import Document # Needed for type hinting Document objects
from rank_bm25 import BM25Okapi # Needed for BM25 type hinting
from dotenv import load_dotenv
from nltk import word_tokenize
import nltk
import json # Added for parsing LLM's strategy decision
from openai import OpenAI # Added for type hinting and using LLM client

# NLTK Punkt tokenizer download (ensure this runs once)
try:
    nltk.data.find('tokenizers/punkt')
except nltk.downloader.DownloadError:
    nltk.download('punkt')

# Load environment variables
load_dotenv()

# Define paths (must match prepare_knowledge_base.py)
FAISS_DB_PATH = "db/faiss_index"
BM25_INDEX_PATH = "db/bm25_index.pkl"
ALL_DOCS_PATH = os.path.join("db", "all_article_docs.pkl")

# Configuration Constants for RAG
K_RETRIEVAL = 10 # Number of articles to retrieve from each method (FAISS, BM25)
RRF_K_CONSTANT = 60 # Constant for Reciprocal Rank Fusion
K_FINAL_CONTEXT = 5 # Limit to top N articles for LLM context after fusion and deduplication

# --- Helper functions (remain here for retrieval logic) ---

def reciprocal_rank_fusion(ranked_lists, k=RRF_K_CONSTANT):
    """
    Performs Reciprocal Rank Fusion (RRF) on multiple ranked lists of documents.
    Combines scores from different retrieval methods (e.g., semantic and lexical).
    Documents that rank highly in multiple lists get a higher fused score.
    """
    fused_scores = {}
    doc_map = {} 

    for rank_list in ranked_lists:
        for rank, (doc, _) in enumerate(rank_list):
            doc_key = hash(doc.page_content) # Use content hash as a unique key for the document
            if doc_key not in fused_scores:
                fused_scores[doc_key] = 0.0
            fused_scores[doc_key] += 1.0 / (k + rank + 1)
            doc_map[doc_key] = doc # Store the document itself for retrieval later

    # Sort documents by their fused scores in descending order
    final_results = []
    for doc_key, score in sorted(fused_scores.items(), key=lambda item: item[1], reverse=True):
        final_results.append((doc_map[doc_key], score))
    return final_results

def deduplicate_chunks(ranked_chunks_with_scores, embeddings_model, similarity_threshold=0.98, verbose=False):
    """
    Deduplicates a list of ranked document chunks based on semantic similarity.
    Removes exact and near-duplicate chunks to provide cleaner context to the LLM,
    reducing redundancy and token usage.
    """
    if not ranked_chunks_with_scores:
        return []

    deduplicated_results = []
    processed_contents = set() # To track exact duplicates by content string
    processed_embeddings = [] # To track embeddings of unique chunks for near-duplicate check

    if verbose:
        print(f"Starting deduplication. Initial chunks: {len(ranked_chunks_with_scores)}")

    for i, (current_doc, current_score) in enumerate(ranked_chunks_with_scores):
        current_content = current_doc.page_content
        
        # 1. Check for exact duplicate first (most efficient check)
        if current_content in processed_contents:
            if verbose:
                print(f"    Skipping exact duplicate: {current_content[:50]}...")
            continue

        # 2. Generate embedding for the current chunk to check for near-duplicates
        current_embedding = embeddings_model.embed_query(current_content)
        is_near_duplicate = False
        if processed_embeddings:
            current_embedding_np = np.array(current_embedding).reshape(1, -1)
            processed_embeddings_np = np.array(processed_embeddings)
            # Calculate cosine similarity with all already processed unique embeddings
            similarities = cosine_similarity(current_embedding_np, processed_embeddings_np)[0]
            if np.max(similarities) > similarity_threshold:
                is_near_duplicate = True
                if verbose:
                    print(f"    Skipping near duplicate (similarity > {similarity_threshold:.2f}): {current_content[:50]}...")

        # If not an exact or near duplicate, add to results and track it
        if not is_near_duplicate:
            deduplicated_results.append((current_doc, current_score))
            processed_contents.add(current_content)
            processed_embeddings.append(current_embedding)

    if verbose:
        print(f"Deduplication complete. Remaining chunks: {len(deduplicated_results)}")
    return deduplicated_results


# --- Class to hold retriever instances and their associated data ---
class RetrieverManager:
    """
    Manages the initialized FAISS vector store, BM25 lexical index,
    the list of documents (full articles), and the embeddings model.
    This class acts as a container for all components needed for retrieval.
    """
    def __init__(self, faiss_db: FAISS, bm25_index: BM25Okapi, all_docs: list[Document], embeddings_model: HuggingFaceEmbeddings):
        self.faiss_db = faiss_db
        self.bm25_index = bm25_index
        self.all_docs = all_docs # Full list of all article documents
        self.embeddings_model = embeddings_model

# --- Initialization function to return RetrieverManager instance (LOADS ONLY) ---
def initialize_retrievers(verbose=True) -> RetrieverManager:
    """
    Loads the FAISS vector store and BM25 lexical index from disk.
    This function should be called once at application startup.
    It expects the indexes to have been pre-built by prepare_knowledge_base.py.
    """
    if verbose:
        print("\n--- Initializing RAG Retriever Module ---")

    # Initialize Embeddings model (needed for FAISS.load_local and deduplication)
    if verbose:
        print("Initializing Mixedbread AI Embeddings model (mxbai-embed-large-v1) for retrieval...")
    _embeddings_model = HuggingFaceEmbeddings(model_name="mixedbread-ai/mxbai-embed-large-v1")
    if verbose:
        print("Embeddings model initialized.")

    # Check if all components exist on disk to load them
    faiss_db_exists = os.path.exists(FAISS_DB_PATH) and os.path.isdir(FAISS_DB_PATH)
    bm25_index_exists = os.path.exists(BM25_INDEX_PATH) and os.path.getsize(BM25_INDEX_PATH) > 0 # Check size > 0
    all_docs_exists = os.path.exists(ALL_DOCS_PATH) and os.path.getsize(ALL_DOCS_PATH) > 0 # Check size > 0

    if not (faiss_db_exists and bm25_index_exists and all_docs_exists):
        missing_components = []
        if not faiss_db_exists: missing_components.append(f"FAISS index ({FAISS_DB_PATH})")
        if not bm25_index_exists: missing_components.append(f"BM25 index ({BM25_INDEX_PATH})")
        if not all_docs_exists: missing_components.append(f"All article documents ({ALL_DOCS_PATH})")
        
        error_message = (
            f"❌ RAG Initialization Failed: Missing or empty knowledge base components. "
            f"Please run `python prepare_knowledge_base.py` first to build the indexes. "
            f"Missing: {', '.join(missing_components)}"
        )
        print(error_message)
        raise FileNotFoundError(error_message)

    try:
        if verbose:
            print(f"Loading FAISS index from {FAISS_DB_PATH}...")
        _faiss_db = FAISS.load_local(FAISS_DB_PATH, _embeddings_model, allow_dangerous_deserialization=True)
        if verbose:
            print("FAISS index loaded.")

        if verbose:
            print(f"Loading BM25 lexical index from {BM25_INDEX_PATH}...")
        with open(BM25_INDEX_PATH, 'rb') as f:
            _bm25_index = pickle.load(f)
        if verbose:
            print("BM25 lexical index loaded.")
        
        if verbose:
            print(f"Loading all article documents from {ALL_DOCS_PATH}...")
        with open(ALL_DOCS_PATH, 'rb') as f:
            _all_docs = pickle.load(f)
        if verbose:
            print("All article documents loaded.")

    except Exception as e:
        error_message = (
            f"❌ RAG Initialization Failed: Error loading existing indexes. "
            f"Details: {e}. "
            f"Consider deleting the 'db' folder and running `python prepare_knowledge_base.py` again."
        )
        print(error_message)
        raise RuntimeError(error_message)

    if verbose:
        print("--- RAG Retriever Module Initialized Successfully ---")
    return RetrieverManager(_faiss_db, _bm25_index, _all_docs, _embeddings_model)


# --- Main RAG Context Retrieval Function ---
def retrieve_context(query: str, retriever_manager: RetrieverManager, retrieval_strategy: str = "hybrid", verbose=False) -> str:
    """
    Retrieves relevant article documents based on the specified retrieval strategy.
    Strategies: "semantic", "lexical", "hybrid".
    """
    faiss_db = retriever_manager.faiss_db
    bm25_index = retriever_manager.bm25_index
    embeddings_model = retriever_manager.embeddings_model
    all_docs = retriever_manager.all_docs # Full list of all article documents for BM25 lookup

    if verbose:
        print(f"Starting RAG context retrieval for query: '{query}' with strategy: '{retrieval_strategy}'")

    retrieved_docs_with_scores = []

    if retrieval_strategy == "semantic":
        # 1. Semantic Search (FAISS)
        if verbose:
            print(f"    Performing semantic search for top {K_RETRIEVAL} articles...")
        semantic_results_with_distances = faiss_db.similarity_search_with_score(query, k=K_RETRIEVAL)
        for doc, distance in semantic_results_with_distances:
            similarity_score = 1.0 / (distance + 1e-5) # Convert distance to a similarity-like score
            retrieved_docs_with_scores.append((doc, similarity_score))
        if verbose:
            print(f"    Semantic search found {len(retrieved_docs_with_scores)} results.")

    elif retrieval_strategy == "lexical":
        # 2. Lexical Search (BM25)
        if verbose:
            print(f"    Performing lexical search for top {K_RETRIEVAL} articles using BM25...")
        tokenized_query_for_bm25 = word_tokenize(query.lower())
        doc_scores = bm25_index.get_scores(tokenized_query_for_bm25)
        
        scored_docs_bm25 = sorted(zip(doc_scores, all_docs), key=lambda x: x[0], reverse=True)
        retrieved_docs_with_scores = [(doc, score) for score, doc in scored_docs_bm25[:K_RETRIEVAL]]
        if verbose:
            print(f"    Lexical search found {len(retrieved_docs_with_scores)} results.")

    elif retrieval_strategy == "hybrid":
        # 1. Semantic Search (FAISS)
        if verbose:
            print(f"    Performing semantic search for top {K_RETRIEVAL} articles...")
        semantic_results_with_distances = faiss_db.similarity_search_with_score(query, k=K_RETRIEVAL)
        semantic_ranked = []
        for doc, distance in semantic_results_with_distances:
            similarity_score = 1.0 / (distance + 1e-5)
            semantic_ranked.append((doc, similarity_score))
        if verbose:
            print(f"    Semantic search found {len(semantic_ranked)} results.")

        # 2. Lexical Search (BM25)
        if verbose:
            print(f"    Performing lexical search for top {K_RETRIEVAL} articles using BM25...")
        tokenized_query_for_bm25 = word_tokenize(query.lower())
        doc_scores = bm25_index.get_scores(tokenized_query_for_bm25)
        
        scored_docs_bm25 = sorted(zip(doc_scores, all_docs), key=lambda x: x[0], reverse=True)
        lexical_ranked = [(doc, score) for score, doc in scored_docs_bm25[:K_RETRIEVAL]]
        if verbose:
            print(f"    Lexical search found {len(lexical_ranked)} results.")

        # 3. Hybrid Search (RRF Fusion)
        if verbose:
            print("    Fusing semantic and lexical search results using RRF...")
        retrieved_docs_with_scores = reciprocal_rank_fusion([semantic_ranked, lexical_ranked], k=RRF_K_CONSTANT)
        if verbose:
            print(f"    Hybrid search (fused) found {len(retrieved_docs_with_scores)} results before deduplication.")
    else:
        print(f"WARNING: Unknown retrieval strategy '{retrieval_strategy}'. Defaulting to 'hybrid'.")
        # Fallback to hybrid if an invalid strategy is provided
        # This block is a copy of the 'hybrid' logic to ensure it runs
        if verbose:
            print(f"    Performing semantic search for top {K_RETRIEVAL} articles...")
        semantic_results_with_distances = faiss_db.similarity_search_with_score(query, k=K_RETRIEVAL)
        semantic_ranked = []
        for doc, distance in semantic_results_with_distances:
            similarity_score = 1.0 / (distance + 1e-5)
            semantic_ranked.append((doc, similarity_score))
        if verbose:
            print(f"    Semantic search found {len(semantic_ranked)} results.")

        if verbose:
            print(f"    Performing lexical search for top {K_RETRIEVAL} articles using BM25...")
        tokenized_query_for_bm25 = word_tokenize(query.lower())
        doc_scores = bm25_index.get_scores(tokenized_query_for_bm25)
        
        scored_docs_bm25 = sorted(zip(doc_scores, all_docs), key=lambda x: x[0], reverse=True)
        lexical_ranked = [(doc, score) for score, doc in scored_docs_bm25[:K_RETRIEVAL]]
        if verbose:
            print(f"    Lexical search found {len(lexical_ranked)} results.")

        if verbose:
            print("    Fusing semantic and lexical search results using RRF...")
        retrieved_docs_with_scores = reciprocal_rank_fusion([semantic_ranked, lexical_ranked], k=RRF_K_CONSTANT)
        if verbose:
            print(f"    Hybrid search (fused) found {len(retrieved_docs_with_scores)} results before deduplication.")


    # 4. Deduplicate Fused/Selected Results
    if verbose:
        print("    Deduplicating selected search results...")
    deduplicated_final_results = deduplicate_chunks(retrieved_docs_with_scores, embeddings_model, similarity_threshold=0.98, verbose=verbose)
    if verbose:
        print(f"    Final results after deduplication: {len(deduplicated_final_results)} articles.")

    # Apply final cutoff (K_FINAL_CONTEXT) and combine content into a single string
    context_string = "\n\n---\n\n".join([doc.page_content for doc, _ in deduplicated_final_results[:K_FINAL_CONTEXT]])
    
    if verbose:
        print("RAG context retrieval complete.")
    return context_string
