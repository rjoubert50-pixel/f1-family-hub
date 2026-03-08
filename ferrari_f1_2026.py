import streamlit as st
import pandas as pd
import requests
import os
import feedparser
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# --- 1. SETUP ---
st.set_page_config(page_title="F1 Family Hub", layout="wide", page_icon="🏎️")
# Refresh every 60 seconds to catch the API update
st_autorefresh(interval=60000, key="f1_refresh")

def safe_st_image(img_path, caption="", width=None, sidebar=False):
    target = st.sidebar if sidebar else st
    try:
        if img_path:
            target.image(img_path, caption=caption, width=width, use_container_width=(width is None))
    except:
        pass # Silently fail to keep dashboard clean

def get_img(local_path, web_fallback):
    if os.path.exists(local_path): return local_path
    return web_fallback

# --- 2. GRID & PLAYER CONFIG ---
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

# --- 3. DATA ENGINE ---
BASE_URL = "https://api.jolpi.ca/ergast/f1"

@st.cache_data(ttl=60)
def fetch_api(endpoint):
    try:
        r = requests.get(f"{BASE_URL}/{endpoint}.json", timeout=10)
        return r.json() if r.status_code == 200 else None
    except: return None

@st.cache_data(ttl=3600)
def fetch_paddock_news():
    try:
        feed = feedparser.parse("https://www.formula1.com/en/latest/all.xml")
        return [{"title": e.title, "link": e.link, "published": getattr(e, 'published', 'Recent'), "summary": getattr(e, 'summary', '')} for e in feed.entries[:10]]
    except: return []

# --- 4. CALCULATION LOGIC ---
@st.cache_data(ttl=60)
def calculate_season_breakdown(year):
    players = {name: {"driver_pts": 0, "bonus_pts": 0, "penalty": cfg['penalty']} for name, cfg in PLAYERS_CONFIG.items()}
    
    # 1. Official Driver Standings (Slow to update, but reliable for history)
    d_data = fetch_api(f"{year}/driverStandings")
    if d_data:
        try:
            standings_list = d_data['MRData']['StandingsTable']['StandingsLists'][0]['DriverStandings']
            pts_map = {item['Driver']['driverId']: float(item['points']) for item in standings_list}
            for n, cfg in PLAYERS_CONFIG.items():
                players[n]["driver_pts"] = sum([pts_map.get(d, 0) for d in cfg['drivers']])
        except: pass

    # 2. Race Results Logic (Fast to update, essential for Bonus Math)
    r_data = fetch_api(f"{year}/results")
    if r_data:
        try:
            for race in r_data['MRData']['RaceTable']['Races']:
                res = race['Results']
                fl_id = next((r['Driver']['driverId'] for r in res if r.get('FastestLap', {}).get('rank') == "1"), "")
                t_wk = {r['Constructor']['constructorId']: 0 for r in res}
                for r in res: t_wk[r['Constructor']['constructorId']] += float(r['points'])
                ranked = sorted(t_wk.items(), key=lambda x: x[1], reverse=True)
                top3 = [t[0] for t in ranked[:3]]
                for n, cfg in PLAYERS_CONFIG.items():
                    if fl_id in cfg['drivers']: players[n]["bonus_pts"] += 2
                    if cfg['constructor'] in top3: players[n]["bonus_pts"] += [3, 2, 1][top3.index(cfg['constructor'])]
                    if ranked and cfg['constructor'] == ranked[0][0]: players[n]["bonus_pts"] += 2
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

# --- 5. THE CSS ---
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

# --- 6. UI ---
selected_year = st.sidebar.selectbox("Active Year", [2026, 2025, 2024], index=0)
cal_data = fetch_api(str(selected_year))

# Ticker Logic
ticker_str = f"NEXT RACE: MELBOURNE GP - MARCH 8th 2026"
d_standings = fetch_api(f"{selected_year}/driverStandings")
try:
    s_list = d_standings['MRData']['StandingsTable']['StandingsLists'][0]['DriverStandings']
    if s_list:
        ticker_str = "  |  ".join([f"{i['position']}. {i['Driver']['familyName'].upper()} ({i['points']} PTS)" for i in s_list])
except: pass

