'''from crewai_tools import TavilySearchTool
from datetime import datetime, timedelta
from config import MAX_AGE_DAYS


def get_search_tool():
    """Return a TavilySearchTool with a dynamic date range based on MAX_AGE_DAYS."""
    now = datetime.now()
    start = now - timedelta(days=MAX_AGE_DAYS)

    start_date_str = start.strftime("%Y-%m-%d")
    end_date_str = now.strftime("%Y-%m-%d")

    print(f"🔍 Tavily initialized with start_date={start_date_str} and end_date={end_date_str}")
    return TavilySearchTool(start_date=start_date_str, end_date=end_date_str)
'''
'''
import os
import requests
from crewai_tools import TavilySearchTool
from datetime import datetime, timedelta
from config import MAX_AGE_DAYS

# Load API key for NewsData.io
NEWSDATA_API_KEY = os.getenv("NEWSDATA_API_KEY")

class NewsDataTool:
    def __init__(self, max_age_days=180):
        self.name = "newsdata_search"
        self.description = "Fetches AI incident news from NewsData.io"
        self.max_age_days = max_age_days

    def run(self, query: str):
        if not NEWSDATA_API_KEY:
            print("⚠️ No NEWSDATA_API_KEY found in environment.")
            return []

        now = datetime.now()
        start = now - timedelta(days=self.max_age_days)
        start_date_str = start.strftime("%Y-%m-%d")
        end_date_str = now.strftime("%Y-%m-%d")

        url = (
            f"https://newsdata.io/api/1/news?"
            f"apikey={NEWSDATA_API_KEY}&q={query}"
            f"&from_date={start_date_str}&to_date={end_date_str}"
            f"&language=en&category=technology"
        )
        try:
            resp = requests.get(url, timeout=15)
            data = resp.json()
            results = []
            for a in data.get("results", []):
                results.append({
                    "title": a.get("title"),
                    "summary": a.get("description"),
                    "url": a.get("link"),
                    "date": a.get("pubDate"),
                    "source": a.get("source_id"),
                })
            return results
        except Exception as e:
            print("❌ Error querying NewsData.io:", e)
            return []

def get_tavily_tool():
    now = datetime.now()
    start = now - timedelta(days=MAX_AGE_DAYS)
    return TavilySearchTool(
        start_date=start.strftime("%Y-%m-%d"),
        end_date=now.strftime("%Y-%m-%d")
    )

def deduplicate_results(results):
    seen, unique = set(), []
    for r in results:
        url = r.get("url") or r.get("source", "")
        if url and url not in seen:
            seen.add(url)
            unique.append(r)
    return unique

def get_search_tool(provider="hybrid"):
    provider = provider.lower()

    if provider == "tavily":
        return get_tavily_tool()

    elif provider == "newsdata":
        return NewsDataTool(max_age_days=MAX_AGE_DAYS)

    elif provider == "hybrid":
        tavily = get_tavily_tool()
        newsdata = NewsDataTool(max_age_days=MAX_AGE_DAYS)

        class HybridTool:
            def __init__(self):
                self.name = "hybrid_search"
                self.description = "Combines Tavily + NewsData.io for AI incident discovery"

            def run(self, query: str):
                t_res = tavily.run(query) or []
                n_res = newsdata.run(query) or []
                return deduplicate_results(t_res + n_res)

        return HybridTool()

    else:
        raise ValueError(f"Unknown provider: {provider}")

'''
'''
# tools.py
import os, requests
from datetime import datetime, timedelta
from config import MAX_AGE_DAYS

# Import BaseTool and Tavily if available
from crewai.tools import BaseTool
from crewai_tools import TavilySearchTool


NEWSDATA_API_KEY = os.getenv("NEWSDATA_API_KEY")

# ✅ NewsData.io search wrapped as a proper BaseTool
class NewsDataTool(BaseTool):
    name: str = "newsdata_search"
    description: str = "Fetch AI incident news from NewsData.io"

    def _run(self, query: str) -> list:
        if not NEWSDATA_API_KEY:
            print("⚠️ No NEWSDATA_API_KEY found in environment.")
            return []

        now = datetime.now()
        start = now - timedelta(days=MAX_AGE_DAYS)
        start_str = start.strftime("%Y-%m-%d")
        end_str = now.strftime("%Y-%m-%d")

        url = (
            f"https://newsdata.io/api/1/news?"
            f"apikey={NEWSDATA_API_KEY}&q={requests.utils.quote(query)}"
            f"&from_date={start_str}&to_date={end_str}"
            f"&language=en&category=technology"
        )
        try:
            resp = requests.get(url, timeout=15)
            data = resp.json()
            results = []
            for a in data.get("results", []):
                results.append({
                    "title": a.get("title"),
                    "summary": a.get("description"),
                    "url": a.get("link"),
                    "date": a.get("pubDate"),
                    "source": a.get("source_id"),
                })
            return results
        except Exception as e:
            print("❌ NewsData API error:", e)
            return []

def get_tavily_tool():
    if TavilySearchTool is None:
        raise RuntimeError("TavilySearchTool not available.")
    now = datetime.now()
    start = now - timedelta(days=MAX_AGE_DAYS)
    return TavilySearchTool(
        start_date=start.strftime("%Y-%m-%d"),
        end_date=now.strftime("%Y-%m-%d"),
    )

def get_search_tool(provider="hybrid"):
    provider = (provider or "hybrid").lower().strip()

    if provider in ("newsdata", "newdata"):
        return NewsDataTool()

    if provider == "tavily":
        return get_tavily_tool()

    if provider == "hybrid":
        tools = []
        try:
            tools.append(get_tavily_tool())
        except Exception as e:
            print("⚠️ Tavily unavailable in hybrid mode:", e)
        tools.append(NewsDataTool())

        # ✅ Hybrid tool is also a BaseTool
        class HybridTool(BaseTool):
            name: str = "hybrid_search"
            description: str = "Combine Tavily + NewsData.io search"

            def _run(self, query: str):
                results = []
                for t in tools:
                    try:
                        if hasattr(t, "_run"):
                            results.extend(t._run(query))
                        else:
                            results.extend(t.run(query))
                    except Exception as e:
                        print(f"⚠️ {t.name} failed:", e)
                return results

        return HybridTool()

    raise ValueError(f"Unknown provider: {provider}")
'''
'''
import os, requests
from datetime import datetime, timedelta
from config import MAX_AGE_DAYS

try:
    from crewai.tools import BaseTool   # ✅ correct BaseTool import
    from crewai_tools import TavilySearchTool
except ImportError:
    BaseTool = object
    TavilySearchTool = None

# ================= NewsData Tool =================
class NewsDataTool(BaseTool):
    name: str = "newsdata_search"
    description: str = "Fetches AI incident news from NewsData.io"

    def _run(self, query: str) -> list:
        api_key = os.getenv("NEWSDATA_API_KEY")
        if not api_key:
            print("⚠️ No NEWSDATA_API_KEY set")
            return []

        now = datetime.now()
        start = now - timedelta(days=MAX_AGE_DAYS)

        url = (
            f"https://newsdata.io/api/1/news?"
            f"apikey={api_key}&q={requests.utils.quote(query)}"
            f"&from_date={start.strftime('%Y-%m-%d')}&to_date={now.strftime('%Y-%m-%d')}"
            f"&language=en&category=technology"
        )
        try:
            resp = requests.get(url, timeout=15)
            data = resp.json()
            return [
                {
                    "title": a.get("title"),
                    "summary": a.get("description"),
                    "url": a.get("link"),
                    "date": a.get("pubDate"),
                    "source": a.get("source_id"),
                }
                for a in data.get("results", [])
            ]
        except Exception as e:
            print("❌ NewsData API error:", e)
            return []

# ================= Hybrid Tool =================
class HybridSearchTool(BaseTool):
    name: str = "hybrid_search"
    description: str = "Combines Tavily + NewsData.io for AI incident discovery"

    def _run(self, query: str):
        results = []
        # Try Tavily
        if TavilySearchTool:
            try:
                now = datetime.now()
                start = now - timedelta(days=MAX_AGE_DAYS)
                tavily = TavilySearchTool(
                    start_date=start.strftime("%Y-%m-%d"),
                    end_date=now.strftime("%Y-%m-%d")
                )
                results += tavily.run(query) or []
            except Exception as e:
                print("⚠️ Tavily failed:", e)
        # Always try NewsData
        try:
            newsdata = NewsDataTool()
            results += newsdata._run(query) or []
        except Exception as e:
            print("⚠️ NewsData failed:", e)

        # Deduplicate by URL
        seen, unique = set(), []
        for r in results:
            url = r.get("url")
            if url and url not in seen:
                seen.add(url)
                unique.append(r)
        return unique

# ================= Selector =================
def get_search_tool(provider="hybrid"):
    provider = (provider or "hybrid").lower().strip()
    if provider in ("newsdata", "newdata"):
        return NewsDataTool()
    elif provider == "tavily":
        if not TavilySearchTool:
            raise RuntimeError("Tavily not available")
        now = datetime.now()
        start = now - timedelta(days=MAX_AGE_DAYS)
        return TavilySearchTool(
            start_date=start.strftime("%Y-%m-%d"),
            end_date=now.strftime("%Y-%m-%d")
        )
    elif provider == "hybrid":
        return HybridSearchTool()
    else:
        raise ValueError(f"Unknown provider: {provider}")
'''

