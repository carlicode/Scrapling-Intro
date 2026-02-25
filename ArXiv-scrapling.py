from __future__ import annotations

import json
import os
from urllib.parse import quote_plus

import requests
from scrapling.parser import Selector


ALLOWED_SIZES = {25, 50, 100, 200}


def fetch_html(url: str) -> str:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,es;q=0.8",
        "Referer": "https://arxiv.org/",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }

    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.text


def scrape_arxiv_search(query: str, size: int = 25) -> list[dict]:
    """
    Scrapea resultados HTML de arXiv Search.
    size debe ser uno de: 25, 50, 100, 200 (si no, arXiv devuelve 400).
    """
    if size not in ALLOWED_SIZES:
        raise ValueError(f"`size` inválido: {size}. Usa uno de {sorted(ALLOWED_SIZES)}")

    q = quote_plus(query)
    url = (
        "https://arxiv.org/search/?"
        f"query={q}"
        "&searchtype=all"
        "&abstracts=show"
        "&order=-announced_date_first"
        f"&size={size}"
    )

    html = fetch_html(url)
    page = Selector(html)

    results = page.css("li.arxiv-result")
    items: list[dict] = []

    for r in results:
        title = r.css("p.title.is-5.mathjax::text").get()
        title = " ".join(title.split()) if title else None

        authors = r.css("p.authors a::text").getall()
        authors = [" ".join(a.split()) for a in authors if a and a.strip()]

        submitted_raw = r.css("p.is-size-7::text").get()
        submitted = " ".join(submitted_raw.split()) if submitted_raw else None

        abstract = r.css("span.abstract-full.has-text-grey-dark.mathjax::text").get()
        abstract = " ".join(abstract.split()) if abstract else None

        paper_url = r.css("p.list-title a::attr(href)").get()
        paper_url = paper_url.strip() if paper_url else None

        pdf_url = None
        if paper_url and "/abs/" in paper_url:
            pdf_url = paper_url.replace("/abs/", "/pdf/") + ".pdf"

        items.append(
            {
                "title": title,
                "authors": authors,
                "submitted": submitted,
                "abstract": abstract,
                "url": paper_url,
                "pdf_url": pdf_url,
            }
        )

    return items


if __name__ == "__main__":
    print("RUNNING FILE:", os.path.abspath(__file__))

    query = "retrieval augmented generation"
    data = scrape_arxiv_search(query=query, size=25)

    print(f"\n✅ Encontré {len(data)} resultados para: {query}\n")

    for i, item in enumerate(data[:5], start=1):
        print(f"{i}. {item.get('title')}")
        a = item.get("authors") or []
        print(f"   Authors: {', '.join(a[:5])}{'...' if len(a) > 5 else ''}")
        print(f"   Submitted: {item.get('submitted')}")
        print(f"   URL: {item.get('url')}")
        print(f"   PDF: {item.get('pdf_url')}\n")

    with open("arxiv_results.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("📦 Guardado: arxiv_results.json")