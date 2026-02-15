"""arXiv paper fetching service.

Supports:
- Fetching new papers from arxiv.org/list/{category}/new (HTML scraping)
- Fetching papers by date range using the arxiv API (via httpx)
"""

import asyncio
import re
import logging
from datetime import date, timedelta
from typing import Optional

import httpx
from bs4 import BeautifulSoup
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Paper

logger = logging.getLogger(__name__)

# ── Category Mapping ──────────────────────────────────

TOPIC_ABBR: dict[str, str] = {
    "Physics": "",
    "Mathematics": "math",
    "Computer Science": "cs",
    "Quantitative Biology": "q-bio",
    "Quantitative Finance": "q-fin",
    "Statistics": "stat",
    "Electrical Engineering and Systems Science": "eess",
    "Economics": "econ",
}

# Map human-readable sub-category -> arxiv code  (e.g. "Artificial Intelligence" -> "cs.AI")
SUBCATEGORY_CODES: dict[str, str] = {
    # Computer Science
    "Artificial Intelligence": "cs.AI",
    "Computation and Language": "cs.CL",
    "Computational Complexity": "cs.CC",
    "Computer Vision and Pattern Recognition": "cs.CV",
    "Cryptography and Security": "cs.CR",
    "Data Structures and Algorithms": "cs.DS",
    "Databases": "cs.DB",
    "Distributed, Parallel, and Cluster Computing": "cs.DC",
    "Human-Computer Interaction": "cs.HC",
    "Information Retrieval": "cs.IR",
    "Machine Learning": "cs.LG",
    "Multiagent Systems": "cs.MA",
    "Neural and Evolutionary Computing": "cs.NE",
    "Robotics": "cs.RO",
    "Software Engineering": "cs.SE",
    "Computer Science and Game Theory": "cs.GT",
    "Computational Engineering, Finance, and Science": "cs.CE",
    "Computational Geometry": "cs.CG",
    "Computers and Society": "cs.CY",
    "Digital Libraries": "cs.DL",
    "Discrete Mathematics": "cs.DM",
    "Emerging Technologies": "cs.ET",
    "Formal Languages and Automata Theory": "cs.FL",
    "General Literature": "cs.GL",
    "Graphics": "cs.GR",
    "Hardware Architecture": "cs.AR",
    "Information Theory": "cs.IT",
    "Logic in Computer Science": "cs.LO",
    "Mathematical Software": "cs.MS",
    "Multimedia": "cs.MM",
    "Networking and Internet Architecture": "cs.NI",
    "Numerical Analysis": "cs.NA",
    "Operating Systems": "cs.OS",
    "Other Computer Science": "cs.OH",
    "Performance": "cs.PF",
    "Programming Languages": "cs.PL",
    "Social and Information Networks": "cs.SI",
    "Sound": "cs.SD",
    "Symbolic Computation": "cs.SC",
    "Systems and Control": "cs.SY",
    # Mathematics
    "Algebraic Geometry": "math.AG",
    "Number Theory": "math.NT",
    "Probability": "math.PR",
    "Statistics Theory": "math.ST",
    "Optimization and Control": "math.OC",
    "Machine Learning (stat)": "stat.ML",
    # Statistics
    "Applications": "stat.AP",
    "Computation": "stat.CO",
    "Methodology": "stat.ME",
}


def _resolve_categories(raw_categories: list[str]) -> list[str]:
    """Accept either arxiv codes ('cs.AI') or human-readable names and normalise to codes."""
    resolved: list[str] = []
    for cat in raw_categories:
        if re.match(r"^[a-z\-]+\.[A-Z]{2,}$", cat):
            resolved.append(cat)
        elif cat in SUBCATEGORY_CODES:
            resolved.append(SUBCATEGORY_CODES[cat])
        else:
            # Might be a top-level topic like "cs" – keep as-is for the search
            resolved.append(cat)
    return resolved


def _extract_field_prefix(categories: list[str]) -> set[str]:
    """Extract unique field prefixes like 'cs', 'math' from full category codes."""
    prefixes: set[str] = set()
    for cat in categories:
        if "." in cat:
            prefixes.add(cat.split(".")[0])
        else:
            prefixes.add(cat)
    return prefixes


# ── HTML scraping (new papers) ────────────────────────

async def _scrape_new_papers(field_abbr: str) -> list[dict]:
    """Scrape today's new papers from arxiv.org/list/{field}/new."""
    url = f"https://arxiv.org/list/{field_abbr}/new"
    max_retries = 4
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        for attempt in range(max_retries):
            resp = await client.get(url)
            if resp.status_code == 429:
                wait = 3 * (2 ** attempt)
                logger.warning(
                    "arxiv rate limited (429) for %s, retrying in %ds (attempt %d/%d)",
                    url, wait, attempt + 1, max_retries,
                )
                await asyncio.sleep(wait)
                continue
            resp.raise_for_status()
            break
        else:
            resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    content = soup.body.find("div", {"id": "content"})
    if content is None or content.dl is None:
        return []

    dt_list = content.dl.find_all("dt")
    dd_list = content.dl.find_all("dd")
    arxiv_base = "https://arxiv.org/abs/"
    papers: list[dict] = []

    for dt, dd in zip(dt_list, dd_list):
        try:
            paper_number = dt.text.strip().split(" ")[2].split(":")[-1]
            title_tag = dd.find("div", {"class": "list-title mathjax"})
            authors_tag = dd.find("div", {"class": "list-authors"})
            subjects_tag = dd.find("div", {"class": "list-subjects"})
            abstract_tag = dd.find("p", {"class": "mathjax"})

            papers.append({
                "arxiv_id": paper_number,
                "title": title_tag.text.replace("Title: ", "").strip() if title_tag else "",
                "authors": authors_tag.text.replace("Authors:\n", "").replace("\n", "").strip() if authors_tag else "",
                "abstract": abstract_tag.text.replace("\n", " ").strip() if abstract_tag else "",
                "categories": subjects_tag.text.replace("Subjects: ", "").strip() if subjects_tag else "",
                "url": arxiv_base + paper_number,
                "pdf_url": f"https://arxiv.org/pdf/{paper_number}",
            })
        except Exception as exc:
            logger.warning("Failed to parse paper entry: %s", exc)
            continue

    return papers


