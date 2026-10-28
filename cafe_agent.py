import os
import re
import inspect
import json
import html
from collections import Counter
from datetime import datetime

import streamlit as st
import pandas as pd
from groq import Groq

st.set_page_config(page_title="The Critical Hit Café", page_icon="🎲", layout="wide", initial_sidebar_state="collapsed")

esc = html.escape

FULL = {"width": "stretch"} if "width" in inspect.signature(st.button).parameters else {"use_container_width": True}

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,700&family=JetBrains+Mono:wght@500&family=Plus+Jakarta+Sans:wght@400,500,600&display=swap');

    :root {
        --bg-canvas: #F4F0EA;
        --bg-surface: #FFFFFF;
        --bg-subtle: #EBE5DC;
        --border-subtle: #DCD4C8;
        --brand-forest: #183226;
        --accent-clay: #C85A32;
        --accent-brass: #D49B35;
        --text-ink: #191816;
        --text-muted: #666055;
        --status-open-bg: #E3F2EA;  --status-open-text: #1B6542;
        --status-taken-bg: #FCE8E4; --status-taken-text: #9E2A1C;
        --font-serif: 'Fraunces', Georgia, serif;
        --font-sans: 'Plus Jakarta Sans', system-ui, sans-serif;
        --font-mono: 'JetBrains Mono', ui-monospace, monospace;
    }

    html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"], .main {
        background: var(--bg-canvas) !important; color: var(--text-ink);
    }
    [data-testid="stHeader"], header[data-testid="stHeader"] { background: var(--bg-canvas) !important; }
    [data-testid="stSidebar"] { background: var(--bg-subtle) !important; }
    [data-testid="stSidebar"], [data-testid="collapsedControl"], [data-testid="stSidebarCollapsedControl"] { display: none; }
    #MainMenu, footer { visibility: hidden; }
    .block-container { padding-top: 1.6rem; max-width: 1500px; }

    .stApp, .stApp label, .stApp input, .stApp textarea, .stApp button { font-family: var(--font-sans); }
    [data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] li,
    [data-testid="stWidgetLabel"] p, [data-testid="stWidgetLabel"] label { color: var(--text-ink); }
    [data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p { color: var(--text-muted) !important; }
    .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5 {
        font-family: var(--font-serif); font-weight: 700; letter-spacing: -0.02em; color: var(--brand-forest);
    }
    pre, code, [data-testid="stCode"] * { font-family: var(--font-mono) !important; }
    [data-testid="stCode"] pre { background: var(--bg-subtle) !important; }
    [data-testid="stCode"] code { color: var(--text-ink) !important; }

    .hero {
        display: flex; align-items: center; justify-content: space-between; gap: 20px; flex-wrap: wrap;
        padding: 24px 28px; margin-bottom: 20px; border-radius: 18px; color: var(--bg-canvas);
        background:
            radial-gradient(620px 230px at 10% -10%, rgba(212,155,53,.22), transparent 60%),
            radial-gradient(520px 260px at 96% 115%, rgba(244,240,234,.12), transparent 60%),
            radial-gradient(rgba(244,240,234,.07) 1px, transparent 1px) 0 0 / 16px 16px,
            var(--brand-forest);
        border: 1px solid #0f2219; box-shadow: 0 14px 30px -16px rgba(24,50,38,.6);
    }
    .hero .brand { display: flex; align-items: center; gap: 16px; }
    .hero .monogram {
        width: 54px; height: 54px; border-radius: 14px; display: grid; place-items: center; flex: none;
        background: var(--accent-brass); color: var(--brand-forest); font-family: var(--font-serif);
        font-weight: 700; font-size: 1.3rem; letter-spacing: -0.02em; box-shadow: inset 0 0 0 2px rgba(24,50,38,.18);
    }
    .hero .brand-name { font-family: var(--font-serif); font-weight: 700; letter-spacing: -0.02em; font-size: 1.75rem; line-height: 1.1; color: var(--bg-canvas); }
    .hero .brand-sub { font-size: .82rem; color: rgba(244,240,234,.74); margin-top: 6px; max-width: 760px; }
    .status-row { display: flex; gap: 8px; flex-wrap: wrap; }
    .gpill {
        display: inline-flex; align-items: center; gap: 8px; padding: 6px 14px; border-radius: 999px;
        font-size: .78rem; font-weight: 500; color: var(--bg-canvas);
        background: rgba(244,240,234,.10); border: 1px solid rgba(244,240,234,.24);
        -webkit-backdrop-filter: blur(8px); backdrop-filter: blur(8px);
    }
    .gpill i { width: 7px; height: 7px; border-radius: 50%; background: rgba(244,240,234,.6); display: inline-block; }
    .gpill.ok i { background: #6FD3A0; } .gpill.bad i { background: #F08A72; } .gpill.warn i { background: var(--accent-brass); }

    .kpi { position: relative; background: var(--bg-surface); border: 1px solid var(--border-subtle); border-radius: 14px;
           padding: 16px 18px; box-shadow: 0 1px 2px rgba(24,50,38,.05); }
    .kpi .k-ico { position: absolute; top: 14px; right: 14px; width: 34px; height: 34px; border-radius: 10px;
                  background: var(--bg-subtle); color: var(--brand-forest); display: grid; place-items: center; }
    .kpi .k-ico svg { width: 18px; height: 18px; }
    .kpi .k-label { color: var(--text-muted); font-size: .8rem; font-weight: 600; padding-right: 44px; }
    .kpi .k-val { font-family: var(--font-serif); font-weight: 700; letter-spacing: -0.02em; font-size: 2.15rem; color: var(--brand-forest); margin: 8px 0 2px; line-height: 1.1; }
    .kpi .k-sub { font-size: .78rem; color: var(--text-muted); }
    .segs { display: flex; gap: 3px; margin-top: 13px; }
    .segs i { flex: 1; height: 6px; border-radius: 2px; background: var(--bg-subtle); }
    .segs i.on { background: var(--c); }

    .sec { display: flex; align-items: baseline; gap: 12px; margin: 4px 0 12px 0; }
    .sec h3 { margin: 0; padding: 0; font-size: 1.3rem; }
    .sec span { color: var(--text-muted); font-size: .82rem; }
    .sub { font-size: .78rem; font-weight: 600; color: var(--text-muted); margin: 18px 0 8px 0; }

    [data-testid="stVerticalBlockBorderWrapper"] { border-color: var(--border-subtle) !important; border-radius: 14px; }
    [data-testid="stChatMessage"] {
        background: var(--bg-surface); border: 1px solid var(--border-subtle); border-left: 3px solid var(--brand-forest);
        border-radius: 12px; padding: 12px 16px; margin-bottom: 10px; box-shadow: 0 2px 8px rgba(24,50,38,.06);
    }
    [data-testid="stChatMessage"]:has(.msg-user) {
        background: var(--brand-forest); border: 1px solid var(--brand-forest); box-shadow: 0 2px 8px rgba(24,50,38,.2);
    }
    [data-testid="stChatMessage"]:has(.msg-user) *:not(code):not(pre) { color: var(--bg-canvas) !important; }
    .msg-user { display: none; }
    [data-testid^="stChatMessageAvatar"] { background: var(--bg-subtle) !important; color: var(--brand-forest) !important; }
    [data-testid="stChatInput"] { background: var(--bg-subtle); border: 1px solid var(--border-subtle); border-radius: 14px; }
    [data-testid="stChatInput"]:focus-within { border-color: var(--accent-clay); box-shadow: 0 0 0 3px rgba(200,90,50,.18); }
    [data-testid="stChatInput"] textarea { background: transparent !important; color: var(--text-ink) !important; }
    [data-testid="stChatInput"] textarea::placeholder { color: var(--text-muted) !important; }
    [data-testid="stChatInputSubmitButton"] { background: var(--accent-clay) !important; color: #fff !important; border-radius: 10px; }
    [data-testid="stBottom"] > div { background: transparent !important; }

    .stButton > button, .stDownloadButton > button {
        border-radius: 999px; background: var(--bg-surface); border: 1px solid var(--border-subtle); color: var(--text-ink);
        font-weight: 600; font-size: .84rem; box-shadow: none; transition: background .14s ease, color .14s ease, transform .14s ease, border-color .14s ease;
    }
    .stButton > button p, .stDownloadButton > button p { color: inherit !important; font-weight: 600; }
    .stButton > button:hover, .stDownloadButton > button:hover {
        background: var(--brand-forest); border-color: var(--brand-forest); color: #FFFFFF; transform: translateY(-1px);
    }
    .stButton > button:focus-visible, .stDownloadButton > button:focus-visible { box-shadow: 0 0 0 3px rgba(200,90,50,.3); outline: none; }
    .stButton > button[kind="primary"], .stButton > button[data-testid="stBaseButton-primary"] {
        background: var(--accent-clay); border-color: var(--accent-clay); color: #FFFFFF;
    }
    .stButton > button[kind="primary"]:hover, .stButton > button[data-testid="stBaseButton-primary"]:hover { background: #B04D29; border-color: #B04D29; }

    [data-testid="stSlider"] [data-baseweb="slider"] [role="slider"] {
        background-color: var(--brand-forest) !important; border: 3px solid var(--accent-clay) !important;
        box-shadow: 0 0 0 4px rgba(200,90,50,.18) !important;
    }
    [data-testid="stSliderThumbValue"], [data-testid="stThumbValue"] { color: var(--accent-clay) !important; font-family: var(--font-mono); font-weight: 500; }
    [data-testid="stTickBarMin"], [data-testid="stTickBarMax"] { color: var(--text-muted) !important; font-family: var(--font-mono); }

    .stTabs [data-baseweb="tab-list"] { gap: 2px; border-bottom: 1px solid var(--border-subtle); background: transparent; }
    .stTabs [data-baseweb="tab"] { height: 44px; padding: 0 14px; background: transparent; color: var(--text-muted); font-weight: 600; font-size: .86rem; }
    .stTabs [data-baseweb="tab"] p { color: inherit !important; }
    .stTabs [aria-selected="true"], .stTabs [aria-selected="true"] p { color: var(--text-ink) !important; }
    .stTabs [data-baseweb="tab-highlight"] { background-color: var(--accent-clay); height: 3px; border-radius: 3px 3px 0 0; }
    .stTabs [data-baseweb="tab-border"] { background-color: var(--border-subtle); }

    [data-testid="stAlert"] { background: var(--bg-surface); border: 1px solid var(--border-subtle); border-radius: 12px; }
    [data-testid="stAlert"] p { color: var(--text-ink); }
    [data-testid="stDataFrame"] { border: 1px solid var(--border-subtle); border-radius: 12px; overflow: hidden; }
    [data-testid="stExpander"] { background: var(--bg-surface); border: 1px solid var(--border-subtle); border-radius: 12px; }
    [data-testid="stExpander"] summary p { color: var(--text-ink); }
    [data-testid="stMetric"] { background: var(--bg-surface); border: 1px solid var(--border-subtle); border-radius: 12px; padding: 12px 16px; }
    [data-testid="stMetricLabel"] p { color: var(--text-muted); }
    [data-testid="stMetricValue"] { font-family: var(--font-serif); color: var(--brand-forest); }
    .info-card { padding: 14px 16px; border-radius: 12px; background: var(--bg-surface); border: 1px solid var(--border-subtle); font-size: .86rem; line-height: 1.85; color: var(--text-ink); }
    .info-card span.k { color: var(--text-muted); display: inline-block; min-width: 150px; }

    .badge { display: inline-block; padding: 2px 10px; border-radius: 999px; font-size: .72rem; font-weight: 600;
             background: var(--bg-subtle); color: var(--text-muted); border: 1px solid var(--border-subtle); }
    .badge.mono { font-family: var(--font-mono); font-weight: 500; }
    .badge.ok, .badge-vegan { background: var(--status-open-bg); color: var(--status-open-text); border-color: transparent; }
    .badge.no, .badge-warn { background: #F6E9CC; color: #7A5410; border-color: transparent; }

    .gcard { display: flex; gap: 14px; align-items: center; padding: 14px 16px; border-radius: 14px; margin-bottom: 12px;
             background: var(--bg-surface); border: 1px solid var(--border-subtle); box-shadow: 0 1px 2px rgba(24,50,38,.05); }
    .gcard.taken { border-left: 3px solid var(--accent-clay); }
    .gcard .gi { width: 50px; height: 50px; flex: none; border-radius: 12px; display: grid; place-items: center; background: var(--bg-subtle);
                 color: var(--brand-forest); font-family: var(--font-serif); font-weight: 700; font-size: 1.15rem; letter-spacing: -0.02em; }
    .gcard .gb { flex: 1; min-width: 0; }
    .gcard .gn { font-family: var(--font-serif); font-weight: 700; letter-spacing: -0.02em; font-size: 1.1rem; color: var(--brand-forest); }
    .gcard .gm { display: flex; gap: 6px; flex-wrap: wrap; align-items: center; margin-top: 5px; }
    .pips { display: flex; gap: 5px; margin-top: 10px; }
    .pip { width: 9px; height: 9px; border-radius: 50%; background: var(--border-subtle); box-sizing: border-box; }
    .pip.on { background: var(--accent-brass); opacity: .5; }
    .pip.you { background: var(--accent-brass); opacity: 1; box-shadow: 0 0 0 3px rgba(212,155,53,.3); }
    .pip.you:not(.on) { background: transparent; border: 2px solid var(--accent-brass); }
    .status { font-size: .74rem; font-weight: 600; padding: 5px 12px; border-radius: 999px; white-space: nowrap; }
    .status.free { background: var(--status-open-bg); color: var(--status-open-text); }
    .status.taken { background: var(--status-taken-bg); color: var(--status-taken-text); }

    .mcard { display: flex; gap: 14px; align-items: center; padding: 12px 16px; border-radius: 14px; background: var(--bg-surface);
             border: 1px solid var(--border-subtle); box-shadow: 0 1px 2px rgba(24,50,38,.05); }
    .mcard .mb { flex: 1; min-width: 0; }
    .mcard .mn { font-family: var(--font-serif); font-weight: 700; letter-spacing: -0.02em; font-size: 1.05rem; color: var(--brand-forest); }
    .mcard .mt { font-size: .8rem; color: var(--text-muted); margin-bottom: 6px; }
    .mcard .price { font-family: var(--font-mono); font-weight: 500; color: var(--text-ink); font-size: 1rem; }

    .floor { display: grid; grid-template-columns: repeat(5, 1fr); grid-template-rows: repeat(2, auto); gap: 10px; margin: 6px 0 8px 0; }
    .tbl { border-radius: 12px; padding: 10px 6px; text-align: center; min-height: 84px; line-height: 1.25;
           display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 3px; }
    .tbl .tn { font-family: var(--font-mono); font-weight: 500; font-size: .72rem; letter-spacing: .04em; opacity: .85; }
    .tbl .tg { font-weight: 600; font-size: .8rem; max-width: 100%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .tbl small { font-family: var(--font-mono); font-weight: 500; font-size: .68rem; }
    .tbl-free { background: var(--status-open-bg); border: 1px solid rgba(27,101,66,.28); color: var(--status-open-text); }
    .tbl-busy { background: var(--status-taken-bg); border: 1px solid rgba(200,90,50,.5); color: var(--status-taken-text); }
    .legend { font-size: .76rem; color: var(--text-muted); margin-bottom: 12px; }
</style>
""", unsafe_allow_html=True)

if str(st.get_option("theme.primaryColor") or "").lower() != "#c85a32":
    st.markdown("""<style>[data-testid="stSlider"] [data-baseweb="slider"] div[style*="linear-gradient"] { filter: hue-rotate(16deg) saturate(.62) brightness(.8); }</style>""", unsafe_allow_html=True)

DATA_FILE = "cafe_data.txt"
DB_FILE = "bookings.json"
ORDERS_FILE = "orders.json"

TOTAL_TABLES = 10
MAX_PARTY = 6
COVER_PER_PERSON = 5.0
TAX_RATE = 0.05
OPEN_TEXT = "12:00 PM to 10:00 PM"
OPEN_MIN = 12 * 60    
CLOSE_MIN = 22 * 60   

ALL_GAMES = [
    {"name": "Catan", "genre": "Strategy", "players": "3-4 players"},
    {"name": "Ticket to Ride", "genre": "Family", "players": "2-5 players"},
    {"name": "Wingspan", "genre": "Strategy/Nature", "players": "1-5 players"},
    {"name": "Codenames", "genre": "Party/Word", "players": "2-8 players"},
    {"name": "Betrayal at House on the Hill", "genre": "Horror/Co-op", "players": "3-6 players"}
]

MENU_PRICES = {
    "Meeple Mocha": 4.50,
    "Oat Milk Upgrade": 0.50,
    "Almond Milk Upgrade": 0.50,
    "Health Potion Smoothie": 6.00,
    "D20 Pepperoni Pizza": 12.00,
    "Vegan Margherita Pizza": 14.00,
    "Bowl of Dice Mixed Nuts": 4.00
}

MENU_DETAILS = {
    "Meeple Mocha": {"category": "drink", "emoji": "☕", "vegan": False, "vegetarian": True, "nut_free": True,
                     "note": "Oat or almond milk for +$0.50"},
    "Health Potion Smoothie": {"category": "drink", "emoji": "🧪", "vegan": True, "vegetarian": True, "nut_free": True,
                               "note": "Berry, vegan"},
    "D20 Pepperoni Pizza": {"category": "food", "emoji": "🍕", "vegan": False, "vegetarian": False, "nut_free": True,
                            "note": "Contains meat"},
    "Vegan Margherita Pizza": {"category": "food", "emoji": "🍅", "vegan": True, "vegetarian": True, "nut_free": True,
                               "note": "Fully vegan"},
    "Bowl of Dice Mixed Nuts": {"category": "snack", "emoji": "🥜", "vegan": True, "vegetarian": True, "nut_free": False,
                                "note": "Contains peanuts"},
}

DEFAULT_CAFE_DATA = """Business Name: The Critical Hit Board Game Café
Location: 123 Meeple Street
Hours: Tuesday - Sunday, 12:00 PM to 10:00 PM (Closed Mondays)

Rules & Policies:
- Table cover charge is $5 per person for a standard 2-hour gameplay session (longer sessions such as 3+ hours can be arranged with staff or pro-rated at +$2.50/person per extra hour if tables are free).
- Maximum party size is 6 people per table (10 tables total in café, max café capacity is 60 guests across all 10 tables).
- Large groups (>6 people) can be split across multiple tables up to our available table capacity.
- Outside food and drink are strictly prohibited.
- Board games are for in-store play only (1 copy of each game in stock; multi-table groups can also share party games like Codenames or rotate games across tables).

Food & Drink Menu:
- Meeple Mocha: $4.50 (Oat and Almond milk available for +$0.50)
- Health Potion Smoothie (Berry/Vegan): $6.00
- D20 Pepperoni Pizza: $12.00
- Vegan Margherita Pizza: $14.00
- Bowl of Dice Mixed Nuts (contains peanuts): $4.00

Available Board Game Library:
- Catan (Strategy, 3-4 players)
- Ticket to Ride (Family, 2-5 players)
- Wingspan (Strategy/Nature, 1-5 players)
- Codenames (Party/Word, 2-8 players)
- Betrayal at House on the Hill (Horror/Co-op, 3-6 players)"""

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        f.write(DEFAULT_CAFE_DATA)

for file_path in [DB_FILE, ORDERS_FILE]:
    if not os.path.exists(file_path):
        with open(file_path, "w") as f:
            json.dump([], f)


def read_text_file(path):
    for enc in ("utf-8", "cp1252", "latin-1"):
        try:
            with open(path, "r", encoding=enc) as f:
                return f.read().replace("\r\n", "\n")
        except UnicodeDecodeError:
            continue
    return DEFAULT_CAFE_DATA


cafe_context = read_text_file(DATA_FILE)


def load_json(path):
    try:
        with open(path, "r") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception:
        return []


def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=4)


def parse_time_slot(text):
    if not text:
        return None
    low = str(text).lower()
    low = re.sub(r"\b(?:for\s+)?\d+(?:\.\d+)?\s*(?:hours?|hrs?|minutes?|mins?)\b", "", low)
    if "noon" in low:
        return 720, "12:00 PM"
    m = re.search(r"(\d{1,2})(?:[:.](\d{2}))?\s*(a\.?m\.?|p\.?m\.?)?", low)
    if not m:
        return None
    h = int(m.group(1))
    minute = int(m.group(2) or 0)
    mer = (m.group(3) or "").replace(".", "")
    if minute > 59 or h > 24:
        return None
    if mer == "pm" and h < 12:
        h += 12
    elif mer == "am" and h == 12:
        h = 0
    elif not mer:
        if 1 <= h <= 9:
            h += 12
    total = h * 60 + minute
    hh = (h % 12) or 12
    return total, f"{hh}:{minute:02d} {'PM' if h >= 12 else 'AM'}"


def cafe_open_status():
    now = datetime.now()
    mins = now.hour * 60 + now.minute
    if now.weekday() == 0:
        return False, "Closed today (Mondays) · opens Tue 12 PM"
    if OPEN_MIN <= mins < CLOSE_MIN:
        return True, "Open now · closes 10:00 PM"
    if mins < OPEN_MIN:
        return False, "Closed · opens 12:00 PM"
    return False, "Closed · opens tomorrow 12:00 PM" if now.weekday() != 6 else "Closed · opens Tue 12:00 PM"


def player_range(players_text):
    nums = [int(n) for n in re.findall(r"\d+", players_text)]
    if not nums:
        return 1, 99
    return nums[0], nums[-1]


def check_reservations():
    bookings = load_json(DB_FILE)
    reserved_games = [b.get("game_name", "") for b in bookings]
    available_games = [g["name"] for g in ALL_GAMES if g["name"].lower() not in [r.lower() for r in reserved_games]]
    return json.dumps({
        "status": "Success",
        "total_tables": TOTAL_TABLES,
        "tables_booked": len(bookings),
        "tables_available": TOTAL_TABLES - len(bookings),
        "current_reservations": bookings,
        "available_games": available_games,
        "reserved_games": reserved_games
    })


def reserve_table_and_game(customer_name: str = "Guest", party_size: int = 2, game_name: str = "", time_slot: str = "Tonight"):
    customer_name = str(customer_name or "Guest").strip() or "Guest"
    time_slot = str(time_slot or "Tonight").strip() or "Tonight"
    try:
        party_size = int(party_size)
    except (TypeError, ValueError):
        return json.dumps({"status": "Failed", "reason": "Party size must be a number."})
    if party_size > MAX_PARTY:
        return json.dumps({
            "status": "Failed",
            "reason": f"Maximum party size is {MAX_PARTY} people per single table. For a group of {party_size}, use `plan_group_booking` or `reserve_group_tables` to split across multiple tables."
        })
    if party_size < 1:
        return json.dumps({"status": "Failed", "reason": "Party size must be at least 1."})

    valid_games = [g["name"] for g in ALL_GAMES]
    matched_game = next((g for g in valid_games if g.lower() == str(game_name).strip().lower()), None)
    if not matched_game:
        matched_game = next((g for g in valid_games if g.lower() in str(game_name).strip().lower() or str(game_name).strip().lower() in g.lower()), None)
    if not matched_game:
        return json.dumps({
            "status": "Failed",
            "reason": f"'{game_name}' is not in our library. Available games: {', '.join(valid_games)}."
        })

    game = next(g for g in ALL_GAMES if g["name"] == matched_game)
    lo, hi = player_range(game["players"])
    if not (lo <= party_size <= hi):
        fits = [g["name"] for g in ALL_GAMES if player_range(g["players"])[0] <= party_size <= player_range(g["players"])[1]]
        return json.dumps({
            "status": "Failed",
            "reason": f"{matched_game} supports {game['players']}, whereas your party has {party_size}. Games that fit {party_size} players: {', '.join(fits) or 'none'}."
        })

    parsed = parse_time_slot(time_slot)
    if parsed:
        minutes, normalized = parsed
        if not (OPEN_MIN <= minutes < CLOSE_MIN):
            return json.dumps({
                "status": "Failed",
                "reason": f"{normalized} is outside our opening hours (12:00 PM to 10:00 PM, closed Mondays)."
            })
        time_slot = normalized

    bookings = load_json(DB_FILE)
    if len(bookings) >= TOTAL_TABLES:
        return json.dumps({"status": "Failed", "reason": "All 10 tables are currently booked."})
    for b in bookings:
        if b.get("game_name", "").lower() == matched_game.lower():
            return json.dumps({
                "status": "Failed",
                "reason": f"'{matched_game}' is already reserved by {b.get('customer_name')} at {b.get('time_slot')}. Please pick another game!"
            })

    cover_total = party_size * COVER_PER_PERSON
    new_booking = {
        "customer_name": customer_name,
        "party_size": party_size,
        "game_name": matched_game,
        "time_slot": time_slot,
        "cover_fee": f"${cover_total:.2f}"
    }
    bookings.append(new_booking)
    save_json(DB_FILE, bookings)

    return json.dumps({
        "status": "Success",
        "message": f"Booked table for {customer_name} ({party_size} guests) to play {matched_game} at {time_slot}. Table cover fee: ${cover_total:.2f} (for 2 hours)."
    })


def cancel_reservation(customer_name: str = "Guest"):
    bookings = load_json(DB_FILE)
    updated = [b for b in bookings if b.get("customer_name", "").lower() != str(customer_name).strip().lower()]
    if len(updated) == len(bookings):
        return json.dumps({"status": "Failed", "reason": f"No reservation found under the name '{customer_name}'."})
    save_json(DB_FILE, updated)
    return json.dumps({"status": "Success", "message": f"Reservation for {customer_name} has been cancelled and the game is back in stock."})


def modify_reservation(customer_name: str = "Guest", new_time_slot: str = "", new_party_size: int = 0):
    bookings = load_json(DB_FILE)
    idx = next((i for i, b in enumerate(bookings) if b.get("customer_name", "").lower() == str(customer_name).strip().lower()), None)
    if idx is None:
        return json.dumps({"status": "Failed", "reason": f"No reservation found under the name '{customer_name}'."})
    booking = bookings[idx]

    if new_time_slot:
        parsed = parse_time_slot(new_time_slot)
        if parsed:
            minutes, normalized = parsed
            if not (OPEN_MIN <= minutes < CLOSE_MIN):
                return json.dumps({"status": "Failed", "reason": f"{normalized} is outside our opening hours (12:00 PM to 10:00 PM)."})
            booking["time_slot"] = normalized
        else:
            booking["time_slot"] = new_time_slot

    try:
        new_party_size = int(new_party_size or 0)
    except (TypeError, ValueError):
        new_party_size = 0
    if new_party_size:
        if not (1 <= new_party_size <= MAX_PARTY):
            return json.dumps({"status": "Failed", "reason": "Party size must be between 1 and 6."})
        game = next((g for g in ALL_GAMES if g["name"] == booking.get("game_name")), None)
        if game:
            lo, hi = player_range(game["players"])
            if not (lo <= new_party_size <= hi):
                return json.dumps({"status": "Failed", "reason": f"{game['name']} needs {game['players']}, so it can't host {new_party_size} players."})
        booking["party_size"] = new_party_size
        booking["cover_fee"] = f"${new_party_size * COVER_PER_PERSON:.2f}"

    bookings[idx] = booking
    save_json(DB_FILE, bookings)
    return json.dumps({"status": "Success", "message": f"Updated reservation: {json.dumps(booking)}"})


VIBE_MAP = {
    "horror": ["horror", "scary", "spooky", "creepy", "halloween"],
    "co-op": ["co-op", "coop", "cooperative", "team", "together"],
    "family": ["family", "kids", "kid", "easy", "beginner", "casual", "light", "chill", "simple"],
    "party": ["party", "fun", "funny", "group", "icebreaker", "social"],
    "word": ["word", "words", "clue"],
    "strategy": ["strategy", "competitive", "brain", "thinking", "heavy", "planning"],
    "nature": ["nature", "birds", "relaxing", "calm", "peaceful"],
}


def recommend_games(party_size: int = 0, vibe: str = ""):
    try:
        party_size = int(party_size or 0)
    except (TypeError, ValueError):
        party_size = 0
    reserved = [b.get("game_name", "").lower() for b in load_json(DB_FILE)]
    vibe_low = str(vibe or "").lower()
    wanted = [tag for tag, words in VIBE_MAP.items() if any(w in vibe_low for w in words)]
    results = []
    for g in ALL_GAMES:
        lo, hi = player_range(g["players"])
        fits = (lo <= party_size <= hi) if party_size else True
        matches = [t for t in wanted if t in g["genre"].lower()]
        results.append({
            "name": g["name"], "genre": g["genre"], "players": g["players"],
            "fits_party_size": fits,
            "available_now": g["name"].lower() not in reserved,
            "vibe_match": bool(matches) if wanted else None,
            "_score": (fits, g["name"].lower() not in reserved, len(matches))
        })
    results.sort(key=lambda r: r["_score"], reverse=True)
    for r in results:
        r.pop("_score")
    return json.dumps({"status": "Success", "party_size": party_size or "not specified", "vibe": vibe or "any", "games": results})


def search_menu(dietary: str = "any", category: str = "any", max_price: float = 0):
    dietary = str(dietary or "any").lower().replace("-", "_").replace(" ", "_")
    category = str(category or "any").lower()
    try:
        max_price = float(max_price or 0)
    except (TypeError, ValueError):
        max_price = 0
    items = []
    for name, d in MENU_DETAILS.items():
        if dietary == "vegan" and not d["vegan"]:
            continue
        if dietary == "vegetarian" and not d["vegetarian"]:
            continue
        if dietary in ("nut_free", "peanut_free", "nut") and not d["nut_free"]:
            continue
        if category in ("drink", "food", "snack") and d["category"] != category:
            continue
        if max_price and MENU_PRICES[name] > max_price:
            continue
        items.append({"name": name, "price": f"${MENU_PRICES[name]:.2f}", "category": d["category"], "note": d["note"]})
    return json.dumps({
        "status": "Success", "filter": {"dietary": dietary, "category": category, "max_price": max_price or None},
        "items": items,
        "reminder": "Almond milk upgrade contains almonds; the café cannot guarantee zero cross-contact, so guests with severe allergies should speak to staff."
    })


def _plan_group(total_guests, time_slot="", duration_hours=2):
    try:
        total = int(total_guests)
    except (TypeError, ValueError):
        return {"status": "Failed", "reason": "Guest count must be a number."}
    if total < 1:
        return {"status": "Failed", "reason": "Guest count must be at least 1."}
    try:
        duration_hours = float(duration_hours or 2)
    except (TypeError, ValueError):
        duration_hours = 2.0
    if duration_hours <= 0:
        duration_hours = 2.0

    normalized_time = str(time_slot or "").strip()
    parsed = parse_time_slot(normalized_time) if normalized_time else None
    if parsed:
        minutes, normalized_time = parsed
        if not (OPEN_MIN <= minutes < CLOSE_MIN):
            return {"status": "Failed", "reason": f"{normalized_time} is outside our opening hours (12:00 PM to 10:00 PM, closed Mondays)."}
        if minutes + int(duration_hours * 60) > CLOSE_MIN:
            return {
                "status": "Failed",
                "reason": f"A {duration_hours:g}-hour session starting at {normalized_time} would run past our 10:00 PM closing time. Please pick an earlier start time (e.g. by {10 - int(duration_hours)}:00 PM)."
            }

    bookings = load_json(DB_FILE)
    tables_free = TOTAL_TABLES - len(bookings)
    max_capacity = tables_free * MAX_PARTY
    if total > max_capacity:
        return {
            "status": "Failed",
            "reason": f"We currently have {tables_free} open tables (max {MAX_PARTY} guests per table = {max_capacity} guests max right now), so we cannot seat {total} guests at once.",
            "max_guests_now": max_capacity,
            "tables_free": tables_free
        }

    tables_needed = -(-total // MAX_PARTY)
    base_size = total // tables_needed
    remainder = total % tables_needed
    sizes = [base_size + (1 if i < remainder else 0) for i in range(tables_needed)]

    reserved = {b.get("game_name", "").lower() for b in bookings}
    free_games = [g for g in ALL_GAMES if g["name"].lower() not in reserved]
    used_games = set()
    plan_rows = []

    for idx, sz in enumerate(sizes):
        chosen = None
        for g in free_games:
            lo, hi = player_range(g["players"])
            if g["name"] not in used_games and lo <= sz <= hi:
                chosen = g["name"]
                used_games.add(chosen)
                break
        if not chosen:
            for g in free_games:
                if g["name"] not in used_games:
                    chosen = g["name"]
                    used_games.add(chosen)
                    break
        if not chosen:
            chosen = ALL_GAMES[idx % len(ALL_GAMES)]["name"]
        plan_rows.append({"table": idx + 1, "party_size": sz, "game_name": chosen})

    standard_cover = total * COVER_PER_PERSON
    extra_hours = max(0.0, duration_hours - 2.0)
    extra_fee = total * 2.50 * extra_hours
    total_fee = standard_cover + extra_fee

    return {
        "status": "Success",
        "total_guests": total,
        "tables_needed": tables_needed,
        "time_slot": normalized_time or "Tonight",
        "duration_hours": duration_hours,
        "plan": plan_rows,
        "cover_fee_2hr": f"${standard_cover:.2f}",
        "extra_time_fee": f"${extra_fee:.2f}" if extra_hours > 0 else "$0.00",
        "cover_fee_total": f"${total_fee:.2f}",
        "tables_free": tables_free,
        "games_free": len(free_games)
    }


def plan_group_booking(total_guests: int = 0, time_slot: str = "", duration_hours: float = 2.0):
    plan = _plan_group(total_guests, time_slot, duration_hours)
    if plan["status"] == "Success":
        plan["note"] = (
            "Each table seats up to 6 guests. Standard cover is $5/person for 2 hours "
            "(extra time beyond 2 hours is estimated at +$2.50/person per hour, subject to staff confirmation)."
        )
    return json.dumps(plan)


def reserve_group_tables(customer_name: str = "Guest", total_guests: int = 0, time_slot: str = "Tonight", duration_hours: float = 2.0):
    customer_name = str(customer_name or "Guest").strip() or "Guest"
    time_slot = str(time_slot or "Tonight").strip() or "Tonight"
    plan = _plan_group(total_guests, time_slot if time_slot != "Tonight" else "", duration_hours)
    if plan["status"] != "Success":
        return json.dumps(plan)
    bookings = load_json(DB_FILE)
    dur_hrs = plan.get("duration_hours", 2.0)
    per_person_rate = COVER_PER_PERSON + max(0.0, dur_hrs - 2.0) * 2.50
    slot_label = plan["time_slot"] if dur_hrs == 2 else f"{plan['time_slot']} ({dur_hrs:g} hrs)"
    for item in plan["plan"]:
        bookings.append({
            "customer_name": customer_name,
            "party_size": item["party_size"],
            "game_name": item["game_name"],
            "time_slot": slot_label,
            "cover_fee": f"${item['party_size'] * per_person_rate:.2f}"
        })
    save_json(DB_FILE, bookings)
    return json.dumps({
        "status": "Success",
        "message": f"Booked {plan['tables_needed']} tables for {customer_name}'s group of {plan['total_guests']} at {slot_label}. Total cover fee: {plan['cover_fee_total']}.",
        "tables": plan["plan"]
    })


NUMBER_WORDS = {"a": 1, "an": 1, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6}


def _split_quantity(item: str):
    m = re.match(r"^\s*(\d+)\s*(?:x|×)?\s+(.*)$", item, re.I)
    if m:
        return max(1, min(int(m.group(1)), 20)), m.group(2)
    m = re.match(r"^\s*(a|an|one|two|three|four|five|six)\s+(.*)$", item, re.I)
    if m:
        return NUMBER_WORDS[m.group(1).lower()], m.group(2)
    return 1, item


def calculate_food_order(customer_name: str = "Table Order", items: list = None):
    customer_name = str(customer_name or "Table Order").strip() or "Table Order"
    if isinstance(items, str):
        items = [x.strip() for x in items.split(",") if x.strip()]
    if not items:
        return json.dumps({"status": "Failed", "reason": "No items were provided for the order."})

    subtotal = 0.0
    matched_items = []
    for raw in items:
        qty, item = _split_quantity(str(raw))
        low = item.lower()
        names = []
        if "mocha" in low:
            names.append("Meeple Mocha")
            if "oat" in low:
                names.append("Oat Milk Upgrade")
            elif "almond" in low:
                names.append("Almond Milk Upgrade")
        else:
            candidates = [k for k in MENU_PRICES if k.lower() in low or low in k.lower()]
            exact = [k for k in candidates if k.lower() == low]
            if exact:
                candidates = exact
            if not candidates:
                return json.dumps({"status": "Failed", "reason": f"Item '{item}' is not on our menu."})
            if len(candidates) > 1:
                return json.dumps({"status": "Failed", "reason": f"'{item}' matches several items ({', '.join(candidates)}). Please specify which one."})
            names.append(candidates[0])
        for _ in range(qty):
            for n in names:
                subtotal += MENU_PRICES[n]
                matched_items.append(f"{n} (${MENU_PRICES[n]:.2f})")

    tax = round(subtotal * TAX_RATE, 2)
    total = round(subtotal + tax, 2)
    orders = load_json(ORDERS_FILE)
    orders.append({
        "customer": customer_name,
        "items": ", ".join(matched_items),
        "subtotal": f"${subtotal:.2f}",
        "tax_5pct": f"${tax:.2f}",
        "total": f"${total:.2f}",
        "placed_at": datetime.now().strftime("%I:%M %p").lstrip("0")
    })
    save_json(ORDERS_FILE, orders)

    result = {
        "status": "Success",
        "items": matched_items,
        "subtotal": f"${subtotal:.2f}",
        "tax": f"${tax:.2f}",
        "total": f"${total:.2f}"
    }
    if any("Bowl of Dice" in m for m in matched_items):
        result["allergy_warning"] = "Bowl of Dice contains peanuts."
    return json.dumps(result)


TOOL_REGISTRY = {
    "check_reservations": check_reservations,
    "reserve_table_and_game": reserve_table_and_game,
    "cancel_reservation": cancel_reservation,
    "modify_reservation": modify_reservation,
    "calculate_food_order": calculate_food_order,
    "recommend_games": recommend_games,
    "search_menu": search_menu,
    "plan_group_booking": plan_group_booking,
    "reserve_group_tables": reserve_group_tables,
}


def run_tool(name, args):
    fn = TOOL_REGISTRY.get(name)
    if not fn:
        return json.dumps({"error": "Unknown tool"})
    clean_args = {k: v for k, v in (args or {}).items() if v is not None}
    try:
        return fn(**clean_args)
    except Exception as e:
        return json.dumps({"status": "Failed", "reason": f"Tool error: {e}"})


tools = [
    {
        "type": "function",
        "function": {
            "name": "check_reservations",
            "description": "Checks the live reservation book for current bookings, available tables, and available board games tonight.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "reserve_table_and_game",
            "description": "Reserves a single table (1 to 6 guests) and a board game. Requires customer_name, party_size, game_name, and time_slot.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_name": {"type": "string", "description": "Customer's name (use 'Guest' if not provided)"},
                    "party_size": {"type": "integer", "description": "Number of guests (1-6)"},
                    "game_name": {"type": "string", "description": "Board game name from library"},
                    "time_slot": {"type": "string", "description": "Time of booking (e.g., 7:00 PM)"}
                },
                "required": ["customer_name", "party_size", "game_name", "time_slot"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "cancel_reservation",
            "description": "Cancels an existing table and game reservation by customer name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_name": {"type": "string", "description": "Customer name on the booking"}
                },
                "required": ["customer_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "modify_reservation",
            "description": "Changes the time slot and/or party size of an existing reservation by customer name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_name": {"type": "string", "description": "Customer name on the booking"},
                    "new_time_slot": {"type": "string", "description": "New time, e.g. 8:00 PM"},
                    "new_party_size": {"type": "integer", "description": "New number of guests (1-6)"}
                },
                "required": ["customer_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_food_order",
            "description": "Places a café food/drink order, calculates bill with 5% tax, and saves to orders database.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_name": {"type": "string", "description": "Customer name (or 'Table Order')"},
                    "items": {"type": "array", "items": {"type": "string"}, "description": "List of menu items ordered"}
                },
                "required": ["customer_name", "items"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "recommend_games",
            "description": "Recommends board games from the café library based on party size and mood/genre.",
            "parameters": {
                "type": "object",
                "properties": {
                    "party_size": {"type": "integer", "description": "Number of players"},
                    "vibe": {"type": "string", "description": "Mood or genre keywords"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_menu",
            "description": "Filters the café menu by dietary need (vegan, vegetarian, nut_free), category (drink, food, snack) and/or max price.",
            "parameters": {
                "type": "object",
                "properties": {
                    "dietary": {"type": "string", "description": "vegan | vegetarian | nut_free | any"},
                    "category": {"type": "string", "description": "drink | food | snack | any"},
                    "max_price": {"type": "number", "description": "Maximum price in dollars"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "plan_group_booking",
            "description": "For large groups (>6 guests, e.g. 20 people): calculates how many tables are needed, assigns board games, and calculates cover fee for 2 hours or custom duration_hours.",
            "parameters": {
                "type": "object",
                "properties": {
                    "total_guests": {"type": "integer", "description": "Total number of guests in the large group"},
                    "time_slot": {"type": "string", "description": "Desired start time, e.g. 7:00 PM"},
                    "duration_hours": {"type": "number", "description": "Duration in hours (default is 2)"}
                },
                "required": ["total_guests"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "reserve_group_tables",
            "description": "Books multiple tables at once for a large group (>6 guests, e.g. 20 people). Call this when the user wants to book/reserve for a large group.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_name": {"type": "string", "description": "Name for the group booking (use 'Guest' if not given)"},
                    "total_guests": {"type": "integer", "description": "Total number of guests"},
                    "time_slot": {"type": "string", "description": "Start time of booking, e.g. 7:00 PM or 'Tonight'"},
                    "duration_hours": {"type": "number", "description": "Duration in hours (default is 2)"}
                },
                "required": ["customer_name", "total_guests", "time_slot"]
            }
        }
    }
]


def get_client_and_model():
    default_model = "qwen/qwen3.8-27b"
    key = st.session_state.get("custom_groq_key") or os.environ.get("GROQ_API_KEY")
    if not key:
        try:
            key = st.secrets.get("GROQ_API_KEY")
        except Exception:
            key = None
    if not key:
        try:
            from dotenv import load_dotenv
            load_dotenv()
            key = os.environ.get("GROQ_API_KEY")
        except Exception:
            key = None

    if not key:
        return None, "offline-fallback"

    if st.session_state.get("_cached_key") == key and st.session_state.get("_cached_client") is not None:
        return st.session_state["_cached_client"], st.session_state.get("_cached_model", default_model)

    try:
        client_obj = Groq(api_key=key, max_retries=2)
        active_model = default_model
        try:
            available_models = [
                m.id for m in client_obj.models.list().data
                if not any(bad in m.id.lower() for bad in ["whisper", "guard", "tts", "embed", "vision", "audio"])
            ]
            for preferred in ["llama-3.3", "qwen", "llama-3.1", "llama3", "mixtral", "gemma"]:
                for m in available_models:
                    if preferred in m.lower():
                        active_model = m
                        break
                if active_model != default_model:
                    break
            if active_model == default_model and available_models:
                active_model = available_models[0]
        except Exception:
            active_model = default_model

        st.session_state["_cached_key"] = key
        st.session_state["_cached_client"] = client_obj
        st.session_state["_cached_model"] = active_model
        return client_obj, active_model
    except Exception:
        return None, "offline-fallback"


client, ACTIVE_MODEL = get_client_and_model()

def _any(patterns, text):
    return any(re.search(p, text) for p in patterns)


BLOCKED_TASK_PATTERNS = [
    r"ignore (all |any |your |the |previous |prior |above )+(instructions|rules|prompt)",
    r"(reveal|show|print|repeat|tell me) (me )?(your|the) (system )?(prompt|instructions)",
    r"system prompt", r"jailbreak", r"developer mode", r"\bdan mode\b",
    r"you are now\b", r"pretend (to be|you)", r"role-?play", r"\bact as\b", r"forget (everything|your)",
    r"write (me )?(a |an |some |the )?(python|java|javascript|c\+\+|html|css|sql|code|script|program|function|poem|essay|story|song|rap|joke|article|blog|speech|letter|cover letter|email)",
    r"\b(python|javascript|typescript|java|c\+\+|html|css|sql)\b",
    r"\b(tell|give|say|sing|make up) (me |us )?(a |an |some )?(joke|riddle|story|poem|song|limerick)",
    r"\b(homework|assignment|exam|quiz me|thesis)\b",
    r"\btranslate\b",
]

OFFTOPIC_PATTERNS = [
    r"weather|forecast|temperature outside|\brain(ing)?\b", r"\bnews\b|headline", r"politic|election|president|prime minister|government|\bmodi\b|\btrump\b",
    r"\bstocks?\b|bitcoin|crypto|invest|forex|share price", r"movie|\bfilm\b|netflix|celebrity|\bactor\b|\bsinger\b|anime",
    r"cricket|football|soccer|\bnba\b|\bipl\b|world cup|who won", r"capital of|population of|who invented|who is\b|who was\b|how tall|how old is|history of|meaning of|\bdefine\b",
    r"\bjokes?\b|riddle|poem|\bstory\b|lyrics", r"\bmath\b|equation|integral|derivative|square root",
    r"medical|symptom|doctor|medicine|diagnos|disease|legal advice|lawyer|\bloan\b|insurance|tax return",
    r"recipe|ingredients for", r"flight|\bhotel\b|\bvisa\b|train ticket",
    r"chatgpt|openai|gemini|\bllm\b|who (made|created|built) you|which model|\bai model\b",
    r"\blove\b.*\byou\b|girlfriend|boyfriend|dating|\bhoroscope|astrology", r"\bgdp\b|\bplanet\b|\bgalaxy\b|\bscience\b",
]

REFUSALS = [
    "I can only help with questions about The Critical Hit Board Game Café.",
    "That's outside what I can help with. I'm limited to topics about The Critical Hit Café.",
    "I'm not able to help with that, as I only handle questions about the café.",
]
REFUSAL_MENU = (
    "\n\nI can help with:\n"
    "- **Games:** check what's on the shelf or recommend one for your group\n"
    "- **Tables:** book, change, or cancel a reservation (including multi-table groups & extended hours)\n"
    "- **Food & drink:** browse the menu (vegan / nut-free options) and place an order\n"
    "- **Café info:** hours, location, cover charge, and house rules"
)


def is_on_topic(text: str, history: list):
    low = text.lower().strip()
    if _any(BLOCKED_TASK_PATTERNS, low):
        return False, "blocked_task"
    if _any(OFFTOPIC_PATTERNS, low):
        return False, "offtopic"
    return True, "allowed"


def scope_refusal(n: int) -> str:
    return REFUSALS[n % len(REFUSALS)] + REFUSAL_MENU


def md_safe(text: str) -> str:
    return re.sub(r"(?<!\\)\$", r"\\$", text or "")


def clean_reply(text):
    text = text or ""
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S)
    text = text.split("</think>")[-1].replace("<think>", "").strip()
    return text or "I've updated that for you! Let me know if you need anything else."


WELCOME = ("Welcome to **The Critical Hit Board Game Café**! 🎲 Ask me about our vegan-friendly menu, "
           "check live game availability, place a snack order, or book a table!")


def get_system_prompt():
    live_state = check_reservations()
    return {
        "role": "system",
        "content": f"""You are the warm, helpful, and professional AI Concierge for The Critical Hit Board Game Café.
Use this business context strictly:
{cafe_context}

Live Reservation Database State:
{live_state}

Core Operating Rules:
- Never output <think> tags.
- Keep your tone natural, conversational, and helpful. Remember context from earlier messages in the conversation!
- LIVE AVAILABILITY: Use `check_reservations` or the Live Reservation Database State above to report exact open tables (out of 10), existing bookings, and available games.
- SINGLE TABLE BOOKINGS (1 to 6 guests): Call `reserve_table_and_game`. If `customer_name` isn't given, ask for their name and preferred time slot, or use 'Guest' if they ask to book immediately.
- LARGE GROUPS (more than 6 guests, e.g., 20 people):
  * A single table holds a maximum of 6 people, and the café has 10 tables total (up to 60 guests max when all 10 tables are free).
  * When a user asks about a large group (e.g. 20 people), call `plan_group_booking(total_guests=20)` to show how they will be split across multiple tables (e.g., 4 tables of 5 people) and quote the cover charge.
  * When they ask to book/confirm the large group (or follow up with a duration like "book for 3 hours" or a time/name), call `reserve_group_tables` (if they gave a name/time) or `plan_group_booking` with their `duration_hours` and ask for their name and start time to finalize!
- EXTENDED DURATION (e.g., "for 3 hours"):
  * Standard table cover is $5.00 per person for 2 hours.
  * If a guest asks to book for 3 hours (or more), explain that standard sessions are 2 hours ($5/person), and an extra hour is +$2.50/person (so $7.50/person for 3 hours, or $150 total for 20 guests for 3 hours), and offer to lock in their booking once they confirm a start time and name.
- MODIFY / CANCEL / FOOD / RECOMMENDATIONS:
  * Use `modify_reservation` to change time or party size, `cancel_reservation` to cancel, `calculate_food_order` to place food/drink orders, `recommend_games` for game suggestions, and `search_menu` for dietary filters.
- STRICT SCOPE: Only discuss The Critical Hit Board Game Café. Politely decline unrelated topics (weather, coding, politics, sports, general trivia)."""
    }


if "messages" not in st.session_state:
    st.session_state.messages = [
        get_system_prompt(),
        {"role": "assistant", "content": WELCOME}
    ]
if "pending" not in st.session_state:
    st.session_state.pending = None
if "blocked_count" not in st.session_state:
    st.session_state.blocked_count = 0
if "last_error" not in st.session_state:
    st.session_state.last_error = ""
if client is None and not st.session_state.last_error:
    st.session_state.last_error = "GROQ_API_KEY not found in environment. Paste your key in the Admin tab or set $env:GROQ_API_KEY."
if "engine_mode" not in st.session_state:
    st.session_state.engine_mode = "AI" if client else "Fallback"


NAME_STOPWORDS = {
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
    "tomorrow", "noon", "dinner", "lunch", "evening", "night", "everyone", "all",
    "catan", "ticket", "wingspan", "codenames", "betrayal", "monopoly", "tonight",
    "today", "me", "us", "the", "a", "an", "my", "our", "three", "two", "four",
    "five", "six", "hours", "hour", "hrs", "people", "guests", "table", "tables"
}

def extract_name(text: str, default: str = "") -> str:
    # Now perfectly captures case-insensitive prefixes and lower-case names
    for m in re.finditer(r"(?i)(?:i'?m|i am|this is|my name is|name is|name'?s|under|for|on the name)\s+([a-z]+)", text):
        cand = m.group(1)
        if cand.lower() not in NAME_STOPWORDS:
            return cand.title()
    return default

def extract_duration_hours(text: str):
    m = re.search(r"(\d+(?:\.\d+)?)\s*(?:hours?|hrs?)\b", text.lower())
    if m:
        return float(m.group(1))
    word_map = {"one": 1.0, "two": 2.0, "three": 3.0, "four": 4.0, "five": 5.0}
    m2 = re.search(r"\b(one|two|three|four|five)\s+(?:hours?|hrs?)\b", text.lower())
    if m2:
        return word_map[m2.group(1).lower()]
    return None

def explicit_party(text: str):
    low = text.lower()
    m = (re.search(r"(\d+)\s*\+?\s*(?:people|persons|guests|ppl|pax|of us|players|friends)", low)
         or re.search(r"\b(?:party of|table of|group of|we are|we're|there are|total of|for)\s+(\d+)\b(?!\s*(?:hours?|hrs?|mins?|minutes?|:|[ap]\.?m))", low))
    return int(m.group(1)) if m else None

def extract_time(text: str):
    low = re.sub(r"\b(?:for\s+)?\d+(?:\.\d+)?\s*(?:hours?|hrs?|minutes?|mins?)\b", "", text.lower())
    m = re.search(r"(\d{1,2}(?::\d{2})?\s*[ap]\.?m\.?)", low)
    if not m:
        m = re.search(r"(?:\bat|\bfrom|@|\baround|\bby)\s*(\d{1,2}(?::\d{2})?)(?!\d)(?!\s*(?:hours?|hrs?|people|persons|guests|ppl|pax|min|[ap]\.?m))", low)
    return parse_time_slot(m.group(1)) if m else None

def find_game(text: str):
    low = text.lower()
    if "monopoly" in low:
        return "Monopoly"
    for g in ALL_GAMES:
        n = g["name"].lower()
        if n in low or n.split()[0] in low:
            return g["name"]
    return None

def _fallback_order(user_text: str, low: str) -> str:
    ordered = []
    for k in MENU_PRICES:
        if k.lower() in low:
            m = re.search(r"(\d+)\s*(?:x\s*)?" + re.escape(k.lower()), low)
            ordered.append(f"{m.group(1)} {k}" if m else k)
    if not ordered:
        ordered = ["Vegan Margherita Pizza", "Health Potion Smoothie"]
    res = json.loads(calculate_food_order(extract_name(user_text, "Guest") or "Guest", ordered))
    if res["status"] != "Success":
        return f"🚫 {res['reason']}"
    return f"✅ **Order Confirmed!** Added {', '.join(res['items'])}. **Subtotal:** {res['subtotal']} | **5% Tax:** {res['tax']} | **Total:** {res['total']}."

def local_fallback_router(user_text: str) -> str:
    low = user_text.lower().strip()
    pend = st.session_state.get("pending") or {}

    name = extract_name(user_text, "")
    
    # Catch standalone 1-2 word names when the bot is waiting for a name
    if not name and pend and not pend.get("name"):
        clean_words = [w for w in user_text.split() if w.lower() not in NAME_STOPWORDS and w.isalpha()]
        if 1 <= len(clean_words) <= 2:
            name = clean_words[0].title()

    party = explicit_party(user_text)
    dur = extract_duration_hours(user_text)
    t = extract_time(user_text)
    game = find_game(user_text)

    if not party and pend.get("total"):
        party = pend["total"]
    elif not party and pend.get("party"):
        party = pend["party"]

    if (party and party > MAX_PARTY) or (pend.get("kind") == "group" and (dur or t or name or re.search(r"\b(book|reserve|yes|sure|ok|confirm|lock|do it|please)\b", low))):
        total_guests = party or pend.get("total", 20)
        duration_hrs = dur or pend.get("duration", 2.0)
        slot = (t[1] if t else None) or pend.get("time")
        cust_name = name or pend.get("name")

        st.session_state.pending = {
            "kind": "group",
            "total": total_guests,
            "duration": duration_hrs,
            "time": slot,
            "name": cust_name
        }

        plan = json.loads(plan_group_booking(total_guests, slot or "", duration_hrs))
        if plan["status"] != "Success":
            return f"🚫 {plan['reason']}"

        # Book now works seamlessly with "lock in" or "confirm"
        if cust_name and slot and (re.search(r"\b(book|reserve|yes|sure|ok|confirm|please|lock|do it)\b", low) or pend.get("awaiting_confirm")):
            res = json.loads(reserve_group_tables(cust_name, total_guests, slot, duration_hrs))
            if res["status"] == "Success":
                st.session_state.pending = None
                lines = "\n".join(f"- Table {x['table']}: **{x['party_size']} guests** → *{x['game_name']}*" for x in res["tables"])
                return f"✅ **Group Reservation Confirmed!** {res['message']}\n\n{lines}"
            return f"🚫 {res['reason']}"

        st.session_state.pending["awaiting_confirm"] = True
        sizes = " + ".join(str(x["party_size"]) for x in plan["plan"])
        lines = "\n".join(f"- Table {x['table']}: **{x['party_size']} guests** → *{x['game_name']}*" for x in plan["plan"])
        dur_text = (
            f"- **Duration & Cover Fee ({duration_hrs:g} hours):** Standard cover is **$5.00/person for 2 hours** (${total_guests * 5:.2f}). "
            f"Adding {duration_hrs - 2:g} extra hour(s) (+$2.50/person/hr) brings the total to **{plan['cover_fee_total']}**."
            if duration_hrs > 2 else
            f"- **Cover Charge (2 hours):** **{plan['cover_fee_total']}** total ($5.00 per person for 2 hours of gameplay)."
        )
        missing_parts = []
        if not cust_name:
            missing_parts.append("your **name**")
        if not slot:
            missing_parts.append("your preferred **start time** (12:00 PM – 10:00 PM)")
        ask_str = (
            f"To lock in all **{plan['tables_needed']} tables** for **{duration_hrs:g} hours**, just reply with {' and '.join(missing_parts)}!"
            if missing_parts else
            f"Reply **'Confirm'** to lock in all {plan['tables_needed']} tables under **{cust_name}** at **{slot}** for **{duration_hrs:g} hours**!"
        )
        return (
            f"👥 **Group Plan for {total_guests} Guests ({duration_hrs:g} Hours):**\n"
            f"Since our maximum is **{MAX_PARTY} guests per table**, we can seat your group across **{plan['tables_needed']} tables** ({sizes}):\n"
            f"{lines}\n\n"
            f"{dur_text}\n\n"
            f"{ask_str}"
        )

    if dur and not party:
        extra = max(0.0, dur - 2.0) * 2.50
        return (
            f"⏱️ **Booking for {dur:g} Hours:**\n"
            f"Our standard table cover is **$5.00 per person for 2 hours**. You can extend your session to **{dur:g} hours** "
            f"for **+${extra:.2f}/person** (${5.0 + extra:.2f}/person total, as long as it finishes before our 10:00 PM closing time).\n\n"
            "How many guests are in your party, which game would you like, and what **start time** works best for you?"
        )

    if any(k in low for k in ["any reservation", "reservations tonight", "empty table", "free table", "available", "availability"]):
        state = json.loads(check_reservations())
        if not state["current_reservations"]:
            return f"✅ **All 10 tables and all 5 board games are currently open tonight!** ({', '.join(state['available_games'])}). Would you like me to book a table for you?"
        booked_str = "; ".join([f"**{b['customer_name']}** ({b['party_size']} guests, *{b['game_name']}* @ {b['time_slot']})" for b in state["current_reservations"]])
        return f"📅 **Live Café Status:** We have **{state['tables_available']} / 10 tables available** tonight.\n- **Current Bookings:** {booked_str}\n- **Available Games on Shelf:** {', '.join(state['available_games'])}"

    if re.search(r"opening hours|business hours|your hours|what are (the|your) hours|when do you (open|close)|what time do you (open|close)|closing time|are you open|\baddress\b|where are you|\blocated\b|\blocation\b", low):
        return "ℹ️ **Café Info:** We're located at **123 Meeple Street**, open **Tuesday – Sunday, 12:00 PM to 10:00 PM** (closed Mondays)."

    if "cancel" in low:
        cname = name or "Guest"
        if cname == "Guest":
            return "No problem! What **name** is the reservation under so I can cancel it?"
        res = json.loads(cancel_reservation(cname))
        return f"✅ {res['message']}" if res["status"] == "Success" else f"🚫 {res['reason']}"

    if "game" in low and any(k in low for k in ["recommend", "suggest", "which", "what should", "pick"]):
        res = json.loads(recommend_games(party or 0, user_text))
        lines = [f"- **{g['name']}** ({g['genre']} • {g['players']}) — {'🟢 Available' if g['available_now'] else '🔴 Reserved'}" for g in res["games"]]
        return "🎲 **Board Game Recommendations:**\n" + "\n".join(lines)

    if re.search(r"\border(s|ed|ing)?\b", low) or "pizza" in low or "smoothie" in low or "mocha" in low:
        return _fallback_order(user_text, low)

    if "vegan" in low or "cover" in low or "menu" in low or "allerg" in low or "nut" in low:
        return (
            "🥗 **Menu, Dietary Info & Cover Policy:**\n"
            "- **Vegan Margherita Pizza:** $14.00 *(100% Vegan, Nut-Free)*\n"
            "- **Health Potion Smoothie (Berry):** $6.00 *(100% Vegan, Nut-Free)*\n"
            "- **D20 Pepperoni Pizza:** $12.00 *(Nut-Free)*\n"
            "- **Meeple Mocha:** $4.50 *(Vegetarian; Oat/Almond milk upgrade +$0.50)*\n"
            "- **Bowl of Dice Mixed Nuts:** $4.00 *(Vegan, ⚠️ Contains Peanuts)*\n\n"
            "**Table Cover Policy:** $5.00 per person for 2 hours of gameplay (max 6 guests per table)."
        )

    if "book" in low or "reserve" in low or "table" in low or party or game or t:
        merged_party = party or pend.get("party")
        merged_game = game or pend.get("game")
        merged_time = (t[1] if t else None) or pend.get("time")
        merged_name = name or pend.get("name") or "Guest"
        st.session_state.pending = {"kind": "single", "party": merged_party, "game": merged_game, "time": merged_time, "name": merged_name}

        missing = []
        if not merged_party:
            missing.append("**party size** (1–6 guests)")
        if not merged_game:
            missing.append("**board game** (Catan, Ticket to Ride, Wingspan, Codenames, or Betrayal)")
        if not merged_time:
            missing.append("**start time** (12:00 PM – 10:00 PM)")
        if missing:
            return f"Happy to book your table! Please let me know your {', '.join(missing)}."

        res = json.loads(reserve_table_and_game(merged_name, merged_party, merged_game, merged_time))
        st.session_state.pending = None
        return f"✅ **Reservation Confirmed!** {res['message']}" if res["status"] == "Success" else f"🚫 **Unable to Complete Booking:** {res['reason']}"

    return "Welcome to **The Critical Hit Board Game Café**! 🎲 I can help you book a table (for small parties or large multi-table groups), check live game availability, browse our vegan-friendly menu, or place a food order. What can I get started for you?"


def build_api_messages(max_turns: int = 10):
    msgs = st.session_state.messages
    user_idx = [i for i, m in enumerate(msgs) if m["role"] == "user"]
    start = user_idx[-max_turns] if len(user_idx) > max_turns else 1
    allowed_keys = ("role", "content", "tool_calls", "tool_call_id", "name")
    out = [msgs[0]]
    for m in msgs[start:]:
        out.append({k: v for k, v in m.items() if k in allowed_keys})
    return out


def process_user_message(user_text):
    global client, ACTIVE_MODEL
    client, ACTIVE_MODEL = get_client_and_model()

    user_text = (user_text or "").strip()[:600]
    if not user_text:
        return

    st.session_state.messages[0] = get_system_prompt()

    allowed, _ = is_on_topic(user_text, st.session_state.messages)
    st.session_state.messages.append({"role": "user", "content": user_text})
    if not allowed:
        st.session_state.messages.append({"role": "assistant", "content": scope_refusal(st.session_state.blocked_count)})
        st.session_state.blocked_count += 1
        return

    if client is None:
        st.session_state.engine_mode = "Fallback"
        st.session_state.messages.append({"role": "assistant", "content": local_fallback_router(user_text)})
        return

    try:
        try:
            response = client.chat.completions.create(
                model=ACTIVE_MODEL,
                messages=build_api_messages(),
                tools=tools,
                tool_choice="auto"
            )
            response_message = response.choices[0].message
        except Exception:
            response = client.chat.completions.create(
                model=ACTIVE_MODEL,
                messages=build_api_messages()
            )
            response_message = response.choices[0].message

        rounds = 0
        while getattr(response_message, "tool_calls", None) and rounds < 3:
            rounds += 1
            st.session_state.messages.append({
                "role": "assistant",
                "content": response_message.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.function.name, "arguments": tc.function.arguments}
                    } for tc in response_message.tool_calls
                ]
            })
            for tool_call in response_message.tool_calls:
                fn_name = tool_call.function.name
                try:
                    args = json.loads(tool_call.function.arguments or "{}")
                except json.JSONDecodeError:
                    args = {}
                res = run_tool(fn_name, args)
                st.session_state.messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": fn_name,
                    "content": res
                })
            try:
                response = client.chat.completions.create(
                    model=ACTIVE_MODEL,
                    messages=build_api_messages(),
                    tools=tools,
                    tool_choice="auto" if rounds < 3 else "none"
                )
            except Exception:
                response = client.chat.completions.create(
                    model=ACTIVE_MODEL,
                    messages=build_api_messages()
                )
            response_message = response.choices[0].message

        st.session_state.messages.append({"role": "assistant", "content": clean_reply(response_message.content)})
        st.session_state.engine_mode = "AI"
        st.session_state.last_error = ""
    except Exception as e:
        st.session_state.last_error = f"{type(e).__name__}: {str(e)[:160]}"
        st.session_state.engine_mode = "Fallback"
        fallback_reply = local_fallback_router(user_text)
        st.session_state.messages.append({"role": "assistant", "content": fallback_reply})


def ask(text: str):
    with st.spinner("🎲 Rolling for initiative..."):
        process_user_message(text)
    st.rerun()


def reset_chat():
    st.session_state.pending = None
    st.session_state.messages = [get_system_prompt(), {"role": "assistant", "content": WELCOME}]


open_now, open_text = cafe_open_status()

DEMO_PROMPTS = [
    ("Check tonight's availability", "Are there any reservations tonight, and which tables and games are open?"),
    ("Vegan & cover rules (RAG)", "What vegan options do you have, and how much is the table cover charge?"),
    ("Book table for 4 (Catan @ 7 PM)", "Hi, I'm Alex. Can I book a table for 4 people to play Catan at 7:00 PM?"),
    ("Large Group: 20 people for 3 hours", "Can I make a reservation for 20 people for 3 hours tonight at 6:00 PM under Jordan?"),
    ("Order pizza & smoothie (tool)", "Can I place an order for Alex for 1 Vegan Margherita Pizza and 1 Health Potion Smoothie?"),
    ("Edge case: 8 guests + Monopoly", "Can I book a single table for 8 people to play Monopoly at 9:00 PM?"),
    ("Guardrail test: off-topic question", "What's the capital of France and who won the last cricket world cup?"),
]

def monogram(name: str) -> str:
    words = [w for w in re.findall(r"[A-Za-z]+", name) if w.lower() not in ("at", "to", "of", "the", "on")]
    return "".join(w[0].upper() for w in words[:2]) or "G"


engine_ok = st.session_state.engine_mode == "AI"
st.markdown(
    '<div class="hero"><div class="brand"><div class="monogram">CH</div><div>'
    '<div class="brand-name">The Critical Hit Board Game Café</div>'
    '<div class="brand-sub">AI Operations Hub · Autonomous RAG Knowledge Concierge • Multi-Tool Booking &amp; POS Engine • Real-Time State Sync</div>'
    '</div></div><div class="status-row">'
    f'<span class="gpill {"ok" if open_now else "bad"}"><i></i>{esc(open_text)}</span>'
    f'<span class="gpill {"ok" if engine_ok else "warn"}" title="{esc(st.session_state.last_error or "")}"><i></i>{"AI engine online" if engine_ok else "Fallback engine"}</span>'
    f'<span class="gpill"><i></i>{st.session_state.blocked_count} off-topic blocked</span>'
    '</div></div>', unsafe_allow_html=True)

bookings_data = load_json(DB_FILE)
orders_data = load_json(ORDERS_FILE)
reserved_games = [b.get("game_name", "").lower() for b in bookings_data]
unique_reserved_games = set(reserved_games)
total_guests = sum(int(b.get("party_size", 0)) for b in bookings_data)
cover_rev = sum(float(str(b.get("cover_fee", f"${int(b.get('party_size', 0)) * COVER_PER_PERSON:.2f}")).replace("$", "")) for b in bookings_data)
food_rev = sum(float(str(o.get("total", "$0")).replace("$", "")) for o in orders_data)

_SVG = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">{}</svg>'
KPI_ICONS = {
    "table": _SVG.format('<rect x="3" y="8" width="18" height="4" rx="1"/><path d="M6 12v7M18 12v7M3 19h4M17 19h4"/>'),
    "box": _SVG.format('<path d="M12 3l8 4.5v9L12 21l-8-4.5v-9L12 3z"/><path d="M4 7.5l8 4.5 8-4.5M12 12v9"/>'),
    "users": _SVG.format('<circle cx="9" cy="8" r="3"/><path d="M3 20c0-3.3 2.7-6 6-6s6 2.7 6 6"/><circle cx="17" cy="9" r="2.4"/><path d="M16 14.2c2.9.2 5 2.5 5 5.8"/>'),
    "coin": _SVG.format('<circle cx="12" cy="12" r="9"/><path d="M14.5 9.2c-.6-.8-1.5-1.2-2.6-1.2-1.5 0-2.4.8-2.4 1.9 0 2.7 5 1.4 5 4.1 0 1.2-1 2-2.6 2-1.2 0-2.2-.5-2.9-1.4M12 6v2M12 16v2"/>'),
}


def kpi(label, value, sub, color="#183226", pct=None, icon="table", segments=10):
    segs = ""
    if pct is not None:
        filled = round(max(0, min(100, pct)) / 100 * segments)
        segs = '<div class="segs">' + "".join(f'<i class="{"on" if i < filled else ""}"></i>' for i in range(segments)) + "</div>"
    return (f'<div class="kpi" style="--c:{color}"><div class="k-ico">{KPI_ICONS[icon]}</div><div class="k-label">{esc(label)}</div>'
            f'<div class="k-val">{esc(value)}</div><div class="k-sub">{esc(sub)}</div>{segs}</div>')


rev_total = cover_rev + food_rev
m1, m2, m3, m4 = st.columns(4)
m1.markdown(kpi("Tables Available", f"{TOTAL_TABLES - len(bookings_data)} / {TOTAL_TABLES}", f"-{len(bookings_data)} Booked",
                "#183226", 100 * (TOTAL_TABLES - len(bookings_data)) / TOTAL_TABLES, "table", TOTAL_TABLES), unsafe_allow_html=True)
m2.markdown(kpi("Games in Stock", f"{len(ALL_GAMES) - len(unique_reserved_games)} / {len(ALL_GAMES)}", f"{len(unique_reserved_games)} Checked Out",
                "#C85A32", 100 * (len(ALL_GAMES) - len(unique_reserved_games)) / len(ALL_GAMES), "box", len(ALL_GAMES)), unsafe_allow_html=True)
m3.markdown(kpi("Active Guests", f"{total_guests} Players", "Max 6/table",
                "#D49B35", 100 * total_guests / (TOTAL_TABLES * MAX_PARTY), "users", 10), unsafe_allow_html=True)
m4.markdown(kpi("Live Café Revenue", f"${rev_total:.2f}", f"Cover: ${cover_rev:.2f} | Food: ${food_rev:.2f}",
                "#1B6542", (100 * cover_rev / rev_total) if rev_total else 0, "coin", 10), unsafe_allow_html=True)

st.write("")

col1, col2 = st.columns([1.3, 1])

with col1:
    st.markdown('<div class="sec"><h3>Customer Support &amp; Booking Agent</h3><span>Live tools · scope-guarded</span></div>', unsafe_allow_html=True)
    chat_container = st.container(height=470)
    with chat_container:
        for msg in st.session_state.messages:
            if msg["role"] in ["user", "assistant"] and msg.get("content"):
                clean_text = msg["content"].split("</think>")[-1].strip()
                if clean_text:
                    with st.chat_message(msg["role"], avatar="🥂" if msg["role"] == "user" else "🎲"):
                        if msg["role"] == "user":
                            safe_text = clean_text.replace("<", "&lt;").replace(">", "&gt;")
                            st.markdown('<span class="msg-user"></span>' + md_safe(safe_text), unsafe_allow_html=True)
                        else:
                            st.markdown(md_safe(clean_text))

    q1, q2, q3, q4 = st.columns(4)
    if q1.button("Show menu", **FULL, key="chip_menu"):
        ask("What's on your menu and how much is everything?")
    if q2.button("Pick a game", **FULL, key="chip_game"):
        ask("Can you recommend a game for our group?")
    if q3.button("Hours", **FULL, key="chip_hours"):
        ask("What are your opening hours and where are you located?")
    if q4.button("Allergies", **FULL, key="chip_allergy"):
        ask("Which menu items are nut-free, and which are vegan?")

    if user_input := st.chat_input("Ask about menu, book a game table, or order food..."):
        ask(user_input)

with col2:
    st.markdown('<div class="sec"><h3>Live Café State &amp; Databases</h3><span>Updates as guests book</span></div>', unsafe_allow_html=True)
    tab1, tab2, tab3, tab_menu, tab_stats, tab4, tab_admin = st.tabs(
        ["Game Shelf", "Table Bookings", "Café Orders", "Menu", "Analytics", "RAG Context", "Admin"]
    )

    with tab1:
        st.caption("Real-time board game status (updates automatically when booked):")
        party_pick = st.select_slider("Highlight games that fit a party of:", options=list(range(1, MAX_PARTY + 1)), value=4)
        st.markdown('<div class="legend">Brass dots = supported player counts · <b>ringed dot</b> = your selected party size</div>', unsafe_allow_html=True)
        for g in ALL_GAMES:
            is_taken = g["name"].lower() in unique_reserved_games
            lo, hi = player_range(g["players"])
            fit_html = (f'<span class="badge ok">Fits {party_pick}</span>' if lo <= party_pick <= hi
                        else f'<span class="badge no">Needs {lo}–{hi}</span>')
            pips = "".join(f'<span class="pip{" on" if lo <= i <= hi else ""}{" you" if i == party_pick else ""}"></span>' for i in range(1, 9))
            if is_taken:
                holder = next((b.get("customer_name", "Guest") for b in bookings_data if b.get("game_name", "").lower() == g["name"].lower()), "Guest")
                status = f'<span class="status taken">Reserved by {esc(str(holder))}</span>'
            else:
                status = '<span class="status free">Available</span>'
            st.markdown(
                f'<div class="gcard{" taken" if is_taken else ""}"><div class="gi">{monogram(g["name"])}</div>'
                f'<div class="gb"><div class="gn">{esc(g["name"])}</div>'
                f'<div class="gm"><span class="badge">{esc(g["genre"])}</span><span class="badge mono">{esc(g["players"])}</span>{fit_html}</div>'
                f'<div class="pips">{pips}</div></div>{status}</div>', unsafe_allow_html=True)

    with tab2:
        st.markdown('<div class="legend">Café floor plan · T1–T10 · <span style="color:#1B6542;font-weight:600">open</span> · <span style="color:#9E2A1C;font-weight:600">reserved</span></div>', unsafe_allow_html=True)
        tiles = ""
        for i in range(TOTAL_TABLES):
            if i < len(bookings_data):
                b = bookings_data[i]
                tiles += (f'<div class="tbl tbl-busy" title="{esc(str(b.get("game_name", "")))} · {esc(str(b.get("time_slot", "")))}">'
                          f'<span class="tn">T{i + 1}</span><span class="tg">{esc(str(b.get("customer_name", "Guest")))}</span>'
                          f'<small>{esc(str(b.get("party_size", "")))} guests</small></div>')
            else:
                tiles += f'<div class="tbl tbl-free"><span class="tn">T{i + 1}</span><span class="tg">Open</span><small>Free</small></div>'
        st.markdown(f'<div class="floor">{tiles}</div>', unsafe_allow_html=True)
        st.write("")

        if bookings_data:
            st.dataframe(pd.DataFrame(bookings_data), **FULL, hide_index=True)
            st.caption("Quick actions:")
            for i, b in enumerate(bookings_data):
                c_a, c_b = st.columns([3, 1])
                c_a.markdown(f"**{esc(str(b.get('customer_name', 'Guest')))}** · {esc(str(b.get('game_name', '')))} · {esc(str(b.get('time_slot', '')))}", unsafe_allow_html=True)
                if c_b.button("Cancel", key=f"cancel_{i}", **FULL):
                    cancel_reservation(b.get("customer_name", ""))
                    st.toast(f"Cancelled reservation for {b.get('customer_name', 'Guest')}", icon="🗑️")
                    st.rerun()
            st.download_button("⬇️ Export bookings (CSV)", pd.DataFrame(bookings_data).to_csv(index=False), file_name="bookings.csv", **FULL)
        else:
            st.info("No active table reservations.")
        with st.expander("View Raw `bookings.json`"):
            st.json(bookings_data)

    with tab3:
        if orders_data:
            st.dataframe(pd.DataFrame(orders_data), **FULL, hide_index=True)
            st.download_button("⬇️ Export orders (CSV)", pd.DataFrame(orders_data).to_csv(index=False), file_name="orders.csv", **FULL)
        else:
            st.info("No food orders placed yet.")
        with st.expander("View Raw `orders.json`"):
            st.json(orders_data)

    with tab_menu:
        st.caption("Tap **Order** to have the concierge place it for you:")
        for name, d in MENU_DETAILS.items():
            badges = ""
            if d["vegan"]:
                badges += '<span class="badge badge-vegan">Vegan</span>'
            elif d["vegetarian"]:
                badges += '<span class="badge">Vegetarian</span>'
            if not d["nut_free"]:
                badges += '<span class="badge badge-warn">Contains peanuts</span>'
            c_card, c_btn = st.columns([4.2, 1], vertical_alignment="center")
            c_card.markdown(
                f'<div class="mcard"><div class="mb"><div class="mn">{esc(name)}</div>'
                f'<div class="mt">{esc(d["note"])}</div><span class="badge">{esc(d["category"].title())}</span>{badges}</div><div class="price">${MENU_PRICES[name]:.2f}</div></div>',
                unsafe_allow_html=True)
            if c_btn.button("Order", key=f"order_{name}", **FULL):
                ask(f"I'd like to order 1 {name}, please.")
        st.caption("Milk upgrades (+$0.50): Oat or Almond, ask for them with your Meeple Mocha. 5% tax is added to food orders.")

    with tab_stats:
        if not bookings_data and not orders_data:
            st.info("Analytics will appear once there are bookings or orders.")
        else:
            a1, a2 = st.columns(2)
            a1.metric("Avg party size", f"{(total_guests / len(bookings_data)):.1f}" if bookings_data else "–")
            a2.metric("Avg order value", f"${(food_rev / len(orders_data)):.2f}" if orders_data else "–")
            st.markdown("**Revenue split**")
            st.bar_chart(pd.DataFrame({"Revenue ($)": [cover_rev, food_rev]}, index=["Cover charges", "Food & drink"]))
            if orders_data:
                item_counter = Counter()
                for o in orders_data:
                    for name in re.findall(r"([^,]+?) \(\$[\d.]+\)", str(o.get("items", ""))):
                        item_counter[name.strip()] += 1
                if item_counter:
                    st.markdown("**Best sellers**")
                    st.bar_chart(pd.DataFrame({"Units sold": dict(item_counter)}))
            if bookings_data:
                st.markdown("**Guests by time slot**")
                slot_guests = Counter()
                for b in bookings_data:
                    slot_guests[str(b.get("time_slot", "?"))] += int(b.get("party_size", 0))
                st.bar_chart(pd.DataFrame({"Guests": dict(slot_guests)}))

    with tab4:
        st.caption("Source file: `cafe_data.txt`")
        st.code(cafe_context, language="markdown")

    with tab_admin:
        last_err = esc(st.session_state.last_error) if st.session_state.last_error else "None"
        st.markdown('<div class="sub">System status</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="info-card"><span class="k">Engine</span>{"AI (Groq)" if engine_ok else "Local fallback"}<br>'
            f'<span class="k">Model</span><code>{esc(str(ACTIVE_MODEL))}</code><br>'
            f'<span class="k">Off-topic blocked</span>{st.session_state.blocked_count}<br>'
            f'<span class="k">Last error</span>{last_err}<br>'
            f'<span class="k">Location</span>123 Meeple Street<br>'
            f'<span class="k">Hours</span>Tue–Sun, 12:00 PM – 10:00 PM<br>'
            f'<span class="k">Cover charge</span>$5/person (2 hrs) · max 6 per table</div>', unsafe_allow_html=True)

        st.markdown('<div class="sub">Groq API Key (Live Override)</div>', unsafe_allow_html=True)
        key_input = st.text_input("Paste GROQ_API_KEY here if top pill says Fallback:", value=st.session_state.get("custom_groq_key", ""), type="password")
        if key_input and key_input != st.session_state.get("custom_groq_key", ""):
            st.session_state["custom_groq_key"] = key_input.strip()
            os.environ["GROQ_API_KEY"] = key_input.strip()
            client, ACTIVE_MODEL = get_client_and_model()
            if client:
                st.session_state.engine_mode = "AI"
                st.session_state.last_error = ""
            st.rerun()

        st.markdown('<div class="sub">One-click demo prompts</div>', unsafe_allow_html=True)
        for i, (label, prompt) in enumerate(DEMO_PROMPTS):
            if st.button(label, key=f"demo_{i}", **FULL):
                ask(prompt)

        st.markdown('<div class="sub">Session</div>', unsafe_allow_html=True)
        transcript = "\n\n".join(
            f"{'You' if m['role'] == 'user' else 'Concierge'}: {clean_reply(m['content'])}"
            for m in st.session_state.messages if m["role"] in ("user", "assistant") and m.get("content")
        )
        ad1, ad2 = st.columns(2)
        ad1.download_button("Download transcript", transcript, file_name="critical_hit_chat.txt", **FULL)
        if ad2.button("Clear chat (keep data)", **FULL):
            reset_chat()
            st.rerun()

        st.markdown('<div class="sub">Data</div>', unsafe_allow_html=True)
        if st.button("Reset all demo data", type="primary", **FULL):
            with open(DB_FILE, "w") as f:
                json.dump([], f)
            with open(ORDERS_FILE, "w") as f:
                json.dump([], f)
            st.session_state.blocked_count = 0
            reset_chat()
            st.rerun()