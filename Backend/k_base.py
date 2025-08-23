# M:\volunteering\Curate.Fun\chatbot\Backend\prepare_knowledge_base.py

import os
import pickle
import json
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document
from rank_bm25 import BM25Okapi
from dotenv import load_dotenv
from nltk import word_tokenize
import nltk
import os # Ensure os is imported for path operations

# NLTK Punkt tokenizer download (ensure this runs once)
try:
    nltk.data.find('tokenizers/punkt')
except nltk.downloader.DownloadError:
    nltk.download('punkt')

# Load environment variables
load_dotenv()

# Define paths
JSON_FILE_PATH = r"M:\volunteering\Curate.Fun\chatbot\backend\feeds_output\all_new_articles.json"
FAISS_DB_PATH = "db/faiss_index"
BM25_INDEX_PATH = "db/bm25_index.pkl"
ALL_DOCS_PATH = os.path.join("db", "all_article_docs.pkl") # Path to save raw documents

# Ensure the 'db' directory exists for storing indexes
os.makedirs("db", exist_ok=True)

# --- Helper function for loading data into documents ---
def load_data_into_documents(file_path):
    """
    Loads article data from the specified JSON file and converts each article
    into a Langchain Document using the 'combined_text_for_embedding' field,
    and also stores relevant metadata. Each Document represents a full article.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The file '{file_path}' does not exist. Please run your feed processing script first to create it.")
    
    # Check if file is empty
    if os.path.getsize(file_path) == 0:
        print(f"Warning: The JSON file '{file_path}' is empty. No documents to process.")
        return []

    with open(file_path, 'r', encoding='utf-8') as f:
        articles = json.load(f)
    
    documents = []
    for article in articles:
        # Construct the "embedding chunk" for each article including description and link
        combined_text_for_embedding = (
            f"Channel: {article.get('channel_title', '')}\n"
            f"Categories: {article.get('categories', '')}\n"
            f"Title: {article.get('title', '')}\n"
            f"Description: {article.get('description', '')}\n"
            f"Link: {article.get('link', '')}\n"
            f"Content: {article.get('content', '')}"
        )
        
        # Create a Document with the combined text as page_content
        # and useful metadata for context or source tracking.
        metadata = {
            "source": article.get("link", "unknown"),
            "title": article.get("title", ""),
            "channel_title": article.get("channel_title", ""),
            "publication_date": article.get("publication_date", ""),
            "categories": article.get("categories", ""),
            "original_description": article.get("description", ""),
            "guid": article.get("guid", "")
        }
        documents.append(Document(page_content=combined_text_for_embedding, metadata=metadata))
    
    return documents

# --- Main function to prepare the knowledge base ---
def prepare_knowledge_base(verbose=True):
    """
    Builds and saves the FAISS vector store and BM25 lexical index from article data.
    This function should be called as a separate process, not part of the main application runtime.
    """
    if verbose:
        print("--- Starting Knowledge Base Preparation ---")
        print(f"Loading article documents from: {JSON_FILE_PATH}")
    
    all_docs = load_data_into_documents(JSON_FILE_PATH)
    if not all_docs:
        print("No documents loaded. Aborting index creation.")
        return

    if verbose:
        print(f"Loaded {len(all_docs)} full article documents.")
        print(f"Saving full article documents to {ALL_DOCS_PATH}...")
    with open(ALL_DOCS_PATH, 'wb') as f:
        pickle.dump(all_docs, f)
    if verbose:
        print("Full article documents saved.")

    # Initialize Embeddings model (Mixedbread AI - mxbai-embed-large-v1)
    if verbose:
        print("Initializing Mixedbread AI Embeddings model (mxbai-embed-large-v1)...")
    embeddings_model = HuggingFaceEmbeddings(model_name="mixedbread-ai/mxbai-embed-large-v1")
    if verbose:
        print("Embeddings model initialized.")

    # Create and save FAISS index (generating embeddings here)
    if verbose:
        print("Creating FAISS vector store (this generates embeddings for each article)...")
    faiss_db = FAISS.from_documents(all_docs, embeddings_model)
    if verbose:
        print("FAISS vector store created.")
        print(f"Saving FAISS index to {FAISS_DB_PATH}...")
    faiss_db.save_local(FAISS_DB_PATH)
    if verbose:
        print("FAISS index saved.")

    # Create and save BM25 index
    if verbose:
        print("Creating BM25 lexical index...")
    corpus = [doc.page_content for doc in all_docs]
    tokenized_corpus_for_bm25 = [word_tokenize(doc.lower()) for doc in corpus]
    bm25_index = BM25Okapi(tokenized_corpus_for_bm25)
    if verbose:
        print("BM25 lexical index created.")
        print(f"Saving BM25 lexical index to {BM25_INDEX_PATH}...")
    with open(BM25_INDEX_PATH, 'wb') as f:
        pickle.dump(bm25_index, f)
    if verbose:
        print("BM25 lexical index saved.")
    
    if verbose:
        print("--- Knowledge Base Preparation Complete ---")

if __name__ == "__main__":
    prepare_knowledge_base(verbose=True)