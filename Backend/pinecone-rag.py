from pinecone import Pinecone,ServerlessSpec
import os,re
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

load_dotenv()

PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY_")
EMBEDDING_MODEL_NAME = 'mixedbread-ai/mxbai-embed-large-v1'
EXPECTED_EMBEDDING_DIMENSION = 512
pc = Pinecone(api_key=PINECONE_API_KEY)
PINECONE_INDEX_NAME = "curate-fun"
PINECONE_ENVIRONMENT = "us-east-1"

index = pc.Index(name=PINECONE_INDEX_NAME)

TXT_FILE_PATH = "feeds_output/all_new_articles.txt" # Path to your generated TXT file
BATCH_SIZE = 100 

def load_articles_from_txt(filepath):
    """
    Loads article data from the custom plain text file.
    Assumes each article is separated by one or more blank lines.
    Each field is expected to be on its own line in 'key: value,' format.
    Uses 'link' as the unique ID for Pinecone.
    """
    articles = []
    current_article_fields = {} # Using a dict to store fields for the current article

    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()

            if not line:  # A blank line signifies the end of an article
                if current_article_fields: # Only process if we've collected fields for an article
                    # Populate the 'guid' field with the 'link' as the unique ID
                    final_article = {
                        "channel_title": current_article_fields.get("channel_title", "").strip(),
                        "title": current_article_fields.get("title", "").strip(),
                        "link": current_article_fields.get("link", "").strip(),
                        "guid": current_article_fields.get("link", "").strip(), # Using link as the Pinecone ID
                        "publication_date": current_article_fields.get("publication_date", "").strip(),
                        "description": current_article_fields.get("description", "").strip(),
                        "categories": current_article_fields.get("categories", "").strip(),
                    }
                    articles.append(final_article)
                current_article_fields = {} # Reset for the next article
                continue # Skip further processing for blank lines

            # Regex to match "key: value," or "key: value"
            # It captures everything after the first colon as the value.
            match = re.match(r'^(.*?):\s*(.*?),?$', line)
            if match:
                key = match.group(1).strip()
                value = match.group(2).strip()
                current_article_fields[key] = value
            else:
                # This 'else' block would catch lines that don't fit the 'key: value' pattern.
                # Given your example, each field is on its own line and matches the pattern.
                # If you have multi-line descriptions that don't start with a new key,
                # this logic would need to be more complex (e.g., appending to the 'description' field).
                # For now, based on your provided examples, this should work.
                print(f"⚠️ Warning: Unrecognized line format, skipping: '{line}'")


    # After the loop, add the last article if the file doesn't end with a blank line
    if current_article_fields:
        final_article = {
            "channel_title": current_article_fields.get("channel_title", "").strip(),
            "title": current_article_fields.get("title", "").strip(),
            "link": current_article_fields.get("link", "").strip(),
            "guid": current_article_fields.get("link", "").strip(),
            "publication_date": current_article_fields.get("publication_date", "").strip(),
            "description": current_article_fields.get("description", "").strip(),
            "categories": current_article_fields.get("categories", "").strip(),
        }
        articles.append(final_article)

    # Validate and filter articles (must have link and description)
    validated_articles = []
    seen_ids = set() # To ensure unique IDs (links)
    for art in articles:
        if art.get("link") and art.get("description"):
            # Check for uniqueness of the link being used as ID
            if art["link"] not in seen_ids:
                validated_articles.append(art)
                seen_ids.add(art["link"])
            else:
                print(f"⚠️ Skipping duplicate article (same link): {art.get('title', 'Untitled Article')} - {art.get('link')}")
        else:
            print(f"⚠️ Skipping article due to missing link or description: {art.get('title', 'Untitled Article')}")
    return validated_articles

def generate_embeddings(texts, model_name):
    """
    Generates sentence embeddings for a list of texts using SentenceTransformer.
    """
    print(f"🤖 Loading embedding model: {model_name}...")
    try:
        model = SentenceTransformer(model_name)
    except Exception as e:
        print(f"❌ Error loading model '{model_name}': {e}")
        print("Please ensure the model name is correct and you have an internet connection.")
        return None
    
    print(f"✅ Model loaded. Model dimension: {model.get_sentence_embedding_dimension()}")
    
    # Check if the model's output dimension matches what we expect
    if model.get_sentence_embedding_dimension() != EXPECTED_EMBEDDING_DIMENSION:
        print(f"🚨 ERROR: Model '{model_name}' outputs {model.get_sentence_embedding_dimension()} dimensions,")
        print(f"but your configuration expects {EXPECTED_EMBEDDING_DIMENSION} dimensions.")
        print("You MUST either:")
        print(f"1. Recreate your Pinecone index '{PINECONE_INDEX_NAME}' with dimension {model.get_sentence_embedding_dimension()}.")
        print("2. Find and use an embedding model that outputs exactly", EXPECTED_EMBEDDING_DIMENSION, "dimensions.")
        return None # Stop execution

    print("Generating embeddings...")
    # Using convert_to_numpy=True for direct conversion to list later
    embeddings = model.encode(texts, show_progress_bar=True, convert_to_numpy=True)
    return embeddings

