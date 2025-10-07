import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re

BASE_URL = "https://rdm.vu.nl/topics.html"
OUTPUT_FILE = "rdm_vu_topics.txt"


def clean_text(text):
    """Clean and normalize extracted text for LLM ingestion."""
    text = re.sub(r'\s+', ' ', text)  # collapse whitespace
    text = re.sub(r'(?m)^\s*$', '', text)  # remove empty lines
    return text.strip()


def get_page_text(url):
    """Fetch page and extract readable text."""
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        print(f"[WARN] Could not fetch {url}: {e}")
        return ""

    soup = BeautifulSoup(resp.text, "html.parser")

    # Remove scripts, styles, and nav elements
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
        tag.decompose()

    # Extract visible text
    texts = soup.stripped_strings
    full_text = " ".join(texts)
    return clean_text(full_text)


def get_topic_links():
    """Extract topic links from the main topics page."""
    resp = requests.get(BASE_URL)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        full_url = urljoin(BASE_URL, href)
        # Filter only pages within the same domain
        if urlparse(full_url).netloc.endswith("vu.nl"):
            links.add(full_url)

    return sorted(links)


def main():
    print("[INFO] Fetching topic links...")
    topic_links = get_topic_links()
    print(f"[INFO] Found {len(topic_links)} topic pages.")

    all_texts = []
    for i, url in enumerate(topic_links, 1):
        print(f"[{i}/{len(topic_links)}] Scraping {url}")
        page_text = get_page_text(url)
        if page_text:
            all_texts.append(f"### Page: {url}\n\n{page_text}\n")

    combined_text = "\n\n".join(all_texts)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(combined_text)

    print(f"\n✅ Done! Saved all text to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
