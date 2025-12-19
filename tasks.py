'''
from dateutil import parser
from crewai import Task
from tools import get_search_tool
from agents import researcher, analyst, reporter
from pydantic import BaseModel, Field, ConfigDict
from typing import List
from datetime import datetime, timezone, timedelta
import re, requests
from config import MAX_AGE_DAYS, ALLOWED_SOURCES, MAX_INCIDENTS, MIN_SOURCES

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

# --------- Schemas ----------
class ReportSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    title: str
    summary: str
    impact: str
    estimated_loss: str
    fine_due_to_non_compliance: str
    sources: List[str] = Field(
        ..., description=f"At least {MIN_SOURCES} working clickable URLs giving evidence of the incident"
    )

class ReportListSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    reports: List[ReportSchema]  

# --------- Helpers ----------
def is_valid_item(item: dict) -> bool:
    """Return True if the item is valid, else False."""
    title = (item.get("title") or "").lower()
    summary = (item.get("summary") or "").lower()

    if any(b in title for b in BAN_WORDS) or any(b in summary for b in BAN_WORDS):
        return False

    if not any(kw in (title + " " + summary) for kw in NEGATIVE_KEYWORDS):
        return False

    url = item.get("url") or item.get("source", "")
    if not isinstance(url, str) or not url.startswith(("http://", "https://")):
        return False
    if ALLOWED_SOURCES and not any(domain in url for domain in ALLOWED_SOURCES):
        return False

    date_str = item.get("date")
    if not date_str or not isinstance(date_str, str):
        return False
    try:
        dt = parser.isoparse(date_str)
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
            key = r.get("title", "").strip().lower()
        if key and key not in seen:
            seen.add(key)
            unique.append(r)
    return unique

def deduplicate_reports(report_list):
    if hasattr(report_list, "reports"):
        report_list = report_list.reports
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
    """Ensure each report has ≥ MIN_SOURCES working links."""
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
        if len(valid_urls) >= MIN_SOURCES:
            r.sources = valid_urls
            good.append(r)
    return good

# --------- Tasks ----------
research_task = Task(
    key="research_task",
    description=f"""
        Find up to {MAX_INCIDENTS} **real-world incidents** of AI failures or unethical use.

        Requirements:
        - Must be within the last {MAX_AGE_DAYS} days.
        - Must describe an AI system that already caused harm (fraud, scams, bias, accidents, etc.).
        - Exclude studies, surveys, research reports, advisories, proposals, concerns.
        - Always provide the full clickable URL, not just the domain.

        For each incident return: summary, date (ISO8601), and full URL.
    """,
    expected_output="Structured list (summary, date, URL) of up to three real-world AI incidents causing harm.",
    tools=[get_search_tool()],
    agent=researcher,
    postprocess=lambda results: deduplicate(filter_recent(results)),
)

analysis_task = Task(
    key="analysis_task",
    description=f"""
        Validate and enrich each incident:
        1. Confirm it's a real harmful event (no research, warning).
        2. Collect at least {MIN_SOURCES} credible, working URLs with evidence.
        3. Extract impact, estimated_loss ('unknown'), fines ('unknown').
        4. Ensure the incident happened within the last {MAX_AGE_DAYS} days.
        5. Return `sources` as a list of those URLs.
    """,
    expected_output=f"Validated briefs with ≥{MIN_SOURCES} evidence links, impact, estimated_loss, fines.",
    tools=[get_search_tool()],
    agent=analyst,
    context=[research_task],
    postprocess=validate_sources
)

report_task = Task(
    key="report_task",
    description=f"""
        Build a strict JSON report.

        - Only include incidents with ≥{MIN_SOURCES} working clickable URLs.
        - Remove duplicates by URL set or title.
        - Do not include date in the final JSON output.
    """,
    expected_output=f"JSON (ReportListSchema) with up to {MAX_INCIDENTS} reports.",
    agent=reporter,
    context=[analysis_task],
    output_json=ReportListSchema,
    postprocess=deduplicate_reports,
)

for t, key in [
    (research_task, "research_task"),
    (analysis_task, "analysis_task"),
    (report_task, "report_task"),
]:
    if t and (not hasattr(t, "key") or getattr(t, "key") is None):
        setattr(t, "key", key)

'''
'''
from dateutil import parser
from crewai import Task
from tools import get_search_tool
from agents import researcher, analyst, reporter
from pydantic import BaseModel, Field, ConfigDict
from typing import List
from datetime import datetime, timezone, timedelta
import requests, re
from config import MAX_AGE_DAYS, MAX_INCIDENTS, MIN_SOURCES, SEARCH_TOOL

CUTOFF_DATE = datetime.now(timezone.utc) - timedelta(days=MAX_AGE_DAYS)

# ---------------- Schema ----------------
class ReportSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    title: str
    summary: str
    impact: str
    estimated_loss: str
    fine_due_to_non_compliance: str
    sources: List[str] = Field(..., description="At least two working URLs")

class ReportListSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    reports: List[ReportSchema]

# ---------------- Helpers ----------------
def is_valid_item(item: dict) -> bool:
    """Filter invalid/irrelevant incidents, handle both ISO and NewsData.io pubDate formats."""
    title = (item.get("title") or "").lower()
    summary = (item.get("summary") or "").lower()
    if not title or not summary:
        return False

    # URL check
    url = item.get("url") or item.get("source", "")
    if not isinstance(url, str) or not url.startswith(("http://", "https://")):
        return False

    # Date check
    date_str = item.get("date") or item.get("pubDate")
    if not date_str:
        return False

    try:
        dt = parser.parse(date_str)  # ✅ handles both ISO & NewsData pubDate
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
    seen, unique = set(), []
    for r in results:
        key = (r.get("url") or "").strip().lower()
        if key and key not in seen:
            seen.add(key)
            unique.append(r)
    return unique

def validate_sources(report_list):
    """Ensure each report has ≥ MIN_SOURCES valid URLs."""
    if not isinstance(report_list, list):
        return []
    valid_reports = []
    for r in report_list:
        urls = getattr(r, "sources", [])
        checked = []
        for u in urls:
            if isinstance(u, str) and re.match(r"^https?://", u):
                try:
                    resp = requests.head(u, allow_redirects=True, timeout=5)
                    if resp.status_code < 400:
                        checked.append(u)
                except Exception:
                    continue
        if len(checked) >= MIN_SOURCES:
            r.sources = checked
            valid_reports.append(r)
    return valid_reports

def deduplicate_reports(report_list):
    if hasattr(report_list, "reports"):
        report_list = report_list.reports
    seen, unique = set(), []
    for r in report_list:
        urls = getattr(r, "sources", [])
        key = tuple(sorted(urls)) if urls else getattr(r, "title", "").lower()
        if key not in seen:
            seen.add(key)
            unique.append(r)
    return unique

# ---------------- Tasks ----------------
research_task = Task(
    key="research_task",
    description=f"Find up to {MAX_INCIDENTS} harmful AI incidents in the last {MAX_AGE_DAYS} days. Use the hybrid tool to gather credible news (not studies/opinions).",
    expected_output="Structured list of incidents with summary, date, and URL.",
    tools=[get_search_tool(SEARCH_TOOL)],
    agent=researcher,
    postprocess=lambda results: deduplicate(filter_recent(results)),
)

analysis_task = Task(
    key="analysis_task",
    description=f"Validate and enrich incidents. Each must have ≥{MIN_SOURCES} credible sources. Extract impact, estimated_loss ('unknown'), fines ('unknown').",
    expected_output="Validated briefs with ≥2 evidence links, impact, estimated_loss, and fines.",
    tools=[get_search_tool(SEARCH_TOOL)],
    agent=analyst,
    context=[research_task],
    postprocess=validate_sources,
)

report_task = Task(
    key="report_task",
    description="Synthesize validated incidents into strict JSON.",
    expected_output=f"JSON (ReportListSchema) with up to {MAX_INCIDENTS} reports.",
    agent=reporter,
    context=[analysis_task],
    output_json=ReportListSchema,
    postprocess=deduplicate_reports,
)
'''

