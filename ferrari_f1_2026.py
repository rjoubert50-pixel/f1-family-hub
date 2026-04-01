import streamlit as st
import pandas as pd
import requests
import os
import feedparser
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# --- 1. THEME & ASSETS ---
st.set_page_config(page_title="F1 Paddock Hub", layout="wide", page_icon="🏎️")
st_autorefresh(interval=60000, key="f1_refresh")

# Red Bull Racing Palette
RB_NAVY = "#000B21"
RB_YELLOW = "#FFCC00"
RB_RED = "#E10600"

def safe_st_image(img_path, caption="", width=None, sidebar=False):
    target = st.sidebar if sidebar else st
    try:
        if img_path and (os.path.exists(img_path) or img_path.startswith("http")):
            target.image(img_path, caption=caption, width=width, use_container_width=(width is None))
    except: pass

def get_img(local_path, web_fallback="https://media.formula1.com/content/dam/fom-website/2018-redesign-assets/team-car-photos-16x9/2024/mclaren.png"):
    if os.path.exists(local_path): return local_path
    return web_fallback

# --- 2. GRID & PLAYER CONFIG ---
PLAYERS_CONFIG = {
    "Richie": {"drivers": ["max_verstappen", "perez"], "constructor": "audi", "penalty": 0},
    "Rickster": {"drivers": ["bottas", "leclerc"], "constructor": "aston_martin", "penalty": -5},
    "Yoshi": {"drivers": ["norris", "stroll"], "constructor": "ferrari", "penalty": -25},
    "Trip": {"drivers": ["lawson", "hadjar"], "constructor": "red_bull", "penalty": -5},
    "Josh": {"drivers": ["piastri", "hulkenberg"], "constructor": "haas", "penalty": 0},
    "Ruben": {"drivers": ["antonelli", "albon"], "constructor": "mercedes", "penalty": -5},
    "Clive": {"drivers": ["sainz", "russell"], "constructor": "racing_bulls", "penalty": 0},
    "Andy": {"drivers": ["hamilton", "bearman"], "constructor": "mclaren", "penalty": 0},
}

FULL_GRID_2026 = {
    "McLaren": {"drivers": ["norris", "piastri"], "car": "imagesf1/mclaren.jpg"},
    "Red Bull": {"drivers": ["max_verstappen", "hadjar"], "car": "imagesf1/red_bull.jpg"},
    "Ferrari": {"drivers": ["leclerc", "hamilton"], "car": "imagesf1/ferrari.jpg"},
    "Mercedes": {"drivers": ["russell", "antonelli"], "car": "imagesf1/mercedes.jpg"},
    "Aston Martin": {"drivers": ["alonso", "stroll"], "car": "imagesf1/aston_martin.jpg"},
    "Williams": {"drivers": ["sainz", "albon"], "car": "imagesf1/williams.jpg"},
    "Alpine": {"drivers": ["gasly", "colapinto"], "car": "imagesf1/alpine.jpg"},
    "Audi": {"drivers": ["hulkenberg", "bortoleto"], "car": "imagesf1/audi.jpg"},
    "Haas": {"drivers": ["ocon", "bearman"], "car": "imagesf1/haas.jpg"},
    "Racing_Bulls": {"drivers": ["lawson", "lindblad"], "car": "imagesf1/vcarb.jpg"},
    "Cadillac": {"drivers": ["perez", "bottas"], "car": "imagesf1/cadillac.jpg"},
}

