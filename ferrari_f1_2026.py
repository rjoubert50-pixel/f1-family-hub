import streamlit as st
import pandas as pd
import requests
import os
import feedparser
import plotly.express as px
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# --- 1. CONFIGURATION & GRID ---
st.set_page_config(page_title="F1 Family Hub 2026", layout="wide", page_icon="🏎️")
st_autorefresh(interval=60000, key="f1_refresh") # Auto-sync every minute

def get_img(local_path, web_fallback):
    if os.path.exists(local_path): return local_path
    return web_fallback

# Driver Headshots (Full 22-Driver Grid)
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
    [data-testid="stSidebar"] { background-color: #121212 !important; border-right: 2px solid #e10600; }
    .f1-card { background-color: #1a1a1a; border-left: 5px solid #e10600; padding: 15px; border-radius: 8px; margin-bottom: 10px; }
    .status-light { height: 10px; width: 10px; background-color: #00ff00; border-radius: 50%; display: inline-block; box-shadow: 0 0 8px #00ff00; animation: blink 2s infinite; }
    @keyframes blink { 0% { opacity: 1; } 50% { opacity: 0.3; } 100% { opacity: 1; } }
    .ticker-wrap { width: 100%; overflow: hidden; height: 35px; background-color: #121212; border-bottom: 2px solid #e10600; }
    .ticker { display: inline-block; animation: ticker 60s linear infinite; white-space: nowrap; line-height:35px; color: #e10600; font-weight: bold; }
    @keyframes ticker { 0% { transform: translateX(0); } 100% { transform: translateX(-100%); } }
    h1, h2, h3 { font-family: 'Arial Black'; text-transform: uppercase; color: white; }
    .sb-header { background: #e10600; color: white; padding: 5px 10px; font-size: 12px; font-weight: bold; border-radius: 3px; margin: 15px 0 5px 0; }
    </style>
""", unsafe_allow_html=True)

# --- 3. DATA ENGINE ---
BASE_URL = "https://api.jolpi.ca/ergast/f1"

@st.cache_data(ttl=600) # Cache results for 10 minutes
def fetch_api(endpoint):
    try:
        r = requests.get(f"{BASE_URL}/{endpoint}.json", timeout=10)
        return r.json() if r.status_code == 200 else None
    except: return None

@st.cache_data(ttl=600)
def get_full_season_breakdown(year):
    """Aggressive logic: Fetches all individual race results to calculate live scores."""
    players = {name: {"driver_pts": 0, "bonus_pts": 0, "total": cfg['penalty']} for name, cfg in PLAYERS_CONFIG.items()}
    history = {} # Round-by-round ledger
    
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
                # 1. Driver Points
                d_pts = sum([float(r['points']) for r in res if r['Driver']['driverId'] in cfg['drivers']])
                # 2. Bonus 3/2/1 + Lead + FL
                b_pts = ([3,2,1][top3.index(cfg['constructor'])] if cfg['constructor'] in top3 else 0)
                if fl_id in cfg['drivers']: b_pts += 2
                if cfg['constructor'] == winner_team: b_pts += 2
                
                players[n]["driver_pts"] += d_pts
                players[n]["bonus_pts"] += b_pts
                players[n]["total"] += (d_pts + b_pts)
                history[r_num][n] = d_pts + b_pts
                
    return players, history

# --- 4. SIDEBAR DASHBOARD ---
with st.sidebar:
    st.markdown('<h3><span class="status-light"></span> PIT WALL LIVE</h3>', unsafe_allow_html=True)
    selected_year = st.selectbox("Active Season", [2026, 2025, 2024], index=0)
    
    # Calculate Data
    stats, history_ledger = get_full_season_breakdown(selected_year)
    
    # Section: Next Race
    st.markdown('<div class="sb-header">NEXT MISSION</div>', unsafe_allow_html=True)
    cal = fetch_api(str(selected_year))
    next_r = None
    if cal:
        for r in cal['MRData']['RaceTable']['Races']:
            if datetime.strptime(r['date'], '%Y-%m-%d') >= datetime.now():
                next_r = r
                break
    if next_r:
        st.write(f"📍 **{next_r['raceName']}**")
        st.caption(f"Date: {next_r['date']}")
        diff = datetime.strptime(next_r['date'], '%Y-%m-%d') - datetime.now()
        st.write(f"⏱️ T-Minus: {diff.days} Days")

    # Section: Leaders
    st.markdown('<div class="sb-header">SEASON TITANS</div>', unsafe_allow_html=True)
    if stats:
        lead_player = max(stats, key=lambda x: stats[x]['total'])
        st.write(f"🏆 **{lead_player.upper()}** ({int(stats[lead_player]['total'])} pts)")
        
        # Leading Driver from Standings
        d_stand = fetch_api(f"{selected_year}/driverStandings")
        if d_stand:
            top_d = d_stand['MRData']['StandingsTable']['StandingsLists'][0]['DriverStandings'][0]
            st.write(f"🏎️ **{top_d['Driver']['familyName'].upper()}**")
            st.image(DRIVER_IMAGES.get(top_d['Driver']['driverId'], ""), width=120)

# --- 5. MAIN UI ---
# Ticker at top
ticker_str = " | ".join([f"{n.upper()}: {int(p['total'])} PTS" for n, p in stats.items()]) if stats else "Awaiting Results..."
st.markdown(f'<div class="ticker-wrap"><div class="ticker">{ticker_str} | {ticker_str}</div></div>', unsafe_allow_html=True)

st.title("🏁 SCUDERIA FAMILY COMMAND")
tabs = st.tabs(["🏆 CHAMPIONSHIP", "📜 HISTORY", "🛠️ GARAGE", "🏎️ THE GRID", "📰 NEWS"])

# --- CHAMPIONSHIP TAB ---
with tabs[0]:
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("Family World Standings")
        df_rows = [{"Player": n, "Driver Pts": int(p['driver_pts']), "Bonus": int(p['bonus_pts']), "Penalty": PLAYERS_CONFIG[n]['penalty'], "GRAND TOTAL": int(p['total'])} for n, p in stats.items()]
        df = pd.DataFrame(df_rows).sort_values("GRAND TOTAL", ascending=False)
        st.dataframe(df, use_container_width=True, hide_index=True, column_config={
            "GRAND TOTAL": st.column_config.ProgressColumn("GRAND TOTAL", format="%d", min_value=-30, max_value=600)
        })
    with col2:
        st.subheader("Title Progression")
        if history_ledger:
            chart_data = []
            for n in PLAYERS_CONFIG.keys():
                cur = PLAYERS_CONFIG[n]['penalty']
                for r in sorted(history_ledger.keys()):
                    cur += history_ledger[r][n]
                    chart_data.append({"Round": f"R{r}", "Player": n, "Points": cur})
            fig = px.line(pd.DataFrame(chart_data), x="Round", y="Points", color="Player", markers=True, template="plotly_dark")
            fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

# --- HISTORY TAB ---
with tabs[1]:
    if history_ledger:
        h_round = st.selectbox("Relive Round:", sorted(history_ledger.keys(), reverse=True))
        st.markdown(f'<div class="f1-card"><h3>Round {h_round} Performance Breakdown</h3></div>', unsafe_allow_html=True)
        h_df = pd.DataFrame([{"Player": n, "Weekend Pts": int(pts)} for n, pts in history_ledger[h_round].items()]).sort_values("Weekend Pts", ascending=False)
        st.table(h_df)
    else:
        st.info("No race history recorded for this year yet.")

# --- GARAGE & THE GRID (IDENTICAL LAYOUT) ---
def render_garage_view(data_dict, title):
    st.subheader(title)
    for name, cfg in data_dict.items():
        with st.expander(f"⚙️ {name.upper()}"):
            c1, c2, c3 = st.columns([1, 1, 1.2])
            with c1: st.image(DRIVER_IMAGES.get(cfg['drivers'][0], ""), caption="Driver 1")
            with c2: st.image(DRIVER_IMAGES.get(cfg['drivers'][1], ""), caption="Driver 2")
            with c3:
                # Find car image
                team_key = next((k for k in FULL_GRID_2026 if k.lower().replace("_"," ") == (cfg.get('constructor') or name).lower().replace("_"," ")), "Ferrari")
                st.image(FULL_GRID_2026[team_key]['car'], caption="Challenger")

with tabs[2]: render_garage_view(PLAYERS_CONFIG, "Family Garage Bays")
with tabs[3]: render_garage_view(FULL_GRID_2026, "Official 2026 Entry List")

# --- NEWS TAB ---
with tabs[4]:
    st.subheader("Paddock Radio")
    news = fetch_paddock_news()
    if news:
        for n in news:
            st.markdown(f"""
            <div class="f1-card">
                <h4>{n['title']}</h4>
                <p style="font-size:12px; color:#e10600;">{n['published']}</p>
                <a href="{n['link']}" target="_blank">Full Story →</a>
            </div>
            """, unsafe_allow_html=True)

st.markdown("<br><center><p style='color:#555;'>ENGINE BY MARANELLO | 2026 EDITION</p></center>", unsafe_allow_html=True)