"""
src/scraper.py
==============
Fragrantica Web Scraper
-----------------------
Capstone Project: What Makes a Perfume Highly Rated?
QM640 Data Analytics Capstone | Walsh College
Author : Priyanka Sharma
Term   : 2, May 2026

Description
-----------
Scrapes perfume records from Fragrantica.com using BeautifulSoup
and the Requests library. For each perfume the scraper collects:
  - Perfume name & brand
  - Consumer rating score and vote count
  - Concentration (Eau de Parfum, Eau de Toilette, etc.)
  - Gender label (for women / for men / unisex)
  - Release year
  - Top notes, heart notes, base notes
  - Main accords

Output
------
  data/raw/fragrantica_raw.csv   — full scraped dataset

Usage
-----
  python src/scraper.py                  # default 50 pages
  python src/scraper.py --pages 200      # scrape 200 pages
  python src/scraper.py --delay 3        # 3-second delay between requests

Ethics / Robots.txt
-------------------
This scraper respects a configurable delay between requests (default 2 s)
to avoid overloading the server. Review fragrantica.com/robots.txt and
ensure any academic or personal use complies with the site's Terms of
Service before running at scale.
"""

import argparse
import csv
import os
import random
import re
import time
from dataclasses import dataclass, fields, asdict
from pathlib import Path
from typing import Optional

import requests
from bs4 import BeautifulSoup

# ── Constants ────────────────────────────────────────────────────────────────

BASE_URL   = "https://www.fragrantica.com"
SEARCH_URL = "https://www.fragrantica.com/search/"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": "https://www.fragrantica.com/",
}

OUTPUT_DIR  = Path("data/raw")
OUTPUT_FILE = OUTPUT_DIR / "fragrantica_raw.csv"

# ── Data model ───────────────────────────────────────────────────────────────

@dataclass
class PerfumeRecord:
    perfume_name    : str  = ""
    brand           : str  = ""
    rating_score    : Optional[float] = None
    num_votes       : Optional[int]   = None
    concentration   : str  = ""
    gender_label    : str  = ""
    release_year    : Optional[int]   = None
    top_notes       : str  = ""   # pipe-separated list e.g. "Rose|Bergamot"
    heart_notes     : str  = ""
    base_notes      : str  = ""
    main_accords    : str  = ""
    longevity_votes : str  = ""   # e.g. "Weak:12|Moderate:45|Long:89|..."
    sillage_votes   : str  = ""
    season_votes    : str  = ""
    perfume_url     : str  = ""


# ── Helper functions ─────────────────────────────────────────────────────────

def get_page(url: str, session: requests.Session, delay: float) -> Optional[BeautifulSoup]:
    """Fetch a URL and return a BeautifulSoup object, or None on failure."""
    try:
        time.sleep(delay + random.uniform(0.3, 0.8))   # polite crawl delay
        response = session.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")
    except requests.RequestException as exc:
        print(f"  [WARN] Failed to fetch {url}: {exc}")
        return None


def parse_rating(soup: BeautifulSoup) -> tuple[Optional[float], Optional[int]]:
    """Extract average rating score and vote count."""
    try:
        # Rating value
        rating_tag = soup.find("span", itemprop="ratingValue")
        score = float(rating_tag.text.strip()) if rating_tag else None

        # Vote count
        vote_tag = soup.find("span", itemprop="ratingCount")
        votes = int(vote_tag.text.strip().replace(",", "")) if vote_tag else None

        return score, votes
    except (AttributeError, ValueError):
        return None, None


def parse_notes(soup: BeautifulSoup) -> tuple[str, str, str]:
    """Return (top_notes, heart_notes, base_notes) as pipe-separated strings."""
    result = {"top": [], "heart": [], "base": []}
    try:
        # Fragrantica wraps note sections in <div> with specific pyramid labels
        pyramid = soup.find("div", class_=re.compile(r"notesTree|pyramid", re.I))
        if pyramid:
            sections = pyramid.find_all("div", recursive=False)
            labels = ["top", "heart", "base"]
            for i, section in enumerate(sections[:3]):
                imgs = section.find_all("img")
                result[labels[i]] = [img.get("title", "").strip() for img in imgs if img.get("title")]
    except Exception:
        pass
    return (
        "|".join(result["top"]),
        "|".join(result["heart"]),
        "|".join(result["base"]),
    )


def parse_accords(soup: BeautifulSoup) -> str:
    """Return main accords as a pipe-separated string."""
    try:
        accord_divs = soup.find_all("div", class_=re.compile(r"accord-box", re.I))
        accords = []
        for div in accord_divs:
            name_tag = div.find("span") or div
            name = name_tag.get_text(strip=True)
            if name:
                accords.append(name)
        return "|".join(accords[:8])   # cap at 8 accords
    except Exception:
        return ""


def parse_votes_bar(soup: BeautifulSoup, section_label: str) -> str:
    """
    Parse vote distribution bars (longevity / sillage / season).
    Returns a string like 'Weak:12|Moderate:45|Long:89|Very Long:34|Eternal:8'
    """
    try:
        # Find section heading
        heading = soup.find(string=re.compile(section_label, re.I))
        if not heading:
            return ""
        container = heading.find_parent("div")
        if not container:
            return ""
        bars = container.find_all("div", class_=re.compile(r"voting-small-chart-size", re.I))
        parts = []
        for bar in bars:
            label = bar.find("span", class_=re.compile(r"voting-small-chart-size-text", re.I))
            count = bar.find("span", class_=re.compile(r"voting-small-chart-size-votes", re.I))
            if label and count:
                parts.append(f"{label.text.strip()}:{count.text.strip()}")
        return "|".join(parts)
    except Exception:
        return ""