# ── arxiv API search (date range) ─────────────────────

async def _search_papers_by_date(
    categories: list[str],
    start: date,
    end: date,
    max_results: int = 200,
) -> list[dict]:
    """Search arxiv API for papers in a date range."""
    cat_query = " OR ".join(f"cat:{c}" for c in categories)
    # arxiv API date format: YYYYMMDDHHMMSS
    date_from = start.strftime("%Y%m%d") + "0000"
    date_to = (end + timedelta(days=1)).strftime("%Y%m%d") + "0000"

    query = f"({cat_query}) AND submittedDate:[{date_from} TO {date_to}]"
    api_url = "https://export.arxiv.org/api/query"
    params = {
        "search_query": query,
        "start": 0,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }

    # arxiv API enforces rate limits; retry with exponential backoff on 429
    max_retries = 4
    async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
        for attempt in range(max_retries):
            resp = await client.get(api_url, params=params)
            if resp.status_code == 429:
                wait = 3 * (2 ** attempt)  # 3s, 6s, 12s, 24s
                logger.warning(
                    "arxiv API rate limited (429), retrying in %ds (attempt %d/%d)",
                    wait, attempt + 1, max_retries,
                )
                await asyncio.sleep(wait)
                continue
            resp.raise_for_status()
            break
        else:
            # All retries exhausted
            resp.raise_for_status()  # will raise the 429 error

    soup = BeautifulSoup(resp.text, "xml")
    entries = soup.find_all("entry")
    papers: list[dict] = []

    for entry in entries:
        arxiv_id_full = entry.find("id").text.strip()
        # e.g. "http://arxiv.org/abs/2301.12345v1" -> "2301.12345"
        arxiv_id = arxiv_id_full.split("/abs/")[-1].split("v")[0] if "/abs/" in arxiv_id_full else arxiv_id_full

        title = entry.find("title").text.strip().replace("\n", " ")
        abstract = entry.find("summary").text.strip().replace("\n", " ")
        authors = ", ".join(a.find("name").text.strip() for a in entry.find_all("author"))
        cats = " ".join(c.get("term", "") for c in entry.find_all("category"))
        published = entry.find("published").text.strip()[:10]  # "2024-01-15"

        papers.append({
            "arxiv_id": arxiv_id,
            "title": title,
            "authors": authors,
            "abstract": abstract,
            "categories": cats,
            "url": f"https://arxiv.org/abs/{arxiv_id}",
            "pdf_url": f"https://arxiv.org/pdf/{arxiv_id}",
            "published_date": published,
        })

    return papers


# ── Public interface ──────────────────────────────────

async def fetch_papers(
    arxiv_categories: list[str],
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    max_results: int = 200,
) -> list[dict]:
    """Fetch papers: by date range if dates given, otherwise scrape today's new papers."""
    codes = _resolve_categories(arxiv_categories)

    if start_date and end_date:
        return await _search_papers_by_date(codes, start_date, end_date, max_results)

    # Scrape new papers for each field prefix
    all_papers: list[dict] = []
    seen_ids: set[str] = set()
    for prefix in _extract_field_prefix(codes):
        for paper in await _scrape_new_papers(prefix):
            if paper["arxiv_id"] not in seen_ids:
                seen_ids.add(paper["arxiv_id"])
                all_papers.append(paper)
    return all_papers


async def upsert_papers(db: AsyncSession, raw_papers: list[dict]) -> list[Paper]:
    """Insert new papers into DB or return existing ones. Returns ORM objects."""
    orm_papers: list[Paper] = []
    for raw in raw_papers:
        result = await db.execute(select(Paper).where(Paper.arxiv_id == raw["arxiv_id"]))
        existing = result.scalar_one_or_none()
        if existing:
            orm_papers.append(existing)
        else:
            pub_date = None
            if raw.get("published_date"):
                try:
                    pub_date = date.fromisoformat(str(raw["published_date"]))
                except (ValueError, TypeError):
                    pass
            paper = Paper(
                arxiv_id=raw["arxiv_id"],
                title=raw["title"],
                authors=raw["authors"],
                abstract=raw["abstract"],
                url=raw["url"],
                pdf_url=raw["pdf_url"],
                categories=raw.get("categories", ""),
                published_date=pub_date,
            )
            db.add(paper)
            await db.flush()
            orm_papers.append(paper)
    return orm_papers
