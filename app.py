import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import pytz
from astral.sun import sun
from astral import LocationInfo
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Ramadan & Quran App",
    page_icon="🌙",
    layout="centered"
)

# --- THEME TOGGLE ---
if "theme" not in st.session_state:
    st.session_state.theme = "dark"

def toggle_theme():
    st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"

st.button("🌗 Theme wechseln", on_click=toggle_theme)

# Theme Styles
if st.session_state.theme == "dark":
    st.markdown("""
    <style>
    .stApp { background: linear-gradient(180deg, #0a192f, #020617); color: #e6f1ff; }
    .block-container { padding-top: 2rem; }
    div[data-testid="stMetricValue"] { color: #ffd700 !important; background-color: rgba(255,255,255,0.1); border-radius:15px; border:1px solid #ffd700; padding:15px;}
    .stTable { background-color: rgba(255,255,255,0.05); border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
    .stApp { background: linear-gradient(180deg,#ffffff,#f0f0f0); color:#0a192f; }
    .block-container { padding-top: 2rem; }
    div[data-testid="stMetricValue"] { color: #ffd700 !important; background-color: rgba(0,0,0,0.05); border-radius:15px; border:1px solid #ffd700; padding:15px;}
    .stTable { background-color: rgba(0,0,0,0.05); border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- TABS ---
tabs = st.tabs([
    "🌙 Dashboard",
    "📿 Dhikr",
    "📚 Tafsir",
    "🕌 Kalender",
    "🎧 Quran Audio"
])

# --- TAB 0: Dashboard ---
with tabs[0]:
    st.header("🌙 Ramadan Dashboard")

    # IP / Stadt
    @st.cache_data(ttl=3600)
    def get_ip_info():
        try:
            r = requests.get('https://ipapi.co', timeout=5)
            return r.json()
        except:
            return {"city": "Aachen"}

    ip_info = get_ip_info()
    city_input = st.text_input("📍 Standort anpassen:", value=ip_info.get("city", "Aachen"))

    # Berechnung Gebetszeiten
    try:
        geolocator = Nominatim(user_agent="ramadan_app_v2")
        location = geolocator.geocode(city_input, language="de")
        if location:
            lat, lon = location.latitude, location.longitude
            tf = TimezoneFinder()
            tz_name = tf.timezone_at(lng=lon, lat=lat) or "UTC"
            local_tz = pytz.timezone(tz_name)
            now_city = datetime.now(local_tz)

            city_info = LocationInfo(city_input, "World", tz_name, lat, lon)
            s = sun(city_info.observer, date=now_city.date(), tzinfo=local_tz)
            asr_val = s['noon'] + (s['sunset'] - s['noon']) * 0.5

            df = pd.DataFrame([
                ["Fajr (Sahur-Ende)", s['dawn'].strftime("%H:%M")],
                ["Dhuhr", s['noon'].strftime("%H:%M")],
                ["Asr", asr_val.strftime("%H:%M")],
                ["Maghrib (Iftar)", s['sunset'].strftime("%H:%M")],
                ["Isha", s['dusk'].strftime("%H:%M")]
            ], columns=["Gebet", "Uhrzeit"])
            st.subheader("Gebetszeiten")
            st.table(df)
            st.write(f"🕒 Aktuelle Uhrzeit in {city_input}: **{now_city.strftime('%H:%M:%S')}**")
        else:
            st.error("Stadt nicht gefunden.")
    except:
        st.warning("Gebetszeiten konnten nicht geladen werden.")

    # Countdown Ramadan
    ramadan_start = datetime(2026, 2, 18, 0, 0, 0)
    days_left = (ramadan_start - datetime.now()).days
    if days_left > 0:
        st.info(f"🕌 Countdown bis Ramadan-Beginn: {days_left} Tage")
    else:
        st.success("🌙 Ramadan hat begonnen!")

    # Fortschritt
    ramadan_days = 30
    today_day = min(datetime.now().day, ramadan_days)
    st.progress(today_day / ramadan_days)
    st.metric("Ramadan Tag", f"{today_day}/30")

# --- TAB 1: Dhikr Counter ---
with tabs[1]:
    st.header("📿 Dhikr Counter")
    if "dhikr" not in st.session_state:
        st.session_state.dhikr = 0

    col1, col2 = st.columns(2)
    if col1.button("➕ Zählen"):
        st.session_state.dhikr += 1
    if col2.button("🔄 Reset"):
        st.session_state.dhikr = 0
    st.metric("Dhikr", st.session_state.dhikr)

# --- TAB 2: Tafsir Viewer ---
with tabs[2]:
    st.header("📚 Tafsir Viewer")
    surah_num = st.number_input("Sure Nummer", 1, 114, 1)
    ayah_num = st.number_input("Ayah Nummer", 1, 286, 1)
    if st.button("Tafsir laden"):
        try:
            url = f"https://api.alquran.cloud/v1/ayah/{surah_num}:{ayah_num}/de.bubenheim"
            r = requests.get(url).json()
            st.success(f"Tafsir Sure {surah_num}:{ayah_num}")
            st.markdown(
                f"<div style='max-height:400px; overflow-y:auto; padding:10px; border:1px solid #ffd700; border-radius:10px;'>{r['data']['text']}</div>",
                unsafe_allow_html=True
            )
        except:
            st.error("Tafsir konnte nicht geladen werden.")

# --- TAB 3: Islamischer Kalender ---
with tabs[3]:
    st.header("🕌 Islamischer Kalender")
    try:
        today = datetime.now().strftime("%d-%m-%Y")
        url = f"https://api.aladhan.com/v1/gToH?date={today}"
        r = requests.get(url).json()
        hijri = r["data"]["hijri"]
        st.metric("Hijri Datum", f"{hijri['day']} {hijri['month']['en']} {hijri['year']} AH")
        if hijri["month"]["en"] == "Ramadan":
            st.success("🌙 Ramadan Mubarak!")
    except:
        st.error("Kalender konnte nicht geladen werden.")

# --- TAB 4: Quran Audio Player ---
with tabs[4]:
    st.header("🎧 Quran Audio Player")
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
        st.success("Auto-Wiedergabe läuft…")
        st.session_state.audio_url = audio_url

# Mini Player immer sichtbar
if "audio_url" in st.session_state:
    st.audio(st.session_state.audio_url, format="audio/mp3")
