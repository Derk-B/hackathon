import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re

BASE_URL = "https://rdm.vu.nl/topics.html"
BASE_URL2 = "https://rdm.vu.nl/topics#listing-listing-page=2"
OUTPUT_FILE = "rdm_vu_knowledge_base.txt"


def clean_text(text):
    """Clean and normalize extracted text for LLM ingestion."""
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def get_page_sections(url):
    """Fetch page and extract sections (based on headings)."""
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        print(f"[WARN] Could not fetch {url}: {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")

    # Remove unwanted tags
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "aside"]):
        tag.decompose()

    # Get page title
    title = soup.title.string.strip() if soup.title else url

    # Extract sections based on headings (h2 or h3)
    sections = []
    current_heading = None
    current_text = []

    for element in soup.find_all(["h2", "h3", "p", "li"]):
        if element.name in ["h2", "h3"]:
            # Save previous section
            if current_heading and current_text:
                section_text = clean_text(" ".join(current_text))
                if len(section_text) > 50:  # skip tiny fragments
                    sections.append((current_heading, section_text))
            # Start new section
            current_heading = element.get_text(strip=True)
            current_text = []
        else:
            current_text.append(element.get_text(strip=True))

    # Add final section
    if current_heading and current_text:
        section_text = clean_text(" ".join(current_text))
        if len(section_text) > 50:
            sections.append((current_heading, section_text))

    # If no headings were found, store the whole page as one block
    if not sections:
        body_text = clean_text(" ".join(soup.stripped_strings))
        sections.append((title, body_text))

    return title, sections


def get_topic_links(url):
    """Extract topic links from the main topics page."""
    resp = requests.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        full_url = urljoin(url, href)
        if urlparse(full_url).netloc.endswith("vu.nl"):
            links.add(full_url)

    return sorted(links)


def main():
    print("[INFO] Fetching topic links...")
    topic_links = get_topic_links(BASE_URL) + get_topic_links(BASE_URL2)
    print(f"[INFO] Found {len(topic_links)} topic pages.")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for i, url in enumerate(topic_links, 1):
            print(f"[{i}/{len(topic_links)}] Scraping {url}")
            title, sections = get_page_sections(url)

            f.write(f"### Topic: {title}\n")
            f.write(f"Source: {url}\n\n")

            for heading, text in sections:
                f.write(f"#### Subtopic: {heading}\n{text}\n\n")

            f.write("\n---\n\n")

    print(f"\n✅ Done! Structured knowledge base saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