import os
import requests
from crewai_tools import TavilySearchTool
from datetime import datetime, timedelta
from config import MAX_AGE_DAYS

# Load API key for NewsData.io
NEWSDATA_API_KEY = os.getenv("NEWSDATA_API_KEY")

class NewsDataTool:
    def __init__(self, max_age_days=180):
        self.name = "newsdata_search"
        self.description = "Fetches AI incident news from NewsData.io"
        self.max_age_days = max_age_days

    def run(self, query: str):
        if not NEWSDATA_API_KEY:
            print("⚠️ No NEWSDATA_API_KEY found in environment.")
            return []

        now = datetime.utcnow()
        start = now - timedelta(days=self.max_age_days)
        start_date_str = start.strftime("%Y-%m-%d")
        end_date_str = now.strftime("%Y-%m-%d")

        url = (
            f"https://newsdata.io/api/1/news?"
            f"apikey={NEWSDATA_API_KEY}&q={query}"
            f"&from_date={start_date_str}&to_date={end_date_str}"
            f"&language=en&category=technology"
        )
        try:
            resp = requests.get(url, timeout=15)
            data = resp.json()
            results = []
            for a in data.get("results", []):
                results.append({
                    "title": a.get("title"),
                    "summary": a.get("description"),
                    "url": a.get("link"),
                    "date": a.get("pubDate"),
                    "source": a.get("source_id"),
                })
            return results
        except Exception as e:
            print("❌ Error querying NewsData.io:", e)
            return []

def get_tavily_tool():
    now = datetime.now()
    start = now - timedelta(days=MAX_AGE_DAYS)
    return TavilySearchTool(
        start_date=start.strftime("%Y-%m-%d"),
        end_date=now.strftime("%Y-%m-%d")
    )

def deduplicate_results(results):
    seen, unique = set(), []
    for r in results:
        url = r.get("url") or r.get("source", "")
        if url and url not in seen:
            seen.add(url)
            unique.append(r)
    return unique

def get_search_tool(provider="hybrid"):
    provider = provider.lower()

    if provider == "tavily":
        return get_tavily_tool()

    elif provider == "newsdata":
        return NewsDataTool(max_age_days=MAX_AGE_DAYS)

    elif provider == "hybrid":
        tavily = get_tavily_tool()
        newsdata = NewsDataTool(max_age_days=MAX_AGE_DAYS)

        class HybridTool:
            def __init__(self):
                self.name = "hybrid_search"
                self.description = "Combines Tavily + NewsData.io for AI incident discovery"

            def run(self, query: str):
                t_res = tavily.run(query) or []
                n_res = newsdata.run(query) or []
                return deduplicate_results(t_res + n_res)

        return HybridTool()

    else:
        raise ValueError(f"Unknown provider: {provider}")


