from crewai_tools import TavilySearchTool
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



