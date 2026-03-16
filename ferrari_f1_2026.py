import streamlit as st
import pandas as pd
import requests
import os
import feedparser
import plotly.express as px # Added for the cool interactive chart
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# --- 1. SETUP & CONFIG ---
st.set_page_config(page_title="F1 Family Hub", layout="wide", page_icon="🏎️")
st_autorefresh(interval=60000, key="f1_refresh")

def safe_st_image(img_path, caption="", width=None, sidebar=False):
    target = st.sidebar if sidebar else st
    try:
        if img_path:
            target.image(img_path, caption=caption, width=width, use_container_width=(width is None))
    except: pass

def get_img(local_path, web_fallback):
    if os.path.exists(local_path): return local_path
    return web_fallback

# Driver Images
DRIVER_IMAGES = {
    "norris": "imagesf1/norris.jpg", "piastri": "imagesf1/piastri.jpg",
    "max_verstappen": "imagesf1/max_verstappen.jpg", "hadjar": "imagesf1/hadjar.jpg",
    "leclerc": "imagesf1/leclerc.jpg", "hamilton": "imagesf1/hamilton.jpg",
    "russell": "imagesf1/russell.jpg", "antonelli": "imagesf1/antonelli.jpg",
    "sainz": "imagesf1/sainz.jpg", "albon": "imagesf1/albon.jpg",
    "alonso": "imagesf1/alonso.jpg", "stroll": "imagesf1/stroll.jpg",
    "gasly": "imagesf1/gastly.jpg", "colapinto": "imagesf1/colapinto.jpg",
    "hulkenberg": "imagesf1/hulkenberg.jpg", "bortoleto": "imagesf1/bortoleto.jpg",
    "ocon": "imagesf1/ocon.jpg", "bearman": "imagesf1/bearman.jpg",
    "lawson": "imagesf1/lawson.jpg", "lindblad": "imagesf1/lindblad.jpg",
    "perez": "imagesf1/perez.jpg", "bottas": "imagesf1/bottas.jpg",
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
    "Racing_Bulls": {"drivers": ["lawson", "lindblad"], "car": "imagesf1/racing_bulls.jpg"},
    "Cadillac": {"drivers": ["perez", "bottas"], "car": "imagesf1/cadillac.jpg"},
}

# --- 2. DATA ENGINE ---
BASE_URL = "https://api.jolpi.ca/ergast/f1"

@st.cache_data(ttl=60)
def fetch_api(endpoint):
    try:
        r = requests.get(f"{BASE_URL}/{endpoint}.json", timeout=10)
        return r.json() if r.status_code == 200 else None
    except: return None

@st.cache_data(ttl=60)
def get_full_season_data(year):
    """Deep processing: Returns points per player per round for charts and history."""
    r_data = fetch_api(f"{year}/results")
    history_ledger = {} # {round_num: {player_name: round_total}}
    
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
            
            history_ledger[r_num] = {}
            for name, cfg in PLAYERS_CONFIG.items():
                # 1. Driver Points
                d_pts = sum([float(r['points']) for r in res if r['Driver']['driverId'] in cfg['drivers']])
                # 2. Bonus 3/2/1
                b_pts = ([3,2,1][top3.index(cfg['constructor'])] if cfg['constructor'] in top3 else 0)
                # 3. Fastest Lap (+2)
                if fl_id in cfg['drivers']: b_pts += 2
                # 4. Weekend Winner (+2)
                if cfg['constructor'] == winner_team: b_pts += 2
                
                history_ledger[r_num][name] = d_pts + b_pts
                
    return history_ledger

# --- 3. THE CSS ---
st.markdown("""
    <style>
    .stApp { background: linear-gradient(180deg, #000000 0%, #1a1a1a 100%); color: #ffffff; }
    [data-testid="stSidebar"] { background-color: #808080 !important; border-right: 2px solid #333; }
    .f1-card { background-color: #121212; border: 1px solid #333; border-top: 4px solid #e10600; padding: 15px; border-radius: 12px; margin-bottom: 10px; }
    .sb-header { background: #e10600; padding: 5px 10px; border-radius: 4px; font-size: 14px; margin-top: 20px; }
    .ticker-wrap { width: 100%; overflow: hidden; height: 35px; background-color: #121212; border-bottom: 2px solid #e10600; }
    .ticker { display: inline-block; animation: ticker 60s linear infinite; white-space: nowrap; line-height:35px; }
    @keyframes ticker { 0% { transform: translateX(0); } 100% { transform: translateX(-100%); } }
    </style>
""", unsafe_allow_html=True)

# --- 4. UI LOGIC ---
selected_year = st.sidebar.selectbox("Active Year", [2026, 2025, 2024], index=0)
cal_data = fetch_api(str(selected_year))
ledger = get_full_season_data(selected_year)

# Calculations for Standings
total_scores = {name: cfg['penalty'] for name, cfg in PLAYERS_CONFIG.items()}
for r_num, players in ledger.items():
    for name, pts in players.items():
        total_scores[name] += pts

# Ticker Fallback
ticker_str = f"NEXT RACE: MELBOURNE GP - MARCH 8th"
d_standings = fetch_api(f"{selected_year}/driverStandings")
try:
    s_list = d_standings['MRData']['StandingsTable']['StandingsLists'][0]['DriverStandings']
    if s_list: ticker_str = "  |  ".join([f"{i['position']}. {i['Driver']['familyName'].upper()} ({i['points']} PTS)" for i in s_list])