st.markdown(f'<div class="ticker-wrap"><div class="ticker">{ticker_str} | {ticker_str}</div></div>', unsafe_allow_html=True)

# Sidebar Content
with st.sidebar:
    st.markdown('<div class="sb-header">ORACLE PREDICTIONS</div>', unsafe_allow_html=True)
    next_r = None
    if cal_data:
        races = cal_data['MRData']['RaceTable']['Races']
        for r in races:
            if datetime.strptime(r['date'], '%Y-%m-%d') >= datetime.now():
                next_r = r
                break
    if next_r:
        st.markdown(f"📍 **{next_r['Circuit']['Location']['locality']}**")
        oracle = calculate_oracle_probabilities(next_r, selected_year)
        for i in oracle[:3]:
            st.write(f"{i['player']} ({i['key']})")
            st.progress(int(i['prob']))
            st.caption(f"Win Probability: {i['prob']:.1f}%")

    # Leaderboard calc for Sidebar Photo
    breakdown = calculate_season_breakdown(selected_year)
    if breakdown:
        sorted_f = sorted(breakdown.items(), key=lambda x: (x[1]['driver_pts'] + x[1]['bonus_pts'] + x[1]['penalty']), reverse=True)
        lead_player = sorted_f[0][0]
        st.markdown(f'<div class="sb-header">CHAMPIONSHIP LEADER</div>', unsafe_allow_html=True)
        st.write(f"👑 {lead_player.upper()}")
        safe_st_image(DRIVER_IMAGES.get(PLAYERS_CONFIG[lead_player]['drivers'][0]), sidebar=True)

# Main Screen
st.title("🏎️ F1 FAMILY HUB")
t_board, t_garage, t_cal, t_news = st.tabs(["🏆 CHAMPIONSHIP", "🛠️ GARAGES", "📅 CALENDAR", "📰 NEWS"])

with t_board:
    st.header("World Rankings")
    table_rows = [{"Player": n, "Driver Pts": int(p["driver_pts"]), "Bonus Pts": int(p["bonus_pts"]), "Penalty": int(p["penalty"]), "TOTAL": int(p["driver_pts"] + p["bonus_pts"] + p["penalty"])} for n, p in breakdown.items()]
    df = pd.DataFrame(table_rows).sort_values("TOTAL", ascending=False)
    st.dataframe(df, use_container_width=True, hide_index=True)

with t_garage:
    for player, cfg in PLAYERS_CONFIG.items():
        with st.expander(f"🛠️ GARAGE: {player.upper()}"):
            c1, c2, c3 = st.columns([1, 1, 1.2])
            with c1: safe_st_image(DRIVER_IMAGES.get(cfg['drivers'][0]), caption="DRIVER 1")
            with c2: safe_st_image(DRIVER_IMAGES.get(cfg['drivers'][1]), caption="DRIVER 2")
            with c3:
                team_key = next((k for k in FULL_GRID_2026 if k.lower().replace("_"," ") == cfg['constructor'].lower().replace("_"," ")), None)
                if team_key: safe_st_image(get_img(FULL_GRID_2026[team_key]['car'], ""), caption=f"{team_key.upper()} CHASSIS")

with t_cal:
    if cal_data:
        r_list = [f"R{r['round']}: {r['raceName']}" for r in races]
        choice = st.selectbox("Explore Track Map", r_list)
        sel = next(r for r in races if f"R{r['round']}: {r['raceName']}" == choice)
        c_m, c_d = st.columns([2, 1])
        with c_m: safe_st_image(f"https://www.formula1.com/content/dam/fom-website/2018-redesign-assets/circuit-maps-16x9/{sel['Circuit']['circuitId']}.png")
        with c_d: st.markdown(f'<div class="f1-card">📍 {sel["Circuit"]["Location"]["locality"]}<br>Date: {sel["date"]}</div>', unsafe_allow_html=True)

with t_news:
    st.header("Paddock News")
    news = fetch_paddock_news()
    for n in news:
        st.markdown(f'<div class="f1-card"><h3>{n["title"]}</h3><p>{n["published"]}</p><a href="{n["link"]}" target="_blank">READ STORY</a></div>', unsafe_allow_html=True)

st.markdown("<br><center><p style='color:#555;'>ENGINE BY MARANELLO | 2026</p></center>", unsafe_allow_html=True)