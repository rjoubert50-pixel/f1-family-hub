import streamlit as st
import pandas as pd
import requests
import os
import feedparser
from datetime import datetime, timezone
from streamlit_autorefresh import st_autorefresh

# --- 1. ASSETS & CONFIG ---
st.set_page_config(page_title="F1 Family Hub", layout="wide", page_icon="🏎️")
# Refresh every 5 minutes to keep results updated
st_autorefresh(interval=300000, key="f1_refresh")

# --- UNIVERSAL SAFE IMAGE DISPLAY FUNCTION ---
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
    if os.path.exists(local_path):
        return local_path
    return web_fallback

# Driver Images (Preserving your .webp/local paths)
DRIVER_IMAGES = {
    "norris": get_img("imagesf1/norris.webp", "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/L/LANNOR01_Lando_Norris/lannor01.png"),
    "piastri": get_img("imagesf1/piastri.webp", "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/O/OSCPIA01_Oscar_Piastri/oscpia01.png"),
    "max_verstappen": get_img("imagesf1/max_verstappen.webp", "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/M/MAXVER01_Max_Verstappen/maxver01.png"),
    "hadjar": get_img("imagesf1/hadjar.webp", "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/I/ISAHAD01_Isack_Hadjar/isahad01.png"),
    "leclerc": get_img("imagesf1/leclerc.webp", "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/C/CHALEC01_Charles_Leclerc/chalec01.png"),
    "hamilton": get_img("imagesf1/hamilton.webp", "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/L/LEWHAM01_Lewis_Hamilton/lewham01.png"),
    "russell": get_img("imagesf1/russell.webp", "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/G/GEORUS01_George_Russell/georus01.png"),
    "antonelli": get_img("imagesf1/antonelli.webp", "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/A/ANDANT01_Andrea_Kimi_Antonelli/andant01.png"),
    "sainz": get_img("imagesf1/sainz.webp", "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/C/CARSAI01_Carlos_Sainz/carsai01.png"),
    "albon": get_img("imagesf1/albon.webp", "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/A/ALXALB01_Alexander_Albon/alxalb01.png"),
    "alonso": get_img("imagesf1/alonso.webp", "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/F/FERALO01_Fernando_Alonso/feralo01.png"),
    "stroll": get_img("imagesf1/stroll.webp", "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/L/LANSTR01_Lance_Stroll/lanstr01.png"),
    "gasly": get_img("imagesf1/gastly.webp", "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/P/PIEGAS01_Pierre_Gasly/piegas01.png"),
    "colapinto": get_img("imagesf1/colapinto.webp", "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/F/FRACOL01_Franco_Colapinto/fracol01.png"),
    "hulkenberg": get_img("imagesf1/hulkenberg.webp", "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/N/NICHUL01_Nico_Hulkenberg/nichul01.png"),
    "bortoleto": get_img("imagesf1/bortoleto.webp", "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/G/GABBOR01_Gabriel_Bortoleto/gabbor01.png"),
    "ocon": get_img("imagesf1/ocon.webp", "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/E/ESTOCO01_Esteban_Ocon/estoco01.png"),
    "bearman": get_img("imagesf1/bearman.webp", "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/O/OLIBEA01_Oliver_Bearman/olibea01.png"),
    "lawson": get_img("imagesf1/lawson.webp", "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/L/LIALAW01_Liam_Lawson/lialaw01.png"),
    "lindblad": get_img("imagesf1/lindblad.webp", "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/A/ARVLIN01_Arvid_Lindblad/arvlin01.png"),
    "perez": get_img("imagesf1/perez.webp", "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/S/SERPER01_Sergio_Perez/serper01.png"),
    "bottas": get_img("imagesf1/bottas.webp", "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/V/VALBOT01_Valtteri_Bottas/valbot01.png"),
}