def parse_perfume_page(url: str, session: requests.Session, delay: float) -> Optional[PerfumeRecord]:
    """Scrape a single perfume page and return a PerfumeRecord."""
    soup = get_page(url, session, delay)
    if soup is None:
        return None

    record = PerfumeRecord(perfume_url=url)

    try:
        # Name & brand from <h1> and <h1 itemprop="name">
        h1 = soup.find("h1")
        if h1:
            brand_tag = h1.find("span", itemprop="name")
            if brand_tag:
                record.brand = brand_tag.text.strip()
                record.perfume_name = h1.get_text(strip=True).replace(record.brand, "").strip()
            else:
                record.perfume_name = h1.get_text(strip=True)

        # Concentration & gender from breadcrumb / meta section
        details_div = soup.find("div", class_=re.compile(r"cell small-12 breadcrumbs", re.I))
        if details_div:
            text = details_div.get_text(" ", strip=True)
            for conc in ["Eau de Parfum", "Eau de Toilette", "Parfum", "Cologne",
                         "Eau de Cologne", "Extrait de Parfum", "Body Mist"]:
                if conc.lower() in text.lower():
                    record.concentration = conc
                    break
            for gender in ["for women", "for men", "unisex", "for women and men"]:
                if gender.lower() in text.lower():
                    record.gender_label = gender
                    break

        # Release year
        year_match = re.search(r"\b(19[5-9]\d|20[0-2]\d)\b", soup.get_text())
        if year_match:
            record.release_year = int(year_match.group())

        # Rating & votes
        record.rating_score, record.num_votes = parse_rating(soup)

        # Notes
        record.top_notes, record.heart_notes, record.base_notes = parse_notes(soup)

        # Accords
        record.main_accords = parse_accords(soup)

        # Perception votes
        record.longevity_votes = parse_votes_bar(soup, "Longevity")
        record.sillage_votes   = parse_votes_bar(soup, "Sillage")
        record.season_votes    = parse_votes_bar(soup, "Season")

    except Exception as exc:
        print(f"  [WARN] Error parsing {url}: {exc}")

    return record


def get_perfume_links_from_search_page(soup: BeautifulSoup) -> list[str]:
    """
    Extract individual perfume URLs from a Fragrantica search/listing page.
    Fragrantica search results contain <div class='cell card fr-news-box'> items.
    """
    links = []
    try:
        cards = soup.find_all("div", class_=re.compile(r"cell card fr-news-box", re.I))
        for card in cards:
            a_tag = card.find("a", href=True)
            if a_tag:
                href = a_tag["href"]
                if href.startswith("/perfume/"):
                    links.append(BASE_URL + href)
    except Exception:
        pass
    return links


# ── Main scraper ─────────────────────────────────────────────────────────────

def scrape(num_pages: int = 50, delay: float = 2.0) -> None:
    """
    Iterate over Fragrantica search result pages and scrape each perfume.

    Parameters
    ----------
    num_pages : int
        Number of search-result pages to iterate (each has ~12 perfumes).
        50 pages ≈ 600 records; 1 900 pages ≈ 22 800 records.
    delay : float
        Seconds to wait between HTTP requests.
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    session  = requests.Session()
    all_seen = set()   # avoid duplicates

    fieldnames = [f.name for f in fields(PerfumeRecord)]

    # Open CSV in append mode so we can resume if interrupted
    file_exists = OUTPUT_FILE.exists()
    csvfile = open(OUTPUT_FILE, "a", newline="", encoding="utf-8")
    writer  = csv.DictWriter(csvfile, fieldnames=fieldnames)
    if not file_exists:
        writer.writeheader()

    total_saved = 0

    try:
        for page_num in range(1, num_pages + 1):
            # Fragrantica paginates with ?page=N (0-indexed internally, 1-indexed in URL)
            search_page_url = f"{SEARCH_URL}?page={page_num}"
            print(f"\n[Page {page_num}/{num_pages}] {search_page_url}")

            soup = get_page(search_page_url, session, delay)
            if soup is None:
                continue

            perfume_urls = get_perfume_links_from_search_page(soup)
            if not perfume_urls:
                print("  No perfume links found — possibly last page or layout change.")
                break

            for perfume_url in perfume_urls:
                if perfume_url in all_seen:
                    continue
                all_seen.add(perfume_url)

                print(f"  Scraping: {perfume_url}")
                record = parse_perfume_page(perfume_url, session, delay)
                if record and record.perfume_name:
                    writer.writerow(asdict(record))
                    csvfile.flush()
                    total_saved += 1
                    print(f"    ✓ {record.brand} — {record.perfume_name} "
                          f"(rating={record.rating_score}, votes={record.num_votes})")
    finally:
        csvfile.close()

    print(f"\nDone. {total_saved} records saved to {OUTPUT_FILE}")


# ── CLI entry point ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fragrantica scraper for QM640 capstone")
    parser.add_argument("--pages", type=int, default=50,
                        help="Number of search-result pages to scrape (default: 50)")
    parser.add_argument("--delay", type=float, default=2.0,
                        help="Seconds between requests (default: 2.0)")
    args = parser.parse_args()

    print("=" * 60)
    print("  Fragrantica Scraper — QM640 Capstone")
    print(f"  Pages: {args.pages}  |  Delay: {args.delay}s")
    print("=" * 60)
    scrape(num_pages=args.pages, delay=args.delay)