# --- 3. THE CSS (RED BULL STYLE) ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: {RB_NAVY}; color: white; }}
    [data-testid="stSidebar"] {{ background-color: #041126 !important; border-right: 3px solid {RB_YELLOW}; }}
    .f1-card {{ background: #0a1a35; border-left: 5px solid {RB_RED}; padding: 15px; border-radius: 10px; margin-bottom: 10px; border-top: 1px solid #1a2a45; }}
    h1, h2, h3 {{ color: {RB_YELLOW} !important; font-family: 'Arial Black'; text-transform: uppercase; }}
    .stTabs [aria-selected="true"] {{ background-color: {RB_RED} !important; color: white !important; font-weight: bold; }}
    .ticker-wrap {{ background: #000; border-bottom: 2px solid {RB_YELLOW}; height: 35px; overflow: hidden; }}
    .ticker {{ display: inline-block; animation: ticker 60s linear infinite; white-space: nowrap; line-height: 35px; color: {RB_YELLOW}; font-weight: bold; }}
    @keyframes ticker {{ 0% {{ transform: translateX(0); }} 100% {{ transform: translateX(-100%); }} }}
    .sb-header {{ background: {RB_RED}; color: white; padding: 5px 10px; font-size: 12px; font-weight: bold; border-radius: 3px; margin: 15px 0; }}
    /* Custom Scrollbar */
    ::-webkit-scrollbar {{ width: 8px; }}
    ::-webkit-scrollbar-track {{ background: {RB_NAVY}; }}
    ::-webkit-scrollbar-thumb {{ background: {RB_RED}; border-radius: 10px; }}
    </style>
""", unsafe_allow_html=True)

# --- 4. DATA ENGINE (THE BRAIN) ---
BASE_URL = "https://api.jolpi.ca/ergast/f1"

@st.cache_data(ttl=600)
def fetch_api(endpoint):
    try:
        r = requests.get(f"{BASE_URL}/{endpoint}.json", timeout=10)
        return r.json() if r.status_code == 200 else None
    except: return None

@st.cache_data(ttl=3600)
def fetch_news():
    try:
        feed = feedparser.parse("https://www.formula1.com/en/latest/all.xml")
        return [{"title": e.title, "link": e.link} for e in feed.entries[:8]]
    except: return []

@st.cache_data(ttl=600)
def get_season_engine(year):
    """Calculates all points from every round manually to ensure Japan R3 is included."""
    players = {n: {"driver_pts": 0, "bonus_pts": 0, "total": cfg['penalty']} for n, cfg in PLAYERS_CONFIG.items()}
    history = {}
    
    r_data = fetch_api(f"{year}/results?limit=1000")
    if r_data and r_data['MRData']['RaceTable']['Races']:
        for race in r_data['MRData']['RaceTable']['Races']:
            r_num = int(race['round'])
            res = race['Results']
            
            # Find Fastest Lap (+2)
            fl_id = next((r['Driver']['driverId'] for r in res if r.get('FastestLap', {}).get('rank') == "1"), "")
            
            # Team Math
            t_wknd = {}
            for r in res:
                c_id = r['Constructor']['constructorId']
                t_wknd[c_id] = t_wknd.get(c_id, 0) + float(r['points'])
            
            ranked_t = sorted(t_wknd.items(), key=lambda x: x[1], reverse=True)
            top3 = [t[0] for t in ranked_t[:3]]
            winner_t = ranked_t[0][0] if ranked_t else ""
            
            history[r_num] = {n: 0 for n in PLAYERS_CONFIG.keys()}
            
            for n, cfg in PLAYERS_CONFIG.items():
                # Driver Pts
                d_pts = sum([float(r['points']) for r in res if r['Driver']['driverId'] in cfg['drivers']])
                # Bonus Pts
                b_pts = 0
                if cfg['constructor'] in top3: b_pts += [3, 2, 1][top3.index(cfg['constructor'])]
                if fl_id in cfg['drivers']: b_pts += 2
                if cfg['constructor'] == winner_t: b_pts += 2
                
                players[n]["driver_pts"] += d_pts
                players[n]["bonus_pts"] += b_pts
                players[n]["total"] += (d_pts + b_pts)
                history[r_num][n] = d_pts + b_pts
                
    return players, history

# --- 5. THE ORACLE (ADVANCED) ---
def get_oracle_advice(race, year):
    circuit = race['Circuit']['circuitId']
    # Logic: High speed vs Technical
    is_street = any(x in circuit for x in ['monaco', 'singapore', 'vegas', 'baku', 'miami'])
    
    advice = []
    oracle_data = [
        {"player": "Richie", "strength": "Straight line speed", "weakness": "Strategy errors", "chance": 85 if not is_street else 40},
        {"player": "Trip", "strength": "Tire management", "weakness": "Qualifying pace", "chance": 70},
        {"player": "Yoshi", "strength": "Wet weather master", "weakness": "Penalty baggage", "chance": 60},
        {"player": "Andy", "strength": "Late braker", "weakness": "Car reliability", "chance": 75}
    ]
    return sorted(oracle_data, key=lambda x: x['chance'], reverse=True)

# --- 6. SIDEBAR MISSION CONTROL ---
with st.sidebar:
    st.markdown(f'<h2><span class="status-light"></span> MISSION CONTROL</h2>', unsafe_allow_html=True)
    sel_year = st.selectbox("Season", [2026, 2025, 2024], index=0)
    stats, ledger = get_season_engine(sel_year)
    
    # NEXT RACE
    st.markdown('<div class="sb-header">🛰️ NEXT TARGET</div>', unsafe_allow_html=True)
    cal = fetch_api(str(sel_year))
    next_r = None
    if cal:
        for r in cal['MRData']['RaceTable']['Races']:
            if datetime.strptime(r['date'], '%Y-%m-%d') >= datetime.now():
                next_r = r; break
    if next_r:
        st.write(f"🚩 **{next_r['raceName'].upper()}**")
        st.caption(f"Location: {next_r['Circuit']['Location']['locality']}")
        diff = datetime.strptime(next_r['date'], '%Y-%m-%d') - datetime.now()
        st.write(f"⏱️ T-Minus: **{diff.days} Days**")

    # ORACLE
    st.markdown('<div class="sb-header">🔮 THE ORACLE</div>', unsafe_allow_html=True)
    if next_r:
        predictions = get_oracle_advice(next_r, sel_year)
        for p in predictions[:3]:
            st.write(f"**{p['player']}** - {p['chance']}%")
            st.caption(f"Adv: {p['strength']}")

# --- 7. MAIN HUB ---
# Top Standings Ticker
ticker_data = fetch_api(f"{sel_year}/driverStandings")
try:
    standings_list = ticker_data['MRData']['StandingsTable']['StandingsLists'][0]['DriverStandings']
    ticker_text = " | ".join([f"{d['position']}. {d['Driver']['familyName'].upper()} ({d['points']} PTS)" for d in standings_list])
except: ticker_text = f"UPCOMING: {next_r['raceName'].upper()} - {next_r['date']}"
st.markdown(f'<div class="ticker-wrap"><div class="ticker">{ticker_text} | {ticker_text}</div></div>', unsafe_allow_html=True)

st.title("🏎️ F1 FAMILY PADDOCK")
tabs = st.tabs(["🏆 CHAMPIONSHIP", "📜 HISTORY", "🛠️ GARAGE", "🏎️ THE GRID", "📰 NEWS"])

# CHAMPIONSHIP
with tabs[0]:
    st.subheader("Family World Standings")
    if stats:
        df_rows = [{"Player": n, "Driver Points": int(p['driver_pts']), "Bonus Points": int(p['bonus_pts']), "Penalty": PLAYERS_CONFIG[n]['penalty'], "GRAND TOTAL": int(p['total'])} for n, p in stats.items()]
        df = pd.DataFrame(df_rows).sort_values("GRAND TOTAL", ascending=False)
        st.dataframe(df, use_container_width=True, hide_index=True, column_config={
            "GRAND TOTAL": st.column_config.NumberColumn("TOTAL 🏆", format="%d"),
            "Penalty": st.column_config.NumberColumn("Start Penalty ⚠️", format="%d")
        })
    else: st.info("Waiting for Round 1 data...")

# HISTORY
with tabs[1]:
    if ledger:
        h_round = st.selectbox("Relive a Race:", sorted(ledger.keys(), reverse=True))
        st.markdown(f'<div class="f1-card"><h3>Round {h_round} Summary</h3></div>', unsafe_allow_html=True)
        h_df = pd.DataFrame([{"Player": n, "Points Gained": int(pts)} for n, pts in ledger[h_round].items()]).sort_values("Points Gained", ascending=False)
        st.dataframe(h_df, use_container_width=True, hide_index=True)
    else: st.info("The history books are empty... for now.")

# GARAGE & GRID (UNIFORM DESIGN)
def draw_entry(data_dict, is_grid=False):
    for name, cfg in data_dict.items():
        with st.expander(f"⚙️ {name.upper()}"):
            c1, c2, c3 = st.columns([1, 1, 1.3])
            with c1: safe_st_image(f"imagesf1/{cfg['drivers'][0]}.webp", caption="Racer 1")
            with c2: safe_st_image(f"imagesf1/{cfg['drivers'][1]}.webp", caption="Racer 2")
            with c3:
                t_key = cfg.get('constructor', name)
                # Find matching car name in FULL_GRID keys
                actual_key = next((k for k in FULL_GRID_2026 if k.lower().replace("_"," ") == t_key.lower().replace("_"," ")), "Ferrari")
                safe_st_image(f"imagesf1/{actual_key.lower().replace(' ', '_')}.jpg", caption="2026 Challenger")

with tabs[2]: draw_entry(PLAYERS_CONFIG)
with tabs[3]: draw_entry(FULL_GRID_2026, is_grid=True)

# NEWS
with tabs[4]:
    news_items = fetch_news()
    for n in news_items:
        st.markdown(f'<div class="f1-card"><b>{n["title"]}</b><br><a href="{n["link"]}" target="_blank" style="color:{RB_YELLOW}; font-size:12px;">READ FULL STORY →</a></div>', unsafe_allow_html=True)

st.markdown("<br><center><p style='color:#555;'>PADDOCK ENGINE BY ORACLE | RED BULL RACING 2026</p></center>", unsafe_allow_html=True)