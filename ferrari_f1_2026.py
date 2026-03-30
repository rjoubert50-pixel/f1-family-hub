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

def get_img(local_path, web_fallback):
    if os.path.exists(local_path): return local_path
    return web_fallback

# Full 22-Driver Grid
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
    "gasly": get_img("imagesf1/gasly.webp", "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/P/PIEGAS01_Pierre_Gasly/piegas01.png"),
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

# --- 2. THE CSS (PREMIUM HUB STYLE) ---
st.markdown("""
    <style>
    .stApp { background: linear-gradient(180deg, #000000 0%, #1a1a1a 100%); color: #ffffff; }
    [data-testid="stSidebar"] { background-color: #121212 !important; border-right: 2px solid #e10600; min-width: 350px !important; }
    .f1-card { background-color: #1a1a1a; border-left: 5px solid #e10600; padding: 15px; border-radius: 8px; margin-bottom: 10px; }
    .status-light { height: 10px; width: 10px; background-color: #00ff00; border-radius: 50%; display: inline-block; box-shadow: 0 0 8px #00ff00; animation: blink 2s infinite; margin-right: 10px; }
    @keyframes blink { 0% { opacity: 1; } 50% { opacity: 0.3; } 100% { opacity: 1; } }
    .ticker-wrap { width: 100%; overflow: hidden; height: 35px; background-color: #121212; border-bottom: 2px solid #e10600; }
    .ticker { display: inline-block; animation: ticker 60s linear infinite; white-space: nowrap; line-height:35px; color: #e10600; font-weight: bold; text-transform: uppercase; }
    @keyframes ticker { 0% { transform: translateX(0); } 100% { transform: translateX(-100%); } }
    h1, h2, h3 { font-family: 'Arial Black'; text-transform: uppercase; color: white; letter-spacing: 1px; }
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
        if not feed.entries: return []
        return [{"title": e.title, "link": e.link, "published": getattr(e, 'published', 'Recent')} for e in feed.entries[:10]]
    except: return []

@st.cache_data(ttl=600)
def get_season_master_data(year):
    """The Unstoppable Brain: Calculates everything from race results."""
    players = {name: {"driver_pts": 0, "bonus_pts": 0, "total": cfg['penalty']} for name, cfg in PLAYERS_CONFIG.items()}
    history = {}
    
    r_data = fetch_api(f"{year}/results")
    if r_data and r_data['MRData']['RaceTable']['Races']:
        races = r_data['MRData']['RaceTable']['Races']
        for race in races:
            r_num = int(race['round'])
            res = race['Results']
            
            # 1. Fastest Lap (+2)
            fl_id = next((r['Driver']['driverId'] for r in res if r.get('FastestLap', {}).get('rank') == "1"), "")
            
            # 2. Team Performance
            t_wknd = {}
            for r in res:
                c_id = r['Constructor']['constructorId']
                t_wknd[c_id] = t_wknd.get(c_id, 0) + float(r['points'])
            
            ranked = sorted(t_wknd.items(), key=lambda x: x[1], reverse=True)
            top3 = [t[0] for t in ranked[:3]]
            winner_team = ranked[0][0] if ranked else ""
            
            history[r_num] = {n: 0 for n in PLAYERS_CONFIG.keys()}
            
            for n, cfg in PLAYERS_CONFIG.items():
                # Driver Pts
                d_pts = sum([float(r['points']) for r in res if r['Driver']['driverId'] in cfg['drivers']])
                # Bonuses
                b_pts = ([3,2,1][top3.index(cfg['constructor'])] if cfg['constructor'] in top3 else 0)
                if fl_id in cfg['drivers']: b_pts += 2
                if cfg['constructor'] == winner_team: b_pts += 2
                
                players[n]["driver_pts"] += d_pts
                players[n]["bonus_pts"] += b_pts
                players[n]["total"] += (d_pts + b_pts)
                history[r_num][n] = d_pts + b_pts
                
    return players, history

# --- 4. SIDEBAR COMMAND CENTER ---
with st.sidebar:
    st.markdown('<h3><span class="status-light"></span> PIT WALL LIVE</h3>', unsafe_allow_html=True)
    selected_year = st.selectbox("Season", [2026, 2025, 2024], index=0)
    
    stats, history_ledger = get_season_master_data(selected_year)
    
    # NEXT GP
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
        st.caption(f"Track: {next_r['Circuit']['Location']['locality']}")
        diff = datetime.strptime(next_r['date'], '%Y-%m-%d') - datetime.now()
        st.write(f"⏱️ Countdown: **{diff.days} Days**")

    # LEADERS
    st.markdown('<div class="sb-header">🏆 SEASON TITANS</div>', unsafe_allow_html=True)
    if stats:
        lead_p = max(stats, key=lambda x: stats[x]['total'])
        st.write(f"🥇 Player: **{lead_p.upper()}** ({int(stats[lead_p]['total'])} pts)")
        
        d_stand = fetch_api(f"{selected_year}/driverStandings")
        if d_stand:
            top_d = d_stand['MRData']['StandingsTable']['StandingsLists'][0]['DriverStandings'][0]
            st.write(f"🏎️ Driver: **{top_d['Driver']['familyName'].upper()}**")
            st.image(DRIVER_IMAGES.get(top_d['Driver']['driverId'], ""), width=150)

# --- 5. TOP TICKER ---
d_stand = fetch_api(f"{selected_year}/driverStandings")
try:
    s_list = d_stand['MRData']['StandingsTable']['StandingsLists'][0]['DriverStandings']
    ticker_str = " | ".join([f"{i['position']}. {i['Driver']['familyName'].upper()} ({i['points']} PTS)" for i in s_list])
except:
    ticker_str = f"NEXT RACE: {next_r['raceName'].upper()} ({next_r['date']})" if next_r else "Awaiting Results..."

st.markdown(f'<div class="ticker-wrap"><div class="ticker">{ticker_str} | {ticker_str}</div></div>', unsafe_allow_html=True)

# --- 6. MAIN HUB ---
st.title("🏁 SCUDERIA FAMILY HUB")
tabs = st.tabs(["🏆 CHAMPIONSHIP", "📜 HISTORY", "🛠️ GARAGE", "🏎️ THE GRID", "📰 NEWS"])

# CHAMPIONSHIP
with tabs[0]:
    c1, c2 = st.columns([1.5, 1])
    with c1:
        st.subheader("Leaderboard")
        df_rows = [{"Player": n, "Drivers": int(p['driver_pts']), "Bonus": int(p['bonus_pts']), "Penalty": PLAYERS_CONFIG[n]['penalty'], "TOTAL": int(p['total'])} for n, p in stats.items()]
        df = pd.DataFrame(df_rows).sort_values("TOTAL", ascending=False)
        st.dataframe(df, use_container_width=True, hide_index=True, column_config={
            "TOTAL": st.column_config.ProgressColumn("TOTAL", format="%d", min_value=-30, max_value=600)
        })
    with c2:
        st.subheader("Title Race Progression")
        if history_ledger:
            chart_rows = []
            for n in PLAYERS_CONFIG.keys():
                cur = PLAYERS_CONFIG[n]['penalty']
                for r in sorted(history_ledger.keys()):
                    cur += history_ledger[r][n]
                    chart_rows.append({"Round": f"R{r}", "Player": n, "Points": cur})
            fig = px.line(pd.DataFrame(chart_rows), x="Round", y="Points", color="Player", markers=True, template="plotly_dark")
            fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

# HISTORY
with tabs[1]:
    if history_ledger:
        h_round = st.selectbox("Select Race to Review:", sorted(history_ledger.keys(), reverse=True))
        h_res = fetch_api(f"{selected_year}/{h_round}/results")
        if h_res:
            race_meta = h_res['MRData']['RaceTable']['Races'][0]
            st.markdown(f'<div class="f1-card"><h3>{race_meta["raceName"]} Breakdown</h3></div>', unsafe_allow_html=True)
            col_a, col_b = st.columns(2)
            with col_a:
                st.write("**Family Round Rankings**")
                st.table(pd.DataFrame([{"Player": n, "Weekend Points": int(p)} for n, p in history_ledger[h_round].items()]).sort_values("Weekend Points", ascending=False))
            with col_b:
                st.write("**Official Podium**")
                podium = [{"Pos": r['position'], "Driver": r['Driver']['familyName']} for r in race_meta['Results'][:3]]
                st.table(pd.DataFrame(podium))
    else:
        st.info("Results will appear here after Round 1.")

# GARAGE & GRID
def draw_spec_view(data, title):
    st.subheader(title)
    for name, cfg in data.items():
        with st.expander(f"⚙️ {name.upper()}"):
            col1, col2, col3 = st.columns([1, 1, 1.2])
            with col1: st.image(DRIVER_IMAGES.get(cfg['drivers'][0], ""), caption="Driver 1")
            with col2: st.image(DRIVER_IMAGES.get(cfg['drivers'][1], ""), caption="Driver 2")
            with col3:
                t_key = next((k for k in FULL_GRID_2026 if k.lower().replace("_"," ") == (cfg.get('constructor') or name).lower().replace("_"," ")), "Ferrari")
                st.image(FULL_GRID_2026[t_key]['car'], caption="Livery")

with tabs[2]: draw_spec_view(PLAYERS_CONFIG, "Garage Bays")
with tabs[3]: draw_spec_view(FULL_GRID_2026, "2026 Constructor Specs")

# NEWS
with tabs[4]:
    st.subheader("Headlines")
    news_list = fetch_paddock_news()
    if news_list:
        for n in news_list:
            st.markdown(f'<div class="f1-card"><b>{n["title"]}</b><br><a href="{n["link"]}" target="_blank" style="color:#e10600; font-size:12px;">Read Full Story →</a></div>', unsafe_allow_html=True)
    else: st.info("Paddock radio silent.")

st.markdown("<br><center><p style='color:#555;'>ENGINE BY MARANELLO | 2026</p></center>", unsafe_allow_html=True)