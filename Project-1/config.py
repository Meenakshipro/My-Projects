# config.py - all project settings live here in one place.

import os
from pathlib import Path

_key_file = Path(__file__).with_name("API-KEY.txt")
API_KEY = os.getenv("SPORTRADAR_API_KEY", "")
if not API_KEY and _key_file.exists():
	API_KEY = _key_file.read_text(encoding="utf-8").strip()
BASE_URL = "https://api.sportradar.com/ncaafb/trial/v7/en"
DB_FILE = "ncaafb.db"

HOW_MANY_SEASONS = 50   # set above the real season count so any year can be found
RANKING_WEEKS = [1, 2, 3]   # project requires at least 1 week
POLL_TYPES = ["AP25", "EU25", "CFP25", "FCS25", "FCSC25"]  # all 5 Sportradar supports

HOW_MANY_TEAMS = 10     # trial keys are slow (1 req/sec) - keep this small
HOW_MANY_PLAYERS = 50   # each player is 1 extra API call
