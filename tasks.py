from crewai import Task
from tools import get_search_tool
from agents import researcher, analyst, reporter
from pydantic import BaseModel, Field, ConfigDict
from typing import List
from datetime import datetime, timezone, timedelta
import re, requests
from config import MAX_AGE_DAYS, ALLOWED_SOURCES, MAX_INCIDENTS

CUTOFF_DATE = datetime.now(timezone.utc) - timedelta(days=MAX_AGE_DAYS)

NEGATIVE_KEYWORDS = [
    "harm","bias","scam","deepfake","fraud","abuse",
    "injury","lawsuit","misinformation","fatal","crime",
    "data breach","exploit","malicious","discrimination",
    "privacy leak","breach","illegal","death","failure"
]

BAN_WORDS = [
    "concern","warning","risk","study","opinion","fact-check",
    "hoax","rumor","misinformation report","advisory",
    "plan to","proposal","initiative","announcement",
    "safety mechanism","survey","whitepaper","paper",
    "research","analysis","report"
]

BLOG_WORDS = [
    "blogspot","wordpress","medium.com","substack",
    "tumblr","blog.","/blog/","dev.to","hashnode","ghost.io"
]

# --------- Schemas ----------
class ReportSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    title: str
    summary: str
    impact: str
    estimated_loss: str
    fine_due_to_non_compliance: str
    sources: List[str] = Field(
        ..., description="At least two working clickable URLs giving evidence of the incident"
    )

class ReportListSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    reports: List[ReportSchema]

# --------- Helpers ----------
def is_valid_item(item: dict) -> bool:
    """Filter out invalid, speculative, blog or stale results."""
    title = (item.get("title") or "").lower()
    summary = (item.get("summary") or "").lower()

    if any(b in title for b in BAN_WORDS) or any(b in summary for b in BAN_WORDS):
        return False

    if not any(kw in title for kw in NEGATIVE_KEYWORDS):
        return False

    url = item.get("url") or item.get("source", "")
    if not isinstance(url, str) or not url.startswith(("http://", "https://")):
        return False

    if ALLOWED_SOURCES and not any(domain in url for domain in ALLOWED_SOURCES):
        return False
    if any(word in url.lower() for word in BLOG_WORDS):
        return False

    date_str = item.get("date")
    if not date_str or not isinstance(date_str, str):
        return False
    try:
        dt = datetime.fromisoformat(date_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        if dt < CUTOFF_DATE:
            return False
    except Exception:
        return False

    return True


def filter_recent(results):
    if not isinstance(results, list):
        return []
    valid = [r for r in results if is_valid_item(r)]
    return valid[:MAX_INCIDENTS]


def deduplicate(results):
    if not isinstance(results, list):
        return []
    seen, unique = set(), []
    for r in results:
        key = (r.get("url") or r.get("source") or "").strip().lower()
        if not key:
            key = r.get("title","").strip().lower()
        if key and key not in seen:
            seen.add(key)
            unique.append(r)
    return unique


def deduplicate_reports(report_list):
    if not isinstance(report_list, list):
        return []
    seen, unique = set(), []
    for r in report_list:
        urls = getattr(r, "sources", [])
        key = tuple(sorted(urls)) if urls else getattr(r, "title", "").lower()
        if key not in seen:
            seen.add(key)
            unique.append(r)
    return unique


def validate_sources(report_list):
    """Ensure each report has ≥2 working links."""
    if not isinstance(report_list, list):
        return []
    good = []
    for r in report_list:
        urls = getattr(r, "sources", [])
        valid_urls = []
        for u in urls:
            if isinstance(u, str) and re.match(r"^https?://", u):
                try:
                    resp = requests.head(u, allow_redirects=True, timeout=5)
                    if resp.status_code < 400:
                        valid_urls.append(u)
                except Exception:
                    continue
        if len(valid_urls) >= 2:
            r.sources = valid_urls
            good.append(r)
    return good

# --------- Tasks ----------
research_task = Task(
    description=f"""
        Find up to {MAX_INCIDENTS} **real-world incidents** of AI failures or unethical use.

        Requirements:
        - Must be within the last {MAX_AGE_DAYS} days.
        - Must describe an AI system that already caused harm (fraud, scams, bias, accidents, etc.).
        - Exclude studies, surveys, research reports, advisories, proposals, concerns,
          and blogs/personal websites (Medium, WordPress, Blogspot, etc.).
        - Always provide the full clickable URL, not just the domain.

        For each incident return: summary, date, and full URL.
    """,
    expected_output="Structured list (summary, date, URL) of up to three real-world AI incidents causing harm.",
    tools=[get_search_tool()],
    agent=researcher,
    postprocess=lambda results: deduplicate(filter_recent(results)),
)

analysis_task = Task(
    description="""
        Validate and enrich each incident:
        1. Confirm it's a real harmful event (no research, warning, or blog).
        2. Collect at least two credible, working URLs with evidence.
        3. Extract impact, estimated_loss ('unknown'), fines ('unknown').
        4. Return `sources` as a list of those URLs.
    """,
    expected_output="Validated briefs with ≥2 evidence links, impact, estimated_loss, fines.",
    tools=[get_search_tool()],
    agent=analyst,
    context=[research_task],
    postprocess=validate_sources
)

report_task = Task(
    description="""
        Build a strict JSON report.

        - Only include incidents with ≥2 working clickable URLs.
        - Remove duplicates by URL set or title.
    """,
    expected_output=f"JSON (ReportListSchema) with up to {MAX_INCIDENTS} reports.",
    agent=reporter,
    context=[analysis_task],
    output_json=ReportListSchema,
    postprocess=deduplicate_reports,
)

# Stability patch for some CrewAI versions
for t, key in [
    (research_task, "research_task"),
    (analysis_task, "analysis_task"),
    (report_task, "report_task"),
]:
    try:
        if not hasattr(t, "key") or getattr(t, "key") is None:
            setattr(t, "key", key)
    except Exception:
        pass


