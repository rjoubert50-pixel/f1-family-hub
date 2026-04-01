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
RB_GREY = "#1D2A3F"

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

# --- 3. THE CSS (RED BULL STYLE) ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: {RB_NAVY}; color: white; font-family: 'Inter', sans-serif; }}
    [data-testid="stSidebar"] {{ background-color: #041126 !important; border-right: 3px solid {RB_YELLOW}; min-width: 380px !important; }}
    .f1-card {{ background: #0a1a35; border-left: 5px solid {RB_RED}; padding: 15px; border-radius: 10px; margin-bottom: 10px; border-top: 1px solid #1a2a45; }}
    h1, h2, h3 {{ color: {RB_YELLOW} !important; font-family: 'Arial Black'; text-transform: uppercase; letter-spacing: 1px; }}
    .stTabs [aria-selected="true"] {{ background-color: {RB_RED} !important; color: white !important; font-weight: bold; border-radius: 5px; }}
    .ticker-wrap {{ background: #000; border-bottom: 2px solid {RB_YELLOW}; height: 35px; overflow: hidden; position: sticky; top: 0; z-index: 999; }}
    .ticker {{ display: inline-block; animation: ticker 60s linear infinite; white-space: nowrap; line-height: 35px; color: {RB_YELLOW}; font-weight: bold; }}
    @keyframes ticker {{ 0% {{ transform: translateX(0); }} 100% {{ transform: translateX(-100%); }} }}
    .sb-header {{ background: {RB_RED}; color: white; padding: 6px 12px; font-size: 13px; font-weight: bold; border-radius: 3px; margin: 15px 0 5px 0; }}
    .stDataFrame {{ background-color: white; border-radius: 8px; }}
    </style>
""", unsafe_allow_html=True)

# --- 4. DATA ENGINE ---
BASE_URL = "https://api.jolpi.ca/ergast/f1"

@st.cache_data(ttl=300)
def fetch_api(endpoint):
    try:
        r = requests.get(f"{BASE_URL}/{endpoint}.json", timeout=15)
        return r.json() if r.status_code == 200 else None
    except: return None

@st.cache_data(ttl=300)
def get_paddock_engine(year):
    """Deep Scanner: Loops through every round to force-update Japan R3."""
    players = {n: {"driver_pts": 0, "bonus_pts": 0, "total": cfg['penalty']} for n, cfg in PLAYERS_CONFIG.items()}
    history = {} 

    # 1. Fetch Constructor Standings (for the +2 Standing Leader Bonus)
    c_standings_data = fetch_api(f"{year}/constructorStandings")
    leader_team = ""
    try:
        leader_team = c_standings_data['MRData']['StandingsTable']['StandingsLists'][0]['ConstructorStandings'][0]['Constructor']['constructorId']
    except: pass

    # 2. Fetch all race results (Aggressive Scan)
    r_data = fetch_api(f"{year}/results?limit=500")
    if r_data and r_data['MRData']['RaceTable']['Races']:
        for race in r_data['MRData']['RaceTable']['Races']:
            r_num = int(race['round'])
            res = race['Results']
            fl_id = next((r['Driver']['driverId'] for r in res if r.get('FastestLap', {}).get('rank') == "1"), "")
            
            t_wknd = {}
            for r in res:
                c_id = r['Constructor']['constructorId']
                t_wknd[c_id] = t_wknd.get(c_id, 0) + float(r['points'])
            
            ranked_t = sorted(t_wknd.items(), key=lambda x: x[1], reverse=True)
            top3_wknd = [t[0] for t in ranked_t[:3]]
            winner_wknd = ranked_t[0][0] if ranked_t else ""

            history[r_num] = {"race_name": race['raceName'], "scores": {n: 0 for n in PLAYERS_CONFIG.keys()}}
            
            for n, cfg in PLAYERS_CONFIG.items():
                d_pts = sum([float(r['points']) for r in res if r['Driver']['driverId'] in cfg['drivers']])
                b_pts = 0
                # Rule: Constructor Podium (3/2/1)
                if cfg['constructor'] in top3_wknd:
                    b_pts += [3, 2, 1][top3_wknd.index(cfg['constructor'])]
                # Rule: Fastest Lap (+2)
                if fl_id in cfg['drivers']: b_pts += 2
                # Rule: Weekend Team Winner (+2)
                if cfg['constructor'] == winner_wknd: b_pts += 2
                # Rule: Championship Standing Leader (+2) - Checked after latest available round
                if cfg['constructor'] == leader_team and r_num == len(r_data['MRData']['RaceTable']['Races']):
                    b_pts += 2

                players[n]["driver_pts"] += d_pts
                players[n]["bonus_pts"] += b_pts
                players[n]["total"] += (d_pts + b_pts)
                history[r_num]["scores"][n] = d_pts + b_pts
                
    return players, history

# --- 5. SIDEBAR cockpit ---
with st.sidebar:
    st.markdown(f'<h3><span class="status-light"></span> PADDOCK COMMAND</h3>', unsafe_allow_html=True)
    sel_year = st.selectbox("Season", [2026, 2025, 2024], index=0)
    
    if st.button("🔄 FORCE SYNC DATA"):
        st.cache_data.clear()
        st.rerun()

    stats, ledger = get_paddock_engine(sel_year)
    
    st.markdown('<div class="sb-header">🛰️ NEXT MISSION</div>', unsafe_allow_html=True)
    cal = fetch_api(str(sel_year))
    next_r = None
    if cal:
        r_list = cal['MRData']['RaceTable']['Races']
        for r in r_list:
            if datetime.strptime(r['date'], '%Y-%m-%d') >= datetime.now():
                next_r = r; break
    
    if next_r:
        st.write(f"🚩 **{next_r['raceName'].upper()}**")
        diff = datetime.strptime(next_r['date'], '%Y-%m-%d') - datetime.now()
        st.write(f"⏱️ T-Minus: **{diff.days} Days**")
        safe_st_image(f"imagesf1maps/{next_r['Circuit']['circuitId']}.png", sidebar=True)

    st.markdown('<div class="sb-header">🏆 PADDOCK LEADER</div>', unsafe_allow_html=True)
    if stats:
        lead_p = max(stats, key=lambda x: stats[x]['total'])
        st.write(f"🥇 **{lead_p.upper()}** ({int(stats[lead_p]['total'])} pts)")
        safe_st_image(f"imagesf1/{PLAYERS_CONFIG[lead_p]['drivers'][0]}.webp", sidebar=True)

    st.markdown('<div class="sb-header">🔮 THE ORACLE</div>', unsafe_allow_html=True)
    if next_r:
        circuit = next_r['Circuit']['circuitId']
        # Crazy Logic: Advantages/Problems
        adv = "Straight-line Speed" if any(x in circuit for x in ['monza', 'vegas', 'spa']) else "High Downforce"
        prob = "Tire Degradation" if "bahrain" in circuit or "suzuka" in circuit else "Brake Overheating"
        
        st.write(f"**Track Type:** {adv}")
        st.write(f"**Risk Factor:** {prob}")
        st.write(f"**Richie's Max:** 88% chance")
        st.write(f"**Yoshi's Lando:** 74% chance")

# --- 6. TICKER ---
d_standings = fetch_api(f"{sel_year}/driverStandings")
try:
    s_list = d_standings['MRData']['StandingsTable']['StandingsLists'][0]['DriverStandings']
    ticker_text = "  |  ".join([f"{i['position']}. {i['Driver']['familyName'].upper()} ({i['points']} PTS)" for i in s_list])
except: ticker_text = f"UPCOMING: {next_r['raceName'].upper()} - {next_r['date']}"
st.markdown(f'<div class="ticker-wrap"><div class="ticker">{ticker_text} | {ticker_text}</div></div>', unsafe_allow_html=True)

# --- 7. MAIN HUB ---
st.title("🏁 F1 FAMILY PADDOCK")
tabs = st.tabs(["🏆 CHAMPIONSHIP", "📜 HISTORY", "🛠️ GARAGE", "🏎️ THE GRID", "📰 NEWS"])

# CHAMPIONSHIP
with tabs[0]:
    st.subheader("Leaderboard")
    df_rows = [{"Player": n, "Drivers": int(p['driver_pts']), "Bonus": int(p['bonus_pts']), "Penalty": PLAYERS_CONFIG[n]['penalty'], "GRAND TOTAL": int(p['total'])} for n, p in stats.items()]
    df = pd.DataFrame(df_rows).sort_values("GRAND TOTAL", ascending=False)
    st.dataframe(df, use_container_width=True, hide_index=True, column_config={
        "GRAND TOTAL": st.column_config.NumberColumn("TOTAL 🏆", format="%d")
    })

# HISTORY
with tabs[1]:
    if ledger:
        h_round = st.selectbox("Select Round to Review:", sorted(ledger.keys(), reverse=True))
        st.markdown(f'<div class="f1-card"><h3>{ledger[h_round]["race_name"]} Breakdown</h3></div>', unsafe_allow_html=True)
        h_df = pd.DataFrame([{"Player": n, "Points Gained": int(pts)} for n, pts in ledger[h_round]["scores"].items()]).sort_values("Points Gained", ascending=False)
        st.dataframe(h_df, use_container_width=True, hide_index=True)
    else: st.info("History data will populate after the first sync.")

# UNIFORM GARAGE & GRID
def draw_specs(data_dict):
    for name, cfg in data_dict.items():
        with st.expander(f"⚙️ {name.upper()}"):
            c1, c2, c3 = st.columns([1, 1, 1.3])
            with c1: safe_st_image(f"imagesf1/{cfg['drivers'][0]}.webp", caption="Driver 1", width=180)
            with c2: safe_st_image(f"imagesf1/{cfg['drivers'][1]}.webp", caption="Driver 2", width=180)
            with c3:
                t_key = cfg.get('constructor', name)
                # Find the livery name
                actual_livery = next((k for k in FULL_GRID_2026 if k.lower().replace("_"," ") == t_key.lower().replace("_"," ")), "Ferrari")
                safe_st_image(f"imagesf1/{actual_livery.lower().replace(' ', '_')}.jpg", caption="2026 Challenger", width=280)

with tabs[2]: draw_specs(PLAYERS_CONFIG)
with tabs[3]: draw_specs(FULL_GRID_2026)

# NEWS SLIDER (LIST VIEW)
with tabs[4]:
    feed = feedparser.parse("https://www.formula1.com/en/latest/all.xml")
    if feed.entries:
        for e in feed.entries[:10]:
            st.markdown(f'<div class="f1-card"><b>{e.title}</b><br><a href="{e.link}" target="_blank" style="color:{RB_YELLOW}; text-decoration:none;">READ MORE →</a></div>', unsafe_allow_html=True)

st.markdown("<br><center><p style='color:#555;'>ORACLE CLOUD INFRASTRUCTURE | RED BULL RACING HUB</p></center>", unsafe_allow_html=True)