TEAM_LOGOS = {
    "mclaren": get_img("imagesf1/mclaren.webp", "https://upload.wikimedia.org/wikipedia/en/thumb/6/66/McLaren_Racing_logo.svg/512px-McLaren_Racing_logo.svg.png"),
    "red_bull": get_img("imagesf1/red_bull.webp", "https://upload.wikimedia.org/wikipedia/en/thumb/1/15/Red_Bull_Racing_logo.svg/512px-Red_Bull_Racing_logo.svg.png"),
    "ferrari": get_img("imagesf1/ferrari.webp", "https://upload.wikimedia.org/wikipedia/en/thumb/d/d1/Ferrari-Logo.svg/512px-Ferrari-Logo.svg.png"),
    "mercedes": get_img("imagesf1/mercedes.webp", "https://upload.wikimedia.org/wikipedia/commons/thumb/f/fb/Mercedes-Benz_in_Formula_One_logo.svg/512px-Mercedes-Benz_in_Formula_One_logo.svg.png"),
    "aston_martin": get_img("imagesf1/aston_martin.webp", "https://upload.wikimedia.org/wikipedia/en/thumb/b/bd/Aston_Martin_F1_team_logo.svg/512px-Aston_Martin_F1_team_logo.svg.png"),
    "williams": get_img("imagesf1/williams.webp", "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7e/Williams_F1_logo.svg/512px-Williams_F1_logo.svg.png"),
    "alpine": get_img("imagesf1/alpine.webp", "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7e/Alpine_F1_Team_Logo.svg/512px-Alpine_F1_Team_Logo.svg.png"),
    "audi": get_img("imagesf1/audi.webp", "https://upload.wikimedia.org/wikipedia/commons/thumb/9/92/Audi_logo_detail.svg/512px-Audi_logo_detail.svg.png"),
    "haas": get_img("imagesf1/haas.webp", "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d4/Haas_F1_Team_logo.svg/512px-Haas_F1_Team_logo.svg.png"),
    "racing_bulls": get_img("imagesf1/racing_bulls.webp", "https://upload.wikimedia.org/wikipedia/en/thumb/2/2b/VCARB_F1_logo.svg/512px-VCARB_F1_logo.svg.png"),
    "cadillac": get_img("imagesf1/cadillac.webp", "https://upload.wikimedia.org/wikipedia/en/thumb/3/33/Cadillac_logo.svg/512px-Cadillac_logo.svg.png")
}

FULL_GRID_2026 = {
    "McLaren": {"drivers": ["norris", "piastri"], "car": "imagesf1/mclaren.webp"},
    "Red Bull": {"drivers": ["max_verstappen", "hadjar"], "car": "imagesf1/red_bull.webp"},
    "Ferrari": {"drivers": ["leclerc", "hamilton"], "car": "imagesf1/ferrari.webp"},
    "Mercedes": {"drivers": ["russell", "antonelli"], "car": "imagesf1/mercedes.webp"},
    "Aston Martin": {"drivers": ["alonso", "stroll"], "car": "imagesf1/aston_martin.webp"},
    "Williams": {"drivers": ["sainz", "albon"], "car": "imagesf1/williams.webp"},
    "Alpine": {"drivers": ["gasly", "colapinto"], "car": "imagesf1/alpine.webp"},
    "Audi": {"drivers": ["hulkenberg", "bortoleto"], "car": "imagesf1/audi.webp"},
    "Haas": {"drivers": ["ocon", "bearman"], "car": "imagesf1/haas.webp"},
    "Racing_Bulls": {"drivers": ["lawson", "lindblad"], "car": "imagesf1/racing_bulls.webp"},
    "Cadillac": {"drivers": ["perez", "bottas"], "car": "imagesf1/cadillac.webp"},
}

PLAYERS_CONFIG = {
    "Richie": {"drivers": ["max_verstappen", "perez"], "constructor": "audi", "penalty": 0},
    "Rickster": {"drivers": ["bottas", "leclerc"], "constructor": "aston_martin", "penalty": -5},
    "Yoshi": {"drivers": ["norris", "stroll"], "constructor": "ferrari", "penalty": -25},
    "Trip": {"drivers": ["lawson", "hadjar"], "constructor": "red_bull", "penalty": -5},
    "Josh": {"drivers": ["piastri", "hulkenberg"], "constructor": "haas", "penalty": 0},
    "Ruben": {"drivers": ["antonelli", "albon"], "constructor": "mercedes", "penalty": -5},
    "Clive": {"drivers": ["sainz", "russell"], "constructor": "racing_bulls", "penalty": 0},
}

