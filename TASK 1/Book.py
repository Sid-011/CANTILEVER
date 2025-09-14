#!/usr/bin/env python3

import argparse
import csv
import os
import time
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter, Retry

DEFAULT_BASE = "https://books.toscrape.com/"
OUTPUT_DIR = os.path.expanduser("~/Desktop/Task/TASK 1")

os.makedirs(OUTPUT_DIR, exist_ok=True)

def make_session() -> requests.Session:
    s = requests.Session()
    retries = Retry(total=5, backoff_factor=0.3, status_forcelist=(500, 502, 503, 504))
    s.mount("https://", HTTPAdapter(max_retries=retries))
    s.headers.update({"User-Agent": "books-to-scrape-scraper/1.0"})
    return s

def get_soup(session: requests.Session, url: str) -> BeautifulSoup:
    print(f"Fetching URL: {url}")
    try:
        r = session.get(url, timeout=15)
        r.raise_for_status()
    except Exception as e:
        print(f"Warning: Failed to fetch {url}: {e}")
        return None
    return BeautifulSoup(r.text, "html.parser")

RATING_MAP = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}

def parse_book_card(card, base_url: str) -> Dict:
    a = card.find("h3").find("a")
    title = a["title"].strip()
    href = a["href"].strip()
    product_url = urljoin(base_url, href)
    price = card.find("p", class_="price_color").text.strip()
    availability = card.find("p", class_="instock availability").text.strip()
    rating_cls = card.find("p", class_="star-rating")["class"]
    rating = next((RATING_MAP[cls] for cls in rating_cls if cls in RATING_MAP), None)
    return {
        "title": title,
        "product_url": product_url,
        "price": price,
        "availability": availability,
        "rating": rating,
    }

def parse_book_detail(soup: BeautifulSoup, base_url: str) -> Dict:
    if soup is None:
        # Return defaults if page couldn't be fetched
        return {
            "upc": "",
            "product_type": "",
            "price_excl_tax": "",
            "price_incl_tax": "",
            "tax": "",
            "num_reviews": "",
            "description": "",
            "category": "",
            "image_url": "",
        }

    data = {}
    table = soup.find("table", class_="table table-striped")
    if table:
        for row in table.find_all("tr"):
            th = row.find("th").text.strip()
            td = row.find("td").text.strip()
            data[th] = td

    desc = ""
    prod_desc_header = soup.find(id="product_description")
    if prod_desc_header:
        p = prod_desc_header.find_next_sibling("p")
        if p:
            desc = p.text.strip()

    category = ""
    breadcrumb = soup.find("ul", class_="breadcrumb")
    if breadcrumb:
        crumbs = breadcrumb.find_all("li")
        if len(crumbs) >= 3:
            category = crumbs[2].get_text(strip=True)

    img = soup.find("div", class_="item active") or soup.find("div", class_="thumbnail")
    image_url = urljoin(base_url, img.find("img")["src"]) if img and img.find("img") else ""

    return {
        "upc": data.get("UPC", ""),
        "product_type": data.get("Product Type", ""),
        "price_excl_tax": data.get("Price (excl. tax)", ""),
        "price_incl_tax": data.get("Price (incl. tax)", ""),
        "tax": data.get("Tax", ""),
        "num_reviews": data.get("Number of reviews", ""),
        "description": desc,
        "category": category,
        "image_url": image_url,
    }

def iterate_site(session: requests.Session, base_url: str, only_category: Optional[str] = None, max_pages: Optional[int] = None):
    if only_category:
        index_soup = get_soup(session, base_url)
        if index_soup is None:
            return []
        cat_nav = index_soup.find("div", class_="side_categories")
        if not cat_nav:
            raise RuntimeError("Couldn't find categories")
        found = None
        for a in cat_nav.find_all("a"):
            if a.get_text(strip=True).lower() == only_category.lower():
                found = urljoin(base_url, a["href"])
                break
        if not found:
            raise RuntimeError(f"Category '{only_category}' not found")
        start_urls = [found]
    else:
        start_urls = [urljoin(base_url, "index.html")]

    books = []
    pages_visited = 0

    for start in start_urls:
        next_url = start
        while next_url:
            pages_visited += 1
            if max_pages and pages_visited > max_pages:
                return books

            print(f"Scraping page {pages_visited}: {next_url}")
            soup = get_soup(session, next_url)
            if soup is None:
                break

            product_list = soup.find_all("article", class_="product_pod")
            for card in product_list:
                try:
                    book = parse_book_card(card, base_url)
                    # ✅ Robust detail fetching with error handling
                    detail_soup = get_soup(session, book["product_url"])
                    detail = parse_book_detail(detail_soup, base_url)
                    book.update(detail)
                    books.append(book)
                    time.sleep(0.5)  # ✅ polite delay to avoid blocking
                except Exception as e:
                    print(f"Warning: failed to parse a product card: {e}")

            next_li = soup.find("li", class_="next")
            next_url = urljoin(next_url, next_li.find("a")["href"]) if next_li and next_li.find("a") else None

    return books

def save_csv(books: List[Dict], out_file: str):
    if not books:
        return
    keys = ["title","price","availability","rating","category","upc","product_type","price_excl_tax","price_incl_tax","tax","num_reviews","description","product_url","image_url"]
    with open(out_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        for b in books:
            writer.writerow({k: b.get(k, "") for k in keys})

def main(argv=None):
    p = argparse.ArgumentParser(description="Scrape books.toscrape.com")
    p.add_argument("--base-url", default=DEFAULT_BASE)
    p.add_argument("--only-category", default=None)
    p.add_argument("--save-images", action="store_true")
    p.add_argument("--out-csv", default=os.path.join(OUTPUT_DIR, "books_toscrape.csv"))
    p.add_argument("--out-html", default=os.path.join(OUTPUT_DIR, "books_toscrape.html"))
    p.add_argument("--max-pages", type=int, default=10)
    args = p.parse_args(argv)

    session = make_session()
    books = iterate_site(session, args.base_url, args.only_category, args.max_pages)

    save_csv(books, args.out_csv)
    print(f"Scraped {len(books)} books and saved to {args.out_csv}")

if __name__ == "__main__":
    main()