def upsert_to_pinecone(articles_data, embeddings, pinecone_api_key, pinecone_environment, index_name, batch_size):
    """
    Connects to Pinecone and upserts article embeddings and metadata.
    """
    if not pinecone_api_key:
        print("❌ Pinecone API key not found in .env. Skipping Pinecone upsert.")
        return

    try:
        pc = Pinecone(api_key=pinecone_api_key, environment=pinecone_environment)
        print(f"🚀 Connected to Pinecone in environment: {pinecone_environment}")
    except Exception as e:
        print(f"❌ Error initializing Pinecone client: {e}. Skipping upsert.")
        return

    try:
        # Check if index exists and get its description
        if index_name not in pc.list_indexes().names():
            print(f"❌ Pinecone index '{index_name}' does not exist.")
            print("Please create it in your Pinecone dashboard with the correct dimension and metric.")
            return

        index = pc.Index(index_name)
        index_stats = index.describe_index_stats()
        print(f"✅ Connected to Pinecone index: '{index_name}'")
        print(f"Current Pinecone index stats: {index_stats}")
        
        # Verify index dimension again for safety (after model output check)
        if index_stats.dimension != embeddings.shape[1]:
             print(f"🚨 FATAL ERROR: Pinecone index '{index_name}' dimension ({index_stats.dimension}) does not match the generated embedding dimension ({embeddings.shape[1]}).")
             print("Please recreate your Pinecone index with the correct dimension or select a different embedding model.")
             return


    except Exception as e:
        print(f"❌ Error connecting to or describing Pinecone index '{index_name}': {e}. Skipping upsert.")
        return

    vectors_to_upsert = []
    for i, article in enumerate(articles_data):
        # article["guid"] now holds the link, which will be the Pinecone ID
        article_id = article["guid"]
        vector = embeddings[i].tolist() # Convert NumPy array to Python list

        # Prepare metadata: Clean keys, handle categories list
        metadata = {
            "channel_title": article.get("channel_title"),
            "title": article.get("title"),
            "link": article.get("link"), # Link is also stored in metadata
            "publication_date": article.get("publication_date"),
            # Parse categories string into a list of strings
            "categories": [c.strip() for c in article.get("categories", "").split(',') if c.strip()],
            "description_text": article.get("description") # Store original text for display
        }
        # Remove any metadata fields that are None or empty lists (Pinecone doesn't like None)
        metadata = {k: v for k, v in metadata.items() if v is not None and (not isinstance(v, list) or len(v) > 0)}

        vectors_to_upsert.append((article_id, vector, metadata))

    print(f"📦 Preparing to upsert {len(vectors_to_upsert)} vectors to Pinecone in batches of {batch_size}...")
    for i in range(0, len(vectors_to_upsert), batch_size):
        batch = vectors_to_upsert[i:i + batch_size]
        try:
            index.upsert(vectors=batch)
            print(f"✅ Upserted batch {i // batch_size + 1}/{(len(vectors_to_upsert) + batch_size - 1) // batch_size} ({len(batch)} vectors).")
        except Exception as e:
            print(f"❌ Error upserting batch starting at {i} (ID: {batch[0][0]}): {e}")
            # You might want more sophisticated error handling here, like logging failed IDs
            # or retrying specific batches.

    print("🎉 All eligible articles upserted to Pinecone!")

# --- Main Execution ---
if __name__ == "__main__":
    if not os.path.exists("feeds_output"):
        os.makedirs("feeds_output") # Create directory if it doesn't exist

    if not os.path.exists(TXT_FILE_PATH):
        print(f"❌ Error: Article text file not found at {TXT_FILE_PATH}")
        print("Please ensure your RSS script has run and generated this file.")
        print("The article format should have 'link:' field for unique ID.")
        exit()

    print("Starting Pinecone Uploader process...")

    articles_data = load_articles_from_txt(TXT_FILE_PATH)
    print(f"📖 Loaded {len(articles_data)} articles from {TXT_FILE_PATH}")

    if articles_data:
        # Extract descriptions for embedding
        texts_for_embeddings = [article["description"] for article in articles_data]

        # Generate embeddings
        embeddings = generate_embeddings(texts_for_embeddings, EMBEDDING_MODEL_NAME)
        
        if embeddings is None: # Exit if embedding generation failed (e.g., dimension mismatch)
            print("Embedding generation failed. Exiting.")
            exit()

        # Upsert to Pinecone
        upsert_to_pinecone(
            articles_data,
            embeddings,
            PINECONE_API_KEY,
            PINECONE_ENVIRONMENT,
            PINECONE_INDEX_NAME,
            BATCH_SIZE
        )
    else:
        print("No articles found in the text file to process for Pinecone.")

    print("\nProcess complete.")