# --- 2. THE CSS ---
st.markdown("""
    <style>
    .stApp { background: linear-gradient(180deg, #000000 0%, #1a1a1a 100%); color: #ffffff; }
    [data-testid="stSidebar"] { background-color: #808080 !important; border-right: 2px solid #333; }
    [data-testid="stSidebar"] * { color: white !important; font-weight: bold; }
    .pulse-light { height: 10px; width: 10px; background-color: #00ff00; border-radius: 50%; display: inline-block; box-shadow: 0 0 8px #00ff00; animation: pulse 1.5s infinite; margin-right: 8px; }
    @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.3; } 100% { opacity: 1; } }
    .f1-card { background-color: #121212; border: 1px solid #333; border-top: 4px solid #e10600; padding: 15px; border-radius: 12px; margin-bottom: 10px; }
    h1, h2, h3 { color: white !important; font-family: 'Arial Black', sans-serif; text-transform: uppercase; }
    .sb-header { background: #e10600; padding: 5px 10px; border-radius: 4px; font-size: 14px; letter-spacing: 1px; margin-top: 20px; margin-bottom: 10px; }
    .ticker-wrap { width: 100%; overflow: hidden; height: 35px; background-color: #121212; border-bottom: 2px solid #e10600; }
    .ticker { display: inline-block; animation: ticker 60s linear infinite; white-space: nowrap; }
    .ticker-item { display: inline-block; padding: 0 30px; font-weight: bold; color: white; font-size: 14px; text-transform: uppercase; line-height:35px; }
    .ticker-rank { color: #e10600; }
    @keyframes ticker { 0% { transform: translateX(0); } 100% { transform: translateX(-100%); } }
    .countdown-box { background: #e10600; padding: 15px; border-radius: 8px; text-align: center; margin-bottom: 20px; }
    .countdown-timer { font-family: 'Courier New', monospace; font-size: 32px; font-weight: bold; color: white; }
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
    feed = feedparser.parse("https://www.formula1.com/en/latest/all.xml")
    return [{"title": e.title, "link": e.link, "published": getattr(e, 'published', 'Recent'), "summary": getattr(e, 'summary', '')} for e in feed.entries[:10]]

# --- 4. CALCULATIONS ---
def get_driver_standings_ticker(year):
    data = fetch_api(f"{year}/driverStandings")
    try:
        standings = data['MRData']['StandingsTable']['StandingsLists'][0]['DriverStandings']
        return "".join([f'<span class="ticker-item"><span class="ticker-rank">{d["position"]}.</span> {d["Driver"]["familyName"]} ({d["points"]} PTS)</span>' for d in standings])
    except: return '<span class="ticker-item">Awaiting Season Results</span>'

def get_next_race_info(year):
    data = fetch_api(f"{year}")
    if not data: return None, 0
    races = data['MRData']['RaceTable']['Races']
    now = datetime.now()
    for i, r in enumerate(races):
        if datetime.strptime(r['date'], '%Y-%m-%d') >= now: return r, i
    return races[-1], len(races)-1

def calculate_oracle_probabilities(next_race, year):
    circuit_id = next_race['Circuit']['circuitId']
    h_data = fetch_api(f"{year-1}/circuits/{circuit_id}/results")
    h_pts = {}
    if h_data:
        try: h_pts = {r['Driver']['driverId']: float(r['points']) for r in h_data['MRData']['RaceTable']['Races'][0]['Results']}
        except: pass
    s_data = fetch_api(f"{year}/driverStandings")
    c_pts = {}
    if s_data:
        try: c_pts = {d['Driver']['driverId']: float(d['points']) for d in s_data['MRData']['StandingsTable']['StandingsLists'][0]['DriverStandings']}
        except: pass
    probs, key_drivers = {}, {}
    for p, cfg in PLAYERS_CONFIG.items():
        d1, d2 = cfg['drivers']
        s1 = (h_pts.get(d1, 0) * 2) + (c_pts.get(d1, 0) / 5)
        s2 = (h_pts.get(d2, 0) * 2) + (c_pts.get(d2, 0) / 5)
        key_drivers[p] = d1 if s1 >= s2 else d2
        probs[p] = s1 + s2 + 5
    total = sum(probs.values())
    return sorted([{"player": p, "prob": (v/total)*100, "key_driver": key_drivers[p].replace('_', ' ').title()} for p, v in probs.items()], key=lambda x: x['prob'], reverse=True)

@st.cache_data(ttl=60)
def calculate_season_breakdown(year):
    players = {name: {"driver_pts": 0, "bonus_pts": 0, "penalty": cfg['penalty']} for name, cfg in PLAYERS_CONFIG.items()}
    d_data = fetch_api(f"{year}/driverStandings")
    if d_data:
        try:
            pts_map = {item['Driver']['driverId']: float(item['points']) for item in d_data['MRData']['StandingsTable']['StandingsLists'][0]['DriverStandings']}
            for n, cfg in PLAYERS_CONFIG.items(): players[n]["driver_pts"] = sum([pts_map.get(d, 0) for d in cfg['drivers']])
        except: pass
    r_data = fetch_api(f"{year}/results")
    if r_data:
        try:
            for race in r_data['MRData']['RaceTable']['Races']:
                res = race['Results']
                fl = next((r['Driver']['driverId'] for r in res if r.get('FastestLap', {}).get('rank') == "1"), "")
                t_wk = {r['Constructor']['constructorId']: 0 for r in res}
                for r in res: t_wk[r['Constructor']['constructorId']] += float(r['points'])
                ranked = sorted(t_wk.items(), key=lambda x: x[1], reverse=True)
                top3 = [t[0] for t in ranked[:3]]
                for n, cfg in PLAYERS_CONFIG.items():
                    if fl in cfg['drivers']: players[n]["bonus_pts"] += 2
                    if cfg['constructor'] in top3: players[n]["bonus_pts"] += [3, 2, 1][top3.index(cfg['constructor'])]
                    if ranked and cfg['constructor'] == ranked[0][0]: players[n]["bonus_pts"] += 2
        except: pass
    return players

# --- 5. SIDEBAR ---
with st.sidebar:
    st.markdown(f'<div><span class="pulse-light"></span><b>PIT WALL LIVE</b></div>', unsafe_allow_html=True)
    selected_year = st.selectbox("Year", [2026, 2025, 2024], index=0)
    
    next_race_obj, next_race_index = get_next_race_info(selected_year)
    cal_data = fetch_api(str(selected_year))
    
    if cal_data:
        races_count = cal_data['MRData']['RaceTable']['Races']
        st.markdown(f'<div class="sb-header">SEASON PROGRESS</div>', unsafe_allow_html=True)
        st.write(f"Round {next_race_index} of {len(races_count)}")
        st.progress(next_race_index/len(races_count) if len(races_count) > 0 else 0)

    breakdown = calculate_season_breakdown(selected_year)
    if breakdown:
        sorted_fam = sorted(breakdown.items(), key=lambda x: (x[1]['driver_pts'] + x[1]['bonus_pts'] + x[1]['penalty']), reverse=True)
        lead_player = sorted_fam[0][0]
        lead_driver = PLAYERS_CONFIG[lead_player]['drivers'][0]
        st.markdown(f'<div class="sb-header">CURRENT #1: {lead_player.upper()}</div>', unsafe_allow_html=True)
        safe_st_image(DRIVER_IMAGES.get(lead_driver, ""), caption=f"Propelled by {lead_driver.upper()}", sidebar=True)

    st.markdown(f'<div class="sb-header">ORACLE PREDICTIONS</div>', unsafe_allow_html=True)
    if next_race_obj:
        oracle = calculate_oracle_probabilities(next_race_obj, selected_year)
        for i in oracle[:3]:
            st.write(f"{i['player']}: {i['prob']:.1f}%")

# --- 6. MAIN UI ---
ticker_content = get_driver_standings_ticker(selected_year)
st.markdown(f'<div class="ticker-wrap"><div class="ticker">{ticker_content} {ticker_content}</div></div>', unsafe_allow_html=True)

st.title("🏎️ F1 FAMILY HUB")
t_board, t_garage, t_next, t_grid, t_sessions, t_news = st.tabs(["🏆 CHAMPIONSHIP", "🛠️ GARAGES", "📅 RACE CALENDAR", "🏎️ THE GRID", "🏁 WEEKEND SESSIONS", "📰 NEWS"])

with t_board:
    st.header(f"{selected_year} Rankings")
    rows = [{"Player": n, "Driver Pts": int(p["driver_pts"]), "Bonus Pts": int(p["bonus_pts"]), "Penalty": int(p["penalty"]), "TOTAL": int(p["driver_pts"] + p["bonus_pts"] + p["penalty"])} for n, p in breakdown.items()]
    df = pd.DataFrame(rows).sort_values("TOTAL", ascending=False)
    if len(df) >= 2:
        gap = df.iloc[0]['TOTAL'] - df.iloc[1]['TOTAL']
        leader = df.iloc[0]['Player']
        if gap > 25: st.info(f"🏆 **DOMINANT LEAD:** {leader} is pulling away! Gap: {gap} pts")
        elif gap < 10 and df.iloc[0]['TOTAL'] > 0: st.warning(f"⚔️ **CLOSE FIGHT:** {leader} is under pressure! Gap: only {gap} pts")
    st.dataframe(df, use_container_width=True, hide_index=True, column_config={"TOTAL": st.column_config.NumberColumn("TOTAL SCORE 🏆", format="%d")})

with t_garage:
    st.header("Player Garages")
    for player, cfg in PLAYERS_CONFIG.items():
        with st.expander(f"🛠️ GARAGE BAY: {player.upper()}"):
            col_d1, col_d2, col_chassis = st.columns([1, 1, 1.2])
            with col_d1: safe_st_image(DRIVER_IMAGES.get(cfg['drivers'][0], ""), caption=f"D1: {cfg['drivers'][0].upper()}", width=180)
            with col_d2: safe_st_image(DRIVER_IMAGES.get(cfg['drivers'][1], ""), caption=f"D2: {cfg['drivers'][1].upper()}", width=180)
            with col_chassis:
                team_key = next((k for k in FULL_GRID_2026 if k.lower().replace("_"," ") == cfg['constructor'].lower().replace("_"," ")), None)
                if team_key: safe_st_image(get_img(FULL_GRID_2026[team_key]['car'], ""), caption=f"{team_key} Livery", width=280)

with t_next:
    if cal_data:
        races_list = cal_data['MRData']['RaceTable']['Races']
        race_names = [f"R{r['round']}: {r['raceName']}" for r in races_list]
        selected_r_name = st.selectbox("📅 Explore Season Calendar", race_names, index=next_race_index)
        sel_race = next(r for r in races_list if f"R{r['round']}: {r['raceName']}" == selected_r_name)
        st.header(f"{sel_race['raceName']}")
        
        race_dt = datetime.strptime(f"{sel_race['date']} {sel_race.get('time', '14:00:00Z').replace('Z', '')}", "%Y-%m-%d %H:%M:%S")
        if race_dt > datetime.now():
            diff = race_dt - datetime.now()
            st.markdown(f'<div class="countdown-box"><div class="countdown-timer">{diff.days}d {diff.seconds//3600}h {(diff.seconds//60)%60}m</div></div>', unsafe_allow_html=True)
        
        c_m, c_d = st.columns([2, 1])
        with c_m: 
            circuit_id = sel_race['Circuit']['circuitId']
            final_map = get_img(f"imagesf1maps/{circuit_id}.png", f"https://www.formula1.com/content/dam/fom-website/2018-redesign-assets/circuit-maps-16x9/{circuit_id}.png")
            safe_st_image(final_map, caption=f"Circuit: {sel_race['Circuit']['circuitName']}") 
            
        with c_d:
            w = get_weather(sel_race['Circuit']['Location']['lat'], sel_race['Circuit']['Location']['long'])
            if w: st.markdown(f'<div class="f1-card">🌦️ {weather_icon(w["code"])}<br>{w["temp"]}°C | Rain: {w["rain"]}%</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="f1-card">📍 {sel_race["Circuit"]["Location"]["locality"]}<br>Date: {sel_race["date"]}</div>', unsafe_allow_html=True)

with t_grid:
    st.header("The 2026 Grid")
    for team, data in FULL_GRID_2026.items():
        with st.expander(f"🏎️ {team.upper()} ENTRY"):
            col_d1, col_d2, col_car = st.columns([1, 1, 1.2])
            with col_d1: safe_st_image(DRIVER_IMAGES.get(data['drivers'][0], ""), width=180)
            with col_d2: safe_st_image(DRIVER_IMAGES.get(data['drivers'][1], ""), width=180)
            with col_car: safe_st_image(get_img(data['car'], ""), width=280)

# --- UPDATED TAB: WEEKEND SESSIONS ---
with t_sessions:
    st.header("🏁 SESSION UPDATES & STARTING GRID")
    
    # Allow user to pick which race weekend to view results for
    if cal_data:
        session_race_names = [f"R{r['round']}: {r['raceName']}" for r in races_list]
        session_choice = st.selectbox("Select Weekend to View Sessions:", session_race_names, index=next_race_index)
        round_num = session_choice.split(":")[0].replace("R", "")

        col_q, col_g = st.columns(2)

        with col_q:
            st.subheader("Qualifying Shootout")
            q_data = fetch_api(f"{selected_year}/{round_num}/qualifying")
            if q_data and q_data['MRData']['RaceTable']['Races']:
                q_results = q_data['MRData']['RaceTable']['Races'][0]['QualifyingResults']
                q_list = [{"Pos": r['position'], "Driver": r['Driver']['familyName'], "Team": r['Constructor']['name'], "Q3": r.get('Q3', 'N/A')} for r in q_results]
                st.dataframe(pd.DataFrame(q_list), use_container_width=True, hide_index=True)
            else:
                st.info("Qualifying data not yet available for this weekend.")

        with col_g:
            st.subheader("Final Starting Grid")
            # The Starting Grid is pulled from the Qualifying rankings
            if q_data and q_data['MRData']['RaceTable']['Races']:
                st.markdown('<div class="f1-card">', unsafe_allow_html=True)
                for r in q_results[:10]: # Top 10 focus
                    st.write(f"**P{r['position']}** | {r['Driver']['familyName']} ({r['Constructor']['name']})")
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.info("Grid will be confirmed after Qualifying.")
                
        # Optional: Add Practice results if the API supports it
        st.divider()
        st.subheader("Practice Intelligence")
        st.caption("Official Practice rankings usually populate here 1 hour after the session ends.")
        # Some APIs don't provide FP1/2/3 results easily, so we show a placeholder for the strategy
        st.write("📈 *Check the 'Oracle' in the sidebar for updated probabilities based on these session times!*")

with t_news:
    st.header("Latest Headlines")
    news_data = fetch_paddock_news()
    for item in news_data:
        st.markdown(f'<div class="f1-card"><h3>{item["title"]}</h3><p style="color:#e10600; font-size:12px;">{item["published"]}</p><p>{item["summary"][:200]}...</p><a href="{item["link"]}" target="_blank"><button style="background:#e10600; color:white; border:none; padding:8px 15px; border-radius:5px; font-weight:bold; cursor:pointer;">Read Story</button></a></div>', unsafe_allow_html=True)

st.markdown("<br><center><p style='color:#555;'>ENGINE BY MARANELLO | 2026</p></center>", unsafe_allow_html=True)