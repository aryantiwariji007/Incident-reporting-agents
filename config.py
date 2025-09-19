

import yaml
from pathlib import Path

CONFIG_FILE = Path(__file__).parent / "config.yaml"

def load_config():
    if CONFIG_FILE.exists():
        with CONFIG_FILE.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}

config = load_config()

# Force correct types and defaults
MAX_AGE_DAYS = int(config.get("max_age_days", 180) or 180)
MAX_INCIDENTS = int(config.get("max_incidents", 3) or 3)
ALLOWED_SOURCES = config.get("allowed_sources", []) or []
SEARCH_TOOL = config.get("search_tool", "tavily")

