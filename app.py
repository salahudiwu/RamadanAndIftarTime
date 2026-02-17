import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import pytz
from astral.sun import sun
from astral import LocationInfo
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder

# --- PAGE CONFIG ---
st.set_page_config(page_title="Ramadan & Quran App", page_icon="🌙", layout="centered")

# --- DESIGN ---
st.markdown("""
<style>
.block-container { padding-top: 2rem; }
.stApp { color: #e6f1ff; background: linear-gradient(180deg, #0a192f, #020617); }
[data-testid="stStatusWidget"] { display: none; }
.stTable { background-color: rgba(255, 255, 255, 0.05); border-radius: 10px; }
div[data-testid="stMetricValue"] { color: #ffd700 !important; background-color: rgba(255, 255, 255, 0.1); padding: 15px; border-radius: 15px; border: 1px solid #ffd700; }
</style>
""", unsafe_allow_html=True)

# --- THEME TOGGLE ---
if "theme" not in st.session_state:
    st.session_state.theme = "dark"

def toggle_theme():
    st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"

st.button("🌗 Theme wechseln", on_click=toggle_theme)

if st.session_state.theme == "dark":
    st.markdown("""
    <style>
    .stApp { background: linear-gradient(180deg, #0a192f, #020617); color: #e6f1ff; }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
    .stApp { background: linear-gradient(180deg, #ffffff, #f0f0f0); color: #0a192f; }
    </style>
    """, unsafe_allow_html=True)

# --- TABS ---
tabs = st.tabs([
    "📿 Gamification & Dhikr",
    "🌙 Weltweite Iftar Zeiten"
])

# -------------------------------
# TAB 1: GAMIFICATION & DHIKR
# -------------------------------
with tabs[0]:
    st.header("📿 Dhikr & Ramadan Streak Tracker")

    if "dhikr_count" not in st.session_state: st.session_state.dhikr_count = 0
    if "ramadan_streak" not in st.session_state: st.session_state.ramadan_streak = 0
    if "last_day" not in st.session_state: st.session_state.last_day = datetime.now().date()

    today = datetime.now().date()
    if today > st.session_state.last_day:
        st.session_state.ramadan_streak += 1
        st.session_state.last_day = today
        st.session_state.dhikr_count = 0

    col1, col2, col3 = st.columns([1,1,1])
    if col1.button("➕ Zählen"): st.session_state.dhikr_count += 1
    if col2.button("🔄 Reset Dhikr"): st.session_state.dhikr_count = 0
    if col3.button("📅 Reset Streak"): st.session_state.ramadan_streak = 0

    st.metric("Dhikr Count", st.session_state.dhikr_count)
    st.metric("Ramadan Streak", f"{st.session_state.ramadan_streak} Tage")
    st.progress(min(st.session_state.dhikr_count/100,1.0))

# -------------------------------
# TAB 2: WELTWEITE IFTAR ZEITEN
# -------------------------------
with tabs[1]:
    st.header("🌙 Weltweite Iftar Zeiten")
    st.info("Zeigt Sunset/Iftar Zeiten für ausgewählte Städte")

    cities = {
        "Mekka, Saudi-Arabien": (21.3891, 39.8579),
        "Kairo, Ägypten": (30.0444, 31.2357),
        "Istanbul, Türkei": (41.0082, 28.9784),
        "Berlin, Deutschland": (52.5200, 13.4050),
        "Karabulak, Inguschetien": (43.3130, 44.9080),
        "Antwerpen, Belgien": (51.2194, 4.4025),
        "Houten Castellum, Niederlande": (52.0181, 5.1789),
        "München, Deutschland": (48.1374, 11.5755),
        "Oulu, Finnland": (65.0121, 25.4651)
    }

    selected_city = st.selectbox("Stadt auswählen:", list(cities.keys()))
    lat, lon = cities[selected_city]

    try:
        tf = pytz.timezone("UTC")
        tzf = TimezoneFinder()
        tz_name = tzf.timezone_at(lat=lat, lng=lon) or "UTC"
        local_tz = pytz.timezone(tz_name)

        now_city = datetime.now(local_tz)
        city_info = LocationInfo(selected_city, "World", tz_name, lat, lon)
        s = sun(city_info.observer, date=now_city.date(), tzinfo=local_tz)

        sunset_time = s['sunset'].strftime("%H:%M")
        st.metric(f"Sonnenuntergang / Iftar in {selected_city}", sunset_time)
        st.write(f"🕒 Aktuelle Uhrzeit: {now_city.strftime('%H:%M:%S')}")
        st.map(pd.DataFrame({'lat': [lat], 'lon': [lon]}))

    except Exception as e:
        st.error("Fehler bei der Berechnung der Sonnenuntergangszeit.")

# -------------------------------
# QURAN PLAYER
# -------------------------------
st.markdown("## 🎧 Quran Player")

@st.cache_data(ttl=86400)
def get_surah_list():
    url = "https://api.alquran.cloud/v1/surah"
    r = requests.get(url, timeout=10)
    return r.json()["data"]

surahs = get_surah_list()
options = [f"{s['number']} — {s['englishName']}" for s in surahs]
selected = st.selectbox("Sure auswählen:", options)
surah_num = int(selected.split(" — ")[0])
audio_url = f"https://cdn.islamic.network/quran/audio-surah/128/ar.alafasy/{surah_num}.mp3"

if st.button("▶ Sure starten"):
    st.audio(audio_url, format="audio/mp3")

# -------------------------------
# QURAN TEXT INTERFACE
# -------------------------------
st.markdown("## 📖 Quran")

@st.cache_data(ttl=86400)
def get_surah_text(num):
    url = f"https://api.alquran.cloud/v1/surah/{num}/de.asad"
    r = requests.get(url, timeout=10)
    return r.json()["data"]

try:
    surah = get_surah_text(surah_num)
    st.markdown(f"<div style='background: rgba(255,255,255,0.05); padding:20px; border-radius:15px; border:1px solid #ffd700; max-height:400px; overflow-y:auto;'>"
                f"<h3 style='color:#ffd700;'>{surah['englishName']} ({surah['name']})</h3>", unsafe_allow_html=True)
    for ayah in surah["ayahs"]:
        st.markdown(f"<p><b>{ayah['numberInSurah']}.</b> {ayah['text']}</p>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
except:
    st.warning("Suren konnten nicht geladen werden.")