from dateutil import parser
from crewai import Task
from tools import get_search_tool
from agents import researcher, analyst, reporter
from pydantic import BaseModel, Field, ConfigDict
from typing import List
from datetime import datetime, timezone, timedelta
import requests, re
from config import MAX_AGE_DAYS, MAX_INCIDENTS, MIN_SOURCES, SEARCH_TOOL

CUTOFF_DATE = datetime.now(timezone.utc) - timedelta(days=MAX_AGE_DAYS)

# ---------------- Schema ----------------
class ReportSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    title: str
    summary: str
    impact: str
    estimated_loss: str
    fine_due_to_non_compliance: str
    sources: List[str] = Field(..., description="At least two working URLs")

class ReportListSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    reports: List[ReportSchema]

# ---------------- Helpers ----------------
def is_valid_item(item: dict) -> bool:
    """Filter invalid/irrelevant incidents, handle both ISO and NewsData.io pubDate formats."""
    title = (item.get("title") or "").lower()
    summary = (item.get("summary") or "").lower()
    if not title or not summary:
        return False

    # URL check
    url = item.get("url") or item.get("source", "")
    if not isinstance(url, str) or not url.startswith(("http://", "https://")):
        return False

    # Date check
    date_str = item.get("date") or item.get("pubDate")
    if not date_str:
        return False

    try:
        dt = parser.parse(date_str)  # ✅ handles both ISO & NewsData pubDate
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
    seen, unique = set(), []
    for r in results:
        key = (r.get("url") or "").strip().lower()
        if key and key not in seen:
            seen.add(key)
            unique.append(r)
    return unique

