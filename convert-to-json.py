import os
import sys
import json
import requests
from datetime import date
from bs4 import BeautifulSoup
from newspaper import Article
from urllib.parse import urlparse
from pathlib import Path


def set_day():
    t = date.today().weekday()
    t = t if t<5 else 0
    path = Path(f"{t}","URLS")
    return path

def read_the_urls(path):
    with open(path, "r") as f:
        return [line.strip() for line in f if line.strip()]

def extract_article_info(url):
    try:
        article = Article(url)
        article.download()
        article.parse()

        title = article.title or ""
        authors = article.authors or []
        publish_date = article.publish_date.isoformat() if article.publish_date else None
        text = article.text.strip().replace("\n", " ")
        description = " ".join(text.split()[:150])
        source = urlparse(url).netloc.replace("www.", "")

        return {
            "url": url,
            "source": source,
            "title": title,
            "author": authors,
            "published_date": publish_date,
            "description": description
        }

    except Exception:
        # Fallback using BeautifulSoup
        try:
            res = requests.get(url, timeout=10)
            soup = BeautifulSoup(res.content, "html.parser")

            title = soup.title.string.strip() if soup.title else ""
            paragraphs = soup.find_all("p")
            text = " ".join(p.get_text() for p in paragraphs)
            description = " ".join(text.strip().split()[:150])

            author_meta = soup.find("meta", attrs={"name": "author"}) or \
                          soup.find("meta", attrs={"property": "article:author"})
            author = [author_meta["content"]] if author_meta and author_meta.get("content") else []

            date_meta = soup.find("meta", attrs={"property": "article:published_time"}) or \
                        soup.find("meta", attrs={"name": "pubdate"})
            publish_date = date_meta["content"] if date_meta and date_meta.get("content") else None

            source = urlparse(url).netloc.replace("www.", "")

            return {
                "url": url,
                "source": source,
                "title": title,
                "author": author,
                "published_date": publish_date,
                "description": description
            }
        except Exception as e:
            return {
                "url": url,
                "source": None,
                "title": None,
                "author": [],
                "published_date": None,
                "description": f"Failed to extract: {str(e)}"
            }

def main(input_path):
    urls = read_the_urls(input_path)
    results = [extract_article_info(url) for url in urls]

    output_path = os.path.splitext(input_path)[0] + ".json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(results)} articles to {output_path}")

if __name__ == "__main__":
#    if len(sys.argv) < 2:
#        print("Usage: python scrape_articles.py path_to_file.txt")
#        sys.exit(1)
#    main(sys.argv[1])
    base_path = set_day()
    for file in os.listdir(base_path):
        if file.endswith(".txt"):
            full_path = base_path / file  # Esto es un objeto Path
            main(str(full_path))
