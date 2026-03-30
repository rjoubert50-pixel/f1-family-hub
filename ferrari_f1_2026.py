import streamlit as st
import pandas as pd
import requests
import os
import feedparser
import plotly.express as px
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# --- 1. CONFIGURATION & ASSETS ---
st.set_page_config(page_title="F1 Family Hub 2026", layout="wide", page_icon="🏎️")
st_autorefresh(interval=60000, key="f1_refresh")

# --- UNIVERSAL SAFE IMAGE DISPLAY FUNCTION ---
def safe_st_image(img_path, caption="", width=None, sidebar=False):
    """Prevents the app from crashing if an image file is missing or corrupted."""
    target = st.sidebar if sidebar else st
    try:
        if img_path and (os.path.exists(img_path) or img_path.startswith("http")):
            target.image(img_path, caption=caption, width=width, use_container_width=(width is None))
        else:
            target.caption(f"Missing: {caption}")
    except Exception:
        target.caption(f"Error loading {caption}")

def get_img(local_path, web_fallback="https://media.formula1.com/content/dam/fom-website/2018-redesign-assets/team-car-photos-16x9/2024/mclaren.png"):
    if os.path.exists(local_path): return local_path
    return web_fallback

# Driver Images
DRIVER_IMAGES = {
    "norris": get_img("imagesf1/norris.webp"),
    "piastri": get_img("imagesf1/piastri.webp"),
    "max_verstappen": get_img("imagesf1/max_verstappen.webp"),
    "hadjar": get_img("imagesf1/hadjar.webp"),
    "leclerc": get_img("imagesf1/leclerc.webp"),
    "hamilton": get_img("imagesf1/hamilton.webp"),
    "russell": get_img("imagesf1/russell.webp"),
    "antonelli": get_img("imagesf1/antonelli.webp"),
    "sainz": get_img("imagesf1/sainz.webp"),
    "albon": get_img("imagesf1/albon.webp"),
    "alonso": get_img("imagesf1/alonso.webp"),
    "stroll": get_img("imagesf1/stroll.webp"),
    "gasly": get_img("imagesf1/gasly.webp"),
    "colapinto": get_img("imagesf1/colapinto.webp"),
    "hulkenberg": get_img("imagesf1/hulkenberg.webp"),
    "bortoleto": get_img("imagesf1/bortoleto.webp"),
    "ocon": get_img("imagesf1/ocon.webp"),
    "bearman": get_img("imagesf1/bearman.webp"),
    "lawson": get_img("imagesf1/lawson.webp"),
    "lindblad": get_img("imagesf1/lindblad.webp"),
    "perez": get_img("imagesf1/perez.webp"),
    "bottas": get_img("imagesf1/bottas.webp"),
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

# --- 2. THE CSS ---
st.markdown("""
    <style>
    .stApp { background: linear-gradient(180deg, #000000 0%, #1a1a1a 100%); color: #ffffff; }
    [data-testid="stSidebar"] { background-color: #121212 !important; border-right: 2px solid #e10600; min-width: 350px !important; }
    .f1-card { background-color: #1a1a1a; border-left: 5px solid #e10600; padding: 15px; border-radius: 8px; margin-bottom: 10px; }
    .status-light { height: 10px; width: 10px; background-color: #00ff00; border-radius: 50%; display: inline-block; box-shadow: 0 0 8px #00ff00; animation: blink 2s infinite; margin-right: 10px; }
    @keyframes blink { 0% { opacity: 1; } 50% { opacity: 0.3; } 100% { opacity: 1; } }
    .ticker-wrap { width: 100%; overflow: hidden; height: 35px; background-color: #121212; border-bottom: 2px solid #e10600; }
    .ticker { display: inline-block; animation: ticker 60s linear infinite; white-space: nowrap; line-height:35px; color: #e10600; font-weight: bold; }
    @keyframes ticker { 0% { transform: translateX(0); } 100% { transform: translateX(-100%); } }
    .sb-header { background: #e10600; color: white; padding: 6px 12px; font-size: 13px; font-weight: bold; border-radius: 3px; margin: 18px 0 8px 0; }
    </style>
""", unsafe_allow_html=True)

# --- 3. DATA ENGINE ---
BASE_URL = "https://api.jolpi.ca/ergast/f1"

@st.cache_data(ttl=600)
def fetch_api(endpoint):
    try:
        r = requests.get(f"{BASE_URL}/{endpoint}.json", timeout=10)
        return r.json() if r.status_code == 200 else None
    except: return None

@st.cache_data(ttl=3600)
def fetch_paddock_news():
    try:
        feed = feedparser.parse("https://www.formula1.com/en/latest/all.xml")
        return [{"title": e.title, "link": e.link, "published": getattr(e, 'published', 'Recent')} for e in feed.entries[:10]]
    except: return []

@st.cache_data(ttl=600)
def get_season_master_data(year):
    players = {name: {"driver_pts": 0, "bonus_pts": 0, "total": cfg['penalty']} for name, cfg in PLAYERS_CONFIG.items()}
    history = {}
    r_data = fetch_api(f"{year}/results")
    if r_data and r_data['MRData']['RaceTable']['Races']:
        for race in r_data['MRData']['RaceTable']['Races']:
            r_num = int(race['round'])
            res = race['Results']
            fl_id = next((r['Driver']['driverId'] for r in res if r.get('FastestLap', {}).get('rank') == "1"), "")
            t_wknd = {}
            for r in res:
                c_id = r['Constructor']['constructorId']
                t_wknd[c_id] = t_wknd.get(c_id, 0) + float(r['points'])
            ranked = sorted(t_wknd.items(), key=lambda x: x[1], reverse=True)
            top3 = [t[0] for t in ranked[:3]]
            winner_team = ranked[0][0] if ranked else ""
            history[r_num] = {n: 0 for n in PLAYERS_CONFIG.keys()}
            for n, cfg in PLAYERS_CONFIG.items():
                d_pts = sum([float(r['points']) for r in res if r['Driver']['driverId'] in cfg['drivers']])
                b_pts = ([3,2,1][top3.index(cfg['constructor'])] if cfg['constructor'] in top3 else 0)
                if fl_id in cfg['drivers']: b_pts += 2
                if cfg['constructor'] == winner_team: b_pts += 2
                players[n]["driver_pts"] += d_pts
                players[n]["bonus_pts"] += b_pts
                players[n]["total"] += (d_pts + b_pts)
                history[r_num][n] = d_pts + b_pts
    return players, history

# --- 4. SIDEBAR ---
with st.sidebar:
    st.markdown('<h3><span class="status-light"></span> PIT WALL LIVE</h3>', unsafe_allow_html=True)
    selected_year = st.selectbox("Season", [2026, 2025, 2024], index=0)
    stats, history_ledger = get_season_master_data(selected_year)
    
    st.markdown('<div class="sb-header">🛰️ NEXT MISSION</div>', unsafe_allow_html=True)
    cal = fetch_api(str(selected_year))
    next_r = None
    if cal:
        for r in cal['MRData']['RaceTable']['Races']:
            if datetime.strptime(r['date'], '%Y-%m-%d') >= datetime.now():
                next_r = r
                break
    if next_r:
        st.write(f"🚩 **{next_r['raceName']}**")
        diff = datetime.strptime(next_r['date'], '%Y-%m-%d') - datetime.now()
        st.write(f"⏱️ Countdown: **{diff.days} Days**")

    st.markdown('<div class="sb-header">🏆 SEASON TITAN</div>', unsafe_allow_html=True)
    if stats:
        lead_p = max(stats, key=lambda x: stats[x]['total'])
        st.write(f"🥇 **{lead_p.upper()}** ({int(stats[lead_p]['total'])} pts)")
        safe_st_image(DRIVER_IMAGES.get(PLAYERS_CONFIG[lead_p]['drivers'][0]), caption="Leading Driver", sidebar=True)

# --- 5. MAIN HUB ---
ticker_str = " | ".join([f"{n.upper()}: {int(p['total'])} PTS" for n, p in stats.items()]) if stats else "Awaiting Data..."
st.markdown(f'<div class="ticker-wrap"><div class="ticker">{ticker_str} | {ticker_str}</div></div>', unsafe_allow_html=True)

st.title("🏁 SCUDERIA FAMILY HUB")
tabs = st.tabs(["🏆 CHAMPIONSHIP", "📜 HISTORY", "🛠️ GARAGE", "🏎️ THE GRID", "📰 NEWS"])

with tabs[0]:
    c1, c2 = st.columns([1.5, 1])
    with c1:
        st.subheader("Leaderboard")
        df_rows = [{"Player": n, "Drivers": int(p['driver_pts']), "Bonus": int(p['bonus_pts']), "Penalty": PLAYERS_CONFIG[n]['penalty'], "TOTAL": int(p['total'])} for n, p in stats.items()]
        df = pd.DataFrame(df_rows).sort_values("TOTAL", ascending=False)
        st.dataframe(df, use_container_width=True, hide_index=True, column_config={"TOTAL": st.column_config.NumberColumn("TOTAL", format="%d")})
    with c2:
        st.subheader("Progression")
        if history_ledger:
            chart_rows = []
            for n in PLAYERS_CONFIG.keys():
                cur = PLAYERS_CONFIG[n]['penalty']
                for r in sorted(history_ledger.keys()):
                    cur += history_ledger[r][n]
                    chart_rows.append({"Round": f"R{r}", "Player": n, "Points": cur})
            st.plotly_chart(px.line(pd.DataFrame(chart_rows), x="Round", y="Points", color="Player", template="plotly_dark"), use_container_width=True)

with tabs[1]:
    if history_ledger:
        h_round = st.selectbox("Select Race:", sorted(history_ledger.keys(), reverse=True))
        h_res = fetch_api(f"{selected_year}/{h_round}/results")
        if h_res:
            race_m = h_res['MRData']['RaceTable']['Races'][0]
            st.markdown(f'<div class="f1-card"><h3>{race_m["raceName"]} Breakdown</h3></div>', unsafe_allow_html=True)
            st.table(pd.DataFrame([{"Player": n, "Weekend Pts": int(p)} for n, p in history_ledger[h_round].items()]).sort_values("Weekend Pts", ascending=False))

# --- SAFE SPEC VIEW FUNCTION ---
def draw_spec_view(data, title, is_grid=False):
    st.subheader(title)
    for name, cfg in data.items():
        with st.expander(f"⚙️ {name.upper()}"):
            col1, col2, col3 = st.columns([1, 1, 1.2])
            with col1: safe_st_image(DRIVER_IMAGES.get(cfg['drivers'][0], ""), caption="Driver 1", width=180)
            with col2: safe_st_image(DRIVER_IMAGES.get(cfg['drivers'][1], ""), caption="Driver 2", width=180)
            with col3:
                # Find the team key by comparing constructor names
                t_id = cfg.get('constructor', name)
                t_key = next((k for k in FULL_GRID_2026 if k.lower().replace("_"," ") == t_id.lower().replace("_"," ")), "Ferrari")
                safe_st_image(FULL_GRID_2026[t_key]['car'], caption="Challenger", width=280)

with tabs[2]: draw_spec_view(PLAYERS_CONFIG, "Garage Bays")
with tabs[3]: draw_spec_view(FULL_GRID_2026, "Official 2026 Entry List", is_grid=True)

with tabs[4]:
    news = fetch_paddock_news()
    for n in news:
        st.markdown(f'<div class="f1-card"><b>{n["title"]}</b><br><a href="{n["link"]}" target="_blank">Story →</a></div>', unsafe_allow_html=True)

st.markdown("<br><center><p style='color:#555;'>ENGINE BY MARANELLO | 2026</p></center>", unsafe_allow_html=True)