def validate_sources(report_list):
    """Ensure each report has ≥ MIN_SOURCES valid URLs."""
    if not isinstance(report_list, list):
        return []
    valid_reports = []
    for r in report_list:
        urls = getattr(r, "sources", [])
        checked = []
        for u in urls:
            if isinstance(u, str) and re.match(r"^https?://", u):
                try:
                    resp = requests.head(u, allow_redirects=True, timeout=5)
                    if resp.status_code < 400:
                        checked.append(u)
                except Exception:
                    continue
        if len(checked) >= MIN_SOURCES:
            r.sources = checked
            valid_reports.append(r)
    return valid_reports

def deduplicate_reports(report_list):
    if hasattr(report_list, "reports"):
        report_list = report_list.reports
    seen, unique = set(), []
    for r in report_list:
        urls = getattr(r, "sources", [])
        key = tuple(sorted(urls)) if urls else getattr(r, "title", "").lower()
        if key not in seen:
            seen.add(key)
            unique.append(r)
    return unique

# ---------------- Tasks ----------------
research_task = Task(
    key="research_task",
    description=f"Find up to {MAX_INCIDENTS} harmful AI incidents in the last {MAX_AGE_DAYS} days. Use the hybrid tool to gather credible news (not studies/opinions).",
    expected_output="Structured list of incidents with summary, date, and URL.",
    tools=[get_search_tool(SEARCH_TOOL)],
    agent=researcher,
    postprocess=lambda results: deduplicate(filter_recent(results)),
)

analysis_task = Task(
    key="analysis_task",
    description=f"Validate and enrich incidents. Each must have ≥{MIN_SOURCES} credible sources. Extract impact, estimated_loss ('unknown'), fines ('unknown').",
    expected_output="Validated briefs with ≥2 evidence links, impact, estimated_loss, and fines.",
    tools=[get_search_tool(SEARCH_TOOL)],
    agent=analyst,
    context=[research_task],
    postprocess=validate_sources,
)

report_task = Task(
    key="report_task",
    description="Synthesize validated incidents into strict JSON.",
    expected_output=f"JSON (ReportListSchema) with up to {MAX_INCIDENTS} reports.",
    agent=reporter,
    context=[analysis_task],
    output_json=ReportListSchema,
    postprocess=deduplicate_reports,
)