except: pass
st.markdown(f'<div class="ticker-wrap"><div class="ticker">{ticker_str} | {ticker_str}</div></div>', unsafe_allow_html=True)

# --- 5. SIDEBAR ---
with st.sidebar:
    st.markdown('<div class="sb-header">CHAMPIONSHIP LEADER</div>', unsafe_allow_html=True)
    if total_scores:
        lead_player = max(total_scores, key=total_scores.get)
        st.write(f"👑 {lead_player.upper()}")
        safe_st_image(DRIVER_IMAGES.get(PLAYERS_CONFIG[lead_player]['drivers'][0]), sidebar=True)

# --- 6. MAIN TABS ---
st.title("🏎️ F1 FAMILY HUB")
t_board, t_history, t_garage, t_cal, t_grid = st.tabs(["🏆 CHAMPIONSHIP", "📜 HISTORY", "🛠️ GARAGES", "📅 CALENDAR", "🏎️ THE GRID"])

# --- TAB: CHAMPIONSHIP (Interactive) ---
with t_board:
    st.header("World Rankings & Progression")
    
    # Season Progress Line Chart
    if ledger:
        chart_data = []
        for name in PLAYERS_CONFIG.keys():
            running_total = PLAYERS_CONFIG[name]['penalty']
            for r_num in sorted(ledger.keys()):
                running_total += ledger[r_num][name]
                chart_data.append({"Round": f"R{r_num}", "Player": name, "Points": running_total})
        
        df_chart = pd.DataFrame(chart_data)
        fig = px.line(df_chart, x="Round", y="Points", color="Player", markers=True, template="plotly_dark", color_discrete_sequence=px.colors.qualitative.Pastel)
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)

    # Standings Table
    rows = [{"Player": n, "Total": int(v)} for n, v in total_scores.items()]
    df_standings = pd.DataFrame(rows).sort_values("Total", ascending=False)
    st.dataframe(df_standings, use_container_width=True, hide_index=True, column_config={"Total": st.column_config.ProgressColumn("GRAND TOTAL 🏆", format="%d", min_value=-30, max_value=500)})

# --- TAB: HISTORY (New!) ---
with t_history:
    if ledger:
        r_list = [f"Round {r}" for r in sorted(ledger.keys(), reverse=True)]
        h_choice = st.selectbox("Select a Past Race Result:", r_list)
        h_round = int(h_choice.split(" ")[1])
        
        # Pull official results for this specific round
        h_results = fetch_api(f"{selected_year}/{h_round}/results")
        if h_results:
            race = h_results['MRData']['RaceTable']['Races'][0]
            st.subheader(f"🏁 {race['raceName']} Dashboard")
            
            c1, c2, c3 = st.columns(3)
            with c1:
                winner = race['Results'][0]
                st.metric("OFFICIAL WINNER", winner['Driver']['familyName'])
                safe_st_image(DRIVER_IMAGES.get(winner['Driver']['driverId']), width=150)
            with c2:
                fl = next(r for r in race['Results'] if r.get('FastestLap', {}).get('rank') == "1")
                st.metric("FASTEST LAP", fl['Driver']['familyName'], f"{fl['FastestLap']['Time']['time']}")
            with c3:
                st.metric("PODIUM TEAM", winner['Constructor']['name'])
            
            st.divider()
            st.subheader("Family Points Looted This Weekend")
            h_rows = [{"Player": n, "Points Gained": int(pts)} for n, pts in ledger[h_round].items()]
            st.table(pd.DataFrame(h_rows).sort_values("Points Gained", ascending=False))
    else:
        st.info("Season history will appear here once the first race data is synced!")

# --- GARAGE, CALENDAR, GRID (Preserved Logic) ---
with t_garage:
    for player, cfg in PLAYERS_CONFIG.items():
        with st.expander(f"🛠️ GARAGE: {player.upper()}"):
            col_d1, col_d2, col_chassis = st.columns([1, 1, 1.2])
            with col_d1: safe_st_image(DRIVER_IMAGES.get(cfg['drivers'][0]), caption=f"D1: {cfg['drivers'][0].upper()}", width=180)
            with col_d2: safe_st_image(DRIVER_IMAGES.get(cfg['drivers'][1]), caption=f"D2: {cfg['drivers'][1].upper()}", width=180)
            with col_chassis:
                team_key = next((k for k in FULL_GRID_2026 if k.lower().replace("_"," ") == cfg['constructor'].lower().replace("_"," ")), None)
                if team_key: safe_st_image(get_img(FULL_GRID_2026[team_key]['car'], ""), width=280)

with t_cal:
    if cal_data:
        r_list = [f"R{r['round']}: {r['raceName']}" for r in cal_data['MRData']['RaceTable']['Races']]
        sel = st.selectbox("Explore Calendar", r_list)
        # Logic same as before... (omitted for brevity but kept in your Notepad)

with t_grid:
    for team, data in FULL_GRID_2026.items():
        with st.expander(f"🏎️ {team.upper()} ENTRY"):
            col_d1, col_d2, col_car = st.columns([1, 1, 1.2])
            with col_d1: safe_st_image(DRIVER_IMAGES.get(data['drivers'][0], ""), width=180)
            with col_d2: safe_st_image(DRIVER_IMAGES.get(data['drivers'][1], ""), width=180)
            with col_car: safe_st_image(get_img(data['car'], ""), width=280)

st.markdown("<br><center><p style='color:#555;'>ENGINE BY MARANELLO | 2026</p></center>", unsafe_allow_html=True)