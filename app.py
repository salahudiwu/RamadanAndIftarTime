import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import pytz
from astral.sun import sun
from astral import LocationInfo
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import time

# --- PAGE CONFIG ---
st.set_page_config(page_title="Ramadan & Quran App", page_icon="🌙", layout="centered")

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

# --- Standort / IP ---
@st.cache_data(ttl=3600)
def get_ip_info():
    try:
        r = requests.get('https://ipapi.co', timeout=5)
        return r.json()
    except:
        return {"city": "Aachen"}

ip_info = get_ip_info()
city_input = st.text_input("📍 Standort anpassen:", value=ip_info.get("city", "Aachen"))

# --- Container für dynamische Zeit & Countdown ---
time_container = st.empty()
countdown_container = st.empty()

try:
    geolocator = Nominatim(user_agent="ramadan_app_dynamic")
    location = geolocator.geocode(city_input, language="de")
    if location:
        lat, lon = location.latitude, location.longitude
        tf = TimezoneFinder()
        tz_name = tf.timezone_at(lng=lon, lat=lat) or "UTC"
        local_tz = pytz.timezone(tz_name)

        city_info = LocationInfo(city_input, "World", tz_name, lat, lon)
        s = sun(city_info.observer, date=datetime.now(local_tz).date(), tzinfo=local_tz)
        asr_val = s['noon'] + (s['sunset'] - s['noon']) * 0.5

        ramadan_start = local_tz.localize(datetime(2026, 2, 18, 0, 0, 0))

        while True:
            now_city = datetime.now(local_tz)
            
            # --- Aktuelle Zeit ---
            time_container.markdown(f"🕒 Aktuelle Uhrzeit in {city_input}: **{now_city.strftime('%H:%M:%S')}**")

            # --- Countdown bis Ramadan / Iftar ---
            if now_city < ramadan_start:
                delta = ramadan_start - now_city
                days = delta.days
                hrs, rem = divmod(delta.seconds, 3600)
                mins, secs = divmod(rem, 60)
                countdown_container.info(f"🕌 Countdown bis Ramadan: {days}T {hrs}h {mins}m {secs}s")
            else:
                delta = s['sunset'] - now_city
                if delta.total_seconds() > 0:
                    hrs, rem = divmod(int(delta.total_seconds()), 3600)
                    mins, secs = divmod(rem, 60)
                    countdown_container.success(f"🌙 Zeit bis Iftar: {hrs}h {mins}m {secs}s")
                else:
                    countdown_container.warning("🍽️ Iftar vorbei!")

            time.sleep(1)

except Exception as e:
    st.error("Standort oder Zeit konnte nicht berechnet werden.")
