import feedparser
import re
import os
from bs4 import BeautifulSoup
import hashlib

# === CONFIG ===
urls = [
    "https://grants-rss.up.railway.app/rss.xml",
    "https://ethereum-rss.up.railway.app/rss.xml",
    "https://near-rss.up.railway.app/rss.xml",
    "https://solana-rss.up.railway.app/rss.xml",
    "https://eigen-rss.up.railway.app/rss.xml",
    "https://abstraction-rss.up.railway.app/rss.xml",
    "https://afrobeats-rss.up.railway.app/rss.xml",
    "https://usa-rss.up.railway.app/rss.xml",
    "https://shippost-rss.up.railway.app/rss.xml",
    "https://sui-rss.up.railway.app/rss.xml",
    "https://stablecoins-rss.up.railway.app/rss.xml",
    "https://xpostbounty1-rss.up.railway.app/rss.xml"
]

output_dir = "feeds_output"
all_new_articles_txt_file = os.path.join(output_dir, "all_new_articles.txt")
seen_guids_file = os.path.join(output_dir, "seen_guids.txt")

# === HELPERS ===

def safe_filename(name):
    return re.sub(r'\W+', '_', name).strip('_')

def contains_html_tags(text):
    # This helper is now less critical for the final output as 'content' is removed,
    # but still used by 'clean_content' which might process 'description' if it contains HTML
    return bool(re.search(r'<[^>]+>', text))

def convert_html_to_labeled_text(html_content):
    # This function is now effectively unused if 'content' is removed and 'description' is plain text
    # but kept for completeness if 'description' *could* contain HTML and needs cleaning.
    soup = BeautifulSoup(html_content, 'html.parser')
    output_lines = []
    for element in soup.descendants:
        if element.name and element.string and element.string.strip():
            text = element.string.strip()
            if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                output_lines.append(f"Heading: {text}")
            elif element.name == 'p':
                output_lines.append(f"Paragraph: {text}")
    return "\n".join(output_lines)

def clean_content(html_content):
    # This function will now process the description if it contains HTML
    return convert_html_to_labeled_text(html_content) if contains_html_tags(html_content) else html_content.strip()

def load_seen_guids(filepath):
    if not os.path.exists(filepath):
        return set()
    with open(filepath, "r", encoding="utf-8") as f:
        return {line.strip() for line in f if line.strip()}

def save_seen_guids(filepath, guids_set):
    with open(filepath, "w", encoding="utf-8") as f:
        for guid in sorted(list(guids_set)):
            f.write(f"{guid}\n")

def get_article_id(entry):
    guid = entry.get("guid")
    if guid and ("http" in guid or len(guid) > 10):
        return guid

    entry_id = entry.get("id")
    if entry_id and ("http" in entry_id or len(entry_id) > 10):
        return entry_id

    link = entry.get("link", "")
    title = entry.get("title", "")
    pub_date = entry.get("published", "")
    unique_string = f"{link}-{title}-{pub_date}"
    return hashlib.sha256(unique_string.encode('utf-8')).hexdigest()

def download_and_extract_new_articles(url, seen_guids, new_guids_this_run):
    feed = feedparser.parse(url)
    channel = feed.feed
    channel_title = channel.get("title", "Untitled")

    articles_from_this_feed = []
    new_articles_count = 0

    for entry in feed.entries:
        item_id = get_article_id(entry)
        if item_id in seen_guids:
            continue

        new_articles_count += 1
        new_guids_this_run.add(item_id)

        # Content and description can sometimes be interchangeable or one might be empty.
        # We'll prioritize description as requested.
        # Ensure description is cleaned in case it contains HTML.
        raw_description = entry.get("description", "").strip()
        cleaned_description = clean_content(raw_description) # Apply cleaning logic to description

        categories_list = [tag["term"] for tag in entry.tags] if "tags" in entry else []
        categories_str = ", ".join(categories_list)

        item_title = entry.get("title", "Untitled Item")

        article_data = {
            "channel_title": channel_title,
            "title": item_title,
            "link": entry.get("link", ""),
            "guid": item_id,
            "publication_date": entry.get("published", ""),
            "description": cleaned_description, # Keeping description
            # "content": cleaned_content, # Removed as per your request
            "categories": categories_str
        }
        articles_from_this_feed.append(article_data)

    print(f"✅ Processed feed '{channel_title}': Found {new_articles_count} new articles.")
    return articles_from_this_feed, new_articles_count

# === MODIFIED: Save to .txt to remove quotes and keep description, remove content ===
def save_articles_to_txt(articles, filepath):
    with open(filepath, "a", encoding="utf-8") as f: # Append new articles to the end
        for article in articles:
            # Prepare description for output. If it's multi-line, add indentation.
            # Replace internal newlines with a newline followed by space for indentation
            formatted_description = article["description"].replace("\n", "\n ")

            f.write(f'channel_title: {article["channel_title"]},\n')
            f.write(f'title: {article["title"]},\n')
            f.write(f'link: {article["link"]},\n')
            # f.write(f'guid: {article["guid"]},\n')
            f.write(f'publication_date: {article["publication_date"]},\n')
            f.write(f'description: {formatted_description},\n') # Keeping description
            # f.write(f' content: {article["content"].replace("\\n", "\\n ")}\n') # Removed content
            f.write(f'categories: {article["categories"]}\n')
            f.write(" " * 100 + "\n\n") # Separator between articles
    print(f"📝 Appended {len(articles)} new articles to plain text file: {filepath}")


# === MAIN WORKFLOW ===

def main():
    os.makedirs(output_dir, exist_ok=True)

    seen_guids = load_seen_guids(seen_guids_file)
    print(f"Loaded {len(seen_guids)} previously seen article IDs.")

    new_guids_this_run = set()
    all_new_articles_data_list = []

    print("🚀 Downloading & Processing Feeds...")
    for url in urls:
        new_articles_from_feed, articles_count = download_and_extract_new_articles(url, seen_guids, new_guids_this_run)
        all_new_articles_data_list.extend(new_articles_from_feed)

    total_new_articles_found = len(all_new_articles_data_list)
    print(f"\nTotal unique new articles found this run: {total_new_articles_found}")

    seen_guids.update(new_guids_this_run)
    save_seen_guids(seen_guids_file, seen_guids)
    print(f"Updated {len(seen_guids)} total seen article IDs in {seen_guids_file}")

    if total_new_articles_found > 0:
        save_articles_to_txt(all_new_articles_data_list, all_new_articles_txt_file)
    else:
        print("\nNo new articles found this run to save.")

    print("\n🎉 All Done.")

if __name__ == "__main__":
    main()