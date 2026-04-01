import streamlit as st
import pandas as pd
import requests
import os
import feedparser
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# --- 1. SETUP & THEME ---
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

def get_img(local_path, web_fallback=""):
    if os.path.exists(local_path): return local_path
    return web_fallback

# --- 2. PLAYER & GRID CONFIG ---
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

# --- 3. THE CSS ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: {RB_NAVY}; color: white; }}
    [data-testid="stSidebar"] {{ background-color: #041126 !important; border-right: 3px solid {RB_YELLOW}; }}
    .f1-card {{ background: #0a1a35; border-left: 5px solid {RB_RED}; padding: 15px; border-radius: 10px; margin-bottom: 10px; }}
    h1, h2, h3 {{ color: {RB_YELLOW} !important; font-family: 'Arial Black'; text-transform: uppercase; }}
    .ticker-wrap {{ background: #000; border-bottom: 2px solid {RB_YELLOW}; height: 35px; overflow: hidden; }}
    .ticker {{ display: inline-block; animation: ticker 60s linear infinite; white-space: nowrap; line-height: 35px; color: {RB_YELLOW}; font-weight: bold; }}
    @keyframes ticker {{ 0% {{ transform: translateX(0); }} 100% {{ transform: translateX(-100%); }} }}
    .sb-header {{ background: {RB_RED}; color: white; padding: 5px 10px; font-size: 12px; font-weight: bold; border-radius: 3px; margin: 15px 0; }}
    </style>
""", unsafe_allow_html=True)

# --- 4. DATA ENGINE ---
BASE_URL = "https://api.jolpi.ca/ergast/f1"

@st.cache_data(ttl=60)
def fetch_api(endpoint):
    try:
        r = requests.get(f"{BASE_URL}/{endpoint}.json", timeout=10)
        return r.json() if r.status_code == 200 else None
    except: return None

def get_paddock_engine(year, force_rounds=None):
    """Calculates points by scanning each round individually to force Japan R3 updates."""
    players = {n: {"driver_pts": 0, "bonus_pts": 0, "total": cfg['penalty']} for n, cfg in PLAYERS_CONFIG.items()}
    history = {}
    
    # We scan from 1 to the 'force_rounds' number (e.g., 3)
    for r_num in range(1, force_rounds + 1):
        data = fetch_api(f"{year}/{r_num}/results")
        if data and data['MRData']['RaceTable']['Races']:
            race = data['MRData']['RaceTable']['Races'][0]
            res = race['Results']
            
            # Fastest Lap
            fl_id = next((r['Driver']['driverId'] for r in res if r.get('FastestLap', {}).get('rank') == "1"), "")
            
            # Constructor Logic
            t_wknd = {}
            for r in res:
                c_id = r['Constructor']['constructorId']
                t_wknd[c_id] = t_wknd.get(c_id, 0) + float(r['points'])
            
            ranked_t = sorted(t_wknd.items(), key=lambda x: x[1], reverse=True)
            top3 = [t[0] for t in ranked_t[:3]]
            winner_t = ranked_t[0][0] if ranked_t else ""

            history[r_num] = {"name": race['raceName'], "scores": {}}
            
            for n, cfg in PLAYERS_CONFIG.items():
                d_pts = sum([float(r['points']) for r in res if r['Driver']['driverId'] in cfg['drivers']])
                b_pts = 0
                if cfg['constructor'] in top3: b_pts += [3, 2, 1][top3.index(cfg['constructor'])]
                if fl_id in cfg['drivers']: b_pts += 2
                if cfg['constructor'] == winner_t: b_pts += 2
                
                players[n]["driver_pts"] += d_pts
                players[n]["bonus_pts"] += b_pts
                players[n]["total"] += (d_pts + b_pts)
                history[r_num]["scores"][n] = d_pts + b_pts
    return players, history

# --- 5. SIDEBAR COMMAND ---
with st.sidebar:
    st.markdown(f'<h3>PIT WALL COMMAND</h3>', unsafe_allow_html=True)
    sel_year = st.selectbox("Season", [2026, 2025, 2024], index=0)
    
    # THE FIX: Manual Round Override
    st.markdown('<div class="sb-header">⚙️ RACE DIRECTOR OVERRIDE</div>', unsafe_allow_html=True)
    max_r = st.number_input("Force Fetch Rounds (1-24):", min_value=1, max_value=24, value=3)
    st.caption("If Japan isn't showing, set this to 3.")
    
    if st.button("⚡ FORCE SYNC"):
        st.cache_data.clear()
        st.rerun()

    stats, ledger = get_paddock_engine(sel_year, max_r)

    st.markdown('<div class="sb-header">🛰️ NEXT TARGET</div>', unsafe_allow_html=True)
    # Get Calendar for Next Race
    cal = fetch_api(str(sel_year))
    next_r = None
    if cal:
        for r in cal['MRData']['RaceTable']['Races']:
            if datetime.strptime(r['date'], '%Y-%m-%d') >= datetime.now():
                next_r = r; break
    if next_r:
        st.write(f"🚩 **{next_r['raceName'].upper()}**")
        safe_st_image(f"imagesf1maps/{next_r['Circuit']['circuitId']}.png", sidebar=True)

    st.markdown('<div class="sb-header">🔮 THE ORACLE</div>', unsafe_allow_html=True)
    if next_r:
        st.write(f"**Track:** {next_r['Circuit']['Location']['locality']}")
        st.write(f"**Favored:** Richie (Max Verstappen)")

# --- 6. MAIN HUB ---
ticker_text = " | ".join([f"{n.upper()}: {int(p['total'])} PTS" for n, p in stats.items()])
st.markdown(f'<div class="ticker-wrap"><div class="ticker">{ticker_text} | {ticker_text}</div></div>', unsafe_allow_html=True)

st.title("🏎️ F1 FAMILY PADDOCK")
tabs = st.tabs(["🏆 CHAMPIONSHIP", "📜 HISTORY", "🛠️ GARAGE", "🏎️ THE GRID", "📰 NEWS"])

# CHAMPIONSHIP
with tabs[0]:
    st.subheader("Family World Standings")
    df_rows = [{"Player": n, "Drivers": int(p['driver_pts']), "Bonus": int(p['bonus_pts']), "Penalty": PLAYERS_CONFIG[n]['penalty'], "GRAND TOTAL": int(p['total'])} for n, p in stats.items()]
    df = pd.DataFrame(df_rows).sort_values("GRAND TOTAL", ascending=False)
    st.dataframe(df, use_container_width=True, hide_index=True)

# HISTORY
with tabs[1]:
    if ledger:
        h_round = st.selectbox("Select Round:", sorted(ledger.keys(), reverse=True))
        st.markdown(f'<div class="f1-card"><h3>{ledger[h_round]["name"]} Results</h3></div>', unsafe_allow_html=True)
        h_df = pd.DataFrame([{"Player": n, "Weekend Pts": int(pts)} for n, pts in ledger[h_round]["scores"].items()]).sort_values("Weekend Pts", ascending=False)
        st.dataframe(h_df, use_container_width=True, hide_index=True)

# GARAGE & GRID (UNIFORM)
def draw_specs(data_dict):
    for name, cfg in data_dict.items():
        with st.expander(f"⚙️ {name.upper()}"):
            c1, c2, c3 = st.columns([1, 1, 1.3])
            # Use safe loader for driver headshots
            d1_path = f"imagesf1/{cfg['drivers'][0]}.webp"
            d2_path = f"imagesf1/{cfg['drivers'][1]}.webp"
            safe_st_image(d1_path, caption="Driver 1", width=180)
            safe_st_image(d2_path, caption="Driver 2", width=180)
            with c3:
                t_key = cfg.get('constructor', name)
                actual_livery = next((k for k in FULL_GRID_2026 if k.lower().replace("_"," ") == t_key.lower().replace("_"," ")), "Ferrari")
                safe_st_image(f"imagesf1/{actual_livery.lower().replace(' ', '_')}.jpg", caption="2026 Chassis", width=280)

with tabs[2]: draw_specs(PLAYERS_CONFIG)
with tabs[3]: draw_specs(FULL_GRID_2026)

# NEWS
with tabs[4]:
    feed = feedparser.parse("https://www.formula1.com/en/latest/all.xml")
    for e in feed.entries[:8]:
        st.markdown(f'<div class="f1-card"><b>{e.title}</b><br><a href="{e.link}" target="_blank">READ STORY →</a></div>', unsafe_allow_html=True)

st.markdown("<br><center><p style='color:#555;'>POWERED BY ORACLE | RED BULL RACING HUB</p></center>", unsafe_allow_html=True)