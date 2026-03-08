import streamlit as st
import pandas as pd
import requests
import os
import feedparser
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# --- 1. ASSETS & CONFIG ---
st.set_page_config(page_title="F1 Family Hub", layout="wide", page_icon="🏎️")
st_autorefresh(interval=60000, key="f1_refresh")

def safe_st_image(img_path, caption="", width=None, sidebar=False):
    target = st.sidebar if sidebar else st
    try:
        if img_path:
            target.image(img_path, caption=caption, width=width, use_container_width=(width is None))
        else:
            target.warning("🖼️ Image Missing")
    except Exception:
        target.error("⚠️ Image Load Fail")

def get_img(local_path, web_fallback):
    if os.path.exists(local_path): return local_path
    return web_fallback

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

TEAM_LOGOS = {
    "mclaren": "imagesf1/mclaren.jpg", "red_bull": "imagesf1/red_bull.jpg",
    "ferrari": "imagesf1/ferrari.jpg", "mercedes": "imagesf1/mercedes.jpg",
    "aston_martin": "imagesf1/aston_martin.jpg", "williams": "imagesf1/williams.jpg",
    "alpine": "imagesf1/alpine.jpg", "audi": "imagesf1/audi.jpg",
    "haas": "imagesf1/haas.jpg", "racing_bulls": "imagesf1/vcarb.jpg",
    "cadillac": "imagesf1/cadillac.jpg"
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

# --- 2. CSS ---
st.markdown("""
    <style>
    .stApp { background: linear-gradient(180deg, #000000 0%, #1a1a1a 100%); color: #ffffff; }
    [data-testid="stSidebar"] { background-color: #808080 !important; border-right: 2px solid #333; }
    [data-testid="stSidebar"] * { color: white !important; font-weight: bold; }
    .sb-header { background: #e10600; padding: 5px 10px; border-radius: 4px; font-size: 14px; margin-top: 20px; margin-bottom: 10px; }
    .ticker-wrap { width: 100%; overflow: hidden; height: 35px; background-color: #121212; border-bottom: 2px solid #e10600; }
    .ticker { display: inline-block; animation: ticker 60s linear infinite; white-space: nowrap; line-height:35px; }
    .ticker-item { display: inline-block; padding: 0 30px; font-weight: bold; color: white; font-size: 14px; text-transform: uppercase; }
    @keyframes ticker { 0% { transform: translateX(0); } 100% { transform: translateX(-100%); } }
    .f1-card { background-color: #121212; border: 1px solid #333; border-top: 4px solid #e10600; padding: 15px; border-radius: 12px; }
    </style>
""", unsafe_allow_html=True)

# --- 3. DATA ENGINE ---
BASE_URL = "https://api.jolpi.ca/ergast/f1"

@st.cache_data(ttl=60)
def fetch_api(endpoint):
    try:
        r = requests.get(f"{BASE_URL}/{endpoint}.json", timeout=10)
        return r.json() if r.status_code == 200 else None
    except: return None

@st.cache_data(ttl=3600)
def get_weather(lat, lon):
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&daily=precipitation_probability_max&timezone=auto"
        res = requests.get(url).json()
        return {"temp": res['current_weather']['temperature'], "code": res['current_weather']['weathercode'], "rain": res['daily']['precipitation_probability_max'][0]}
    except: return None

def weather_icon(code):
    if code == 0: return "☀️ Clear"
    if code in [1, 2, 3]: return "🌤️ Partly Cloudy"
    if code in [51, 53, 55, 61, 63, 65]: return "🌧️ Rain"
    if code in [95, 96, 99]: return "⛈️ Thunderstorm"
    return "☁️ Overcast"

@st.cache_data(ttl=3600)
def fetch_paddock_news():
    try:
        feed = feedparser.parse("https://www.formula1.com/en/latest/all.xml")
        return [{"title": e.title, "link": e.link, "published": getattr(e, 'published', 'Recent'), "summary": getattr(e, 'summary', '')} for e in feed.entries[:10]]
    except: return []

# --- 4. CALCULATIONS & UPDATED POINTS ALGORITHM ---
@st.cache_data(ttl=60)
def calculate_season_breakdown(year):
    # Initialize Andy and the rest
    players = {name: {"driver_pts": 0, "bonus_pts": 0, "penalty": cfg['penalty']} for name, cfg in PLAYERS_CONFIG.items()}
    
    r_data = fetch_api(f"{year}/results")
    if r_data:
        try:
            for race in r_data['MRData']['RaceTable']['Races']:
                res = race['Results']
                
                # Rule 2: Find Fastest Lap Driver
                fl_id = next((r['Driver']['driverId'] for r in res if r.get('FastestLap', {}).get('rank') == "1"), "")
                
                # Rule 1 & 3: Calculate Weekend Constructor Performance
                t_wknd = {}
                for r in res:
                    c_id = r['Constructor']['constructorId']
                    # Normalize for naming inconsistencies (e.g., 'rb' vs 'racing_bulls')
                    if c_id == 'rb': c_id = 'racing_bulls'
                    
                    t_wknd[c_id] = t_wknd.get(c_id, 0) + float(r['points'])
                    
                    # Track Driver Points for Players
                    for name, cfg in PLAYERS_CONFIG.items():
                        if r['Driver']['driverId'] in cfg['drivers']:
                            players[name]["driver_pts"] += float(r['points'])
                
                # Rank constructors based on weekend points
                ranked_constructors = sorted(t_wknd.items(), key=lambda x: x[1], reverse=True)
                top3_constructors = [t[0] for t in ranked_constructors[:3]]
                winner_constructor = ranked_constructors[0][0] if ranked_constructors else ""

                for name, cfg in PLAYERS_CONFIG.items():
                    p_cons = cfg['constructor'].lower()
                    
                    # 1. Constructor finish points (3, 2, 1)
                    if p_cons in top3_constructors:
                        rank = top3_constructors.index(p_cons)
                        players[name]["bonus_pts"] += [3, 2, 1][rank]
                    
                    # 2. Fastest Lap (+2)
                    if fl_id in cfg['drivers']:
                        players[name]["bonus_pts"] += 2
                    
                    # 3. Leading Weekend Constructor (+2)
                    if p_cons == winner_constructor:
                        players[name]["bonus_pts"] += 2
        except: pass
    return players

def calculate_oracle_probabilities(next_race, year):
    circuit_id = next_race['Circuit']['circuitId']
    h_data = fetch_api(f"{year-1}/circuits/{circuit_id}/results")
    h_pts = {}
    if h_data:
        try: h_pts = {r['Driver']['driverId']: float(r['points']) for r in h_data['MRData']['RaceTable']['Races'][0]['Results']}
        except: pass
    
    probs, key_drivers = {}, {}
    for p, cfg in PLAYERS_CONFIG.items():
        d1, d2 = cfg['drivers']
        s1 = (h_pts.get(d1, 0) * 2) + 5
        s2 = (h_pts.get(d2, 0) * 2) + 5
        key_drivers[p] = d1 if s1 >= s2 else d2
        probs[p] = s1 + s2
    total = sum(probs.values())
    return sorted([{"player": p, "prob": (v/total)*100, "key": key_drivers[p].replace('_', ' ').title()} for p, v in probs.items()], key=lambda x: x['prob'], reverse=True)

def get_next_race_info(year):
    data = fetch_api(f"{year}")
    if not data: return None, 0
    races = data['MRData']['RaceTable']['Races']
    now = datetime.now()
    for i, r in enumerate(races):
        if datetime.strptime(r['date'], '%Y-%m-%d') >= now: return r, i
    return races[-1], len(races)-1

# --- 5. SIDEBAR ---
selected_year = st.sidebar.selectbox("Active Year", [2026, 2025, 2024], index=0)
next_race_obj, next_race_index = get_next_race_info(selected_year)
breakdown = calculate_season_breakdown(selected_year)

with st.sidebar:
    st.markdown(f'<div><span class="pulse-light"></span><b>PIT WALL LIVE</b></div>', unsafe_allow_html=True)
    
    # Progress
    cal_data = fetch_api(str(selected_year))
    if cal_data:
        races_count = cal_data['MRData']['RaceTable']['Races']
        st.markdown(f'<div class="sb-header">SEASON PROGRESS</div>', unsafe_allow_html=True)
        st.write(f"Round {next_race_index} of {len(races_count)}")
        st.progress(next_race_index/len(races_count) if len(races_count) > 0 else 0)

    # Leader
    if breakdown:
        sorted_fam = sorted(breakdown.items(), key=lambda x: (x[1]['driver_pts'] + x[1]['bonus_pts'] + x[1]['penalty']), reverse=True)
        lead_player = sorted_fam[0][0]
        st.markdown(f'<div class="sb-header">CHAMPIONSHIP LEADER</div>', unsafe_allow_html=True)
        st.write(f"👑 {lead_player.upper()}")
        safe_st_image(DRIVER_IMAGES.get(PLAYERS_CONFIG[lead_player]['drivers'][0]), sidebar=True)

    # Updated Oracle UI
    st.markdown(f'<div class="sb-header">ORACLE PREDICTIONS</div>', unsafe_allow_html=True)
    if next_race_obj:
        st.markdown(f"📍 **{next_race_obj['Circuit']['Location']['locality']}**")
        oracle = calculate_oracle_probabilities(next_race_obj, selected_year)
        for i in oracle[:3]:
            st.write(f"🔮 **{i['player']}** ({i['key']})")
            st.progress(int(i['prob']))
            st.caption(f"Win Probability: {i['prob']:.1f}%")

# --- 6. TICKER LOGIC (FIXED) ---
ticker_str = f"NEXT RACE: {next_race_obj['raceName'].upper()} - {next_race_obj['date']}"
d_standings = fetch_api(f"{selected_year}/driverStandings")
try:
    s_list = d_standings['MRData']['StandingsTable']['StandingsLists'][0]['DriverStandings']
    if s_list:
        ticker_str = "  |  ".join([f"{i['position']}. {i['Driver']['familyName'].upper()} ({i['points']} PTS)" for i in s_list])
except: pass
st.markdown(f'<div class="ticker-wrap"><div class="ticker">{ticker_str} | {ticker_str}</div></div>', unsafe_allow_html=True)

# --- 7. MAIN UI ---
st.title("🏎️ F1 FAMILY HUB")
t_board, t_garage, t_next, t_grid, t_news = st.tabs(["🏆 CHAMPIONSHIP", "🛠️ GARAGES", "📅 CALENDAR", "🏎️ THE GRID", "📰 NEWS"])

with t_board:
    st.header(f"{selected_year} Rankings")
    table_rows = [{"Player": n, "Driver Pts": int(p["driver_pts"]), "Bonus Pts": int(p["bonus_pts"]), "Penalty": int(p["penalty"]), "TOTAL": int(p["driver_pts"] + p["bonus_pts"] + p["penalty"])} for n, p in breakdown.items()]
    df = pd.DataFrame(table_rows).sort_values("TOTAL", ascending=False)
    
    if len(df) >= 2:
        gap = df.iloc[0]['TOTAL'] - df.iloc[1]['TOTAL']
        leader = df.iloc[0]['Player']
        if gap > 25: st.info(f"🏆 **DOMINANT LEAD:** {leader} is pulling away! Gap: {gap} pts")
        elif gap < 10 and df.iloc[0]['TOTAL'] > 0: st.warning(f"⚔️ **CLOSE FIGHT:** {leader} is under pressure! Gap: only {gap} pts")
    st.dataframe(df, use_container_width=True, hide_index=True, column_config={"TOTAL": st.column_config.NumberColumn("TOTAL SCORE 🏆", format="%d")})

with t_garage:
    for player, cfg in PLAYERS_CONFIG.items():
        with st.expander(f"🛠️ GARAGE: {player.upper()}"):
            c1, c2, c3 = st.columns([1, 1, 1.2])
            with c1: safe_st_image(DRIVER_IMAGES.get(cfg['drivers'][0]), caption="DRIVER 1", width=180)
            with c2: safe_st_image(DRIVER_IMAGES.get(cfg['drivers'][1]), caption="DRIVER 2", width=180)
            with c3:
                team_key = next((k for k in FULL_GRID_2026 if k.lower().replace("_"," ") == cfg['constructor'].lower().replace("_"," ")), None)
                if team_key: safe_st_image(get_img(FULL_GRID_2026[team_key]['car'], ""), caption=f"{team_key.upper()} CHASSIS", width=280)

with t_next:
    if cal_data:
        r_list = cal_data['MRData']['RaceTable']['Races']
        r_names = [f"R{r['round']}: {r['raceName']}" for r in r_list]
        selected_r_name = st.selectbox("📅 Explore Season Calendar", r_names, index=next_race_index)
        sel_race = next(r for r in r_list if f"R{r['round']}: {r['raceName']}" == selected_r_name)
        st.header(f"{sel_race['raceName']}")
        
        c_m, c_d = st.columns([2, 1])
        with c_m: 
            circuit_id = sel_race['Circuit']['circuitId']
            final_map = get_img(f"imagesf1maps/{circuit_id}.png", f"https://www.formula1.com/content/dam/fom-website/2018-redesign-assets/circuit-maps-16x9/{circuit_id}.png")
            safe_st_image(final_map, caption=f"Circuit: {sel_race['Circuit']['circuitName']}") 
        with c_d:
            w = get_weather(sel_race['Circuit']['Location']['lat'], sel_race['Circuit']['Location']['long'])
            if w: st.markdown(f'<div class="f1-card"> {weather_icon(w["code"])}<br>{w["temp"]}°C | Rain: {w["rain"]}%</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="f1-card">📍 {sel_race["Circuit"]["Location"]["locality"]}<br>Date: {sel_race["date"]}</div>', unsafe_allow_html=True)

with t_grid:
    for team, data in FULL_GRID_2026.items():
        with st.expander(f"🏎️ {team.upper()} ENTRY"):
            col_d1, col_d2, col_car = st.columns([1, 1, 1.2])
            with col_d1: safe_st_image(DRIVER_IMAGES.get(data['drivers'][0], ""), width=180)
            with col_d2: safe_st_image(DRIVER_IMAGES.get(data['drivers'][1], ""), width=180)
            with col_car: safe_st_image(get_img(data['car'], ""), width=280)

with st.container():
    st.header("Latest Headlines")
    news_data = fetch_paddock_news()
    if news_data:
        for item in news_data:
            st.markdown(f'<div class="f1-card"><h3>{item["title"]}</h3><p style="color:#e10600; font-size:12px;">{item["published"]}</p><a href="{item["link"]}" target="_blank"><button style="background:#e10600; color:white; border:none; padding:8px 15px; border-radius:5px; font-weight:bold; cursor:pointer;">Read Story</button></a></div>', unsafe_allow_html=True)

st.markdown("<br><center><p style='color:#555;'>ENGINE BY MARANELLO | 2026</p></center>", unsafe_allow_html=True)