import streamlit as st
import pandas as pd
import requests
import math
from datetime import datetime
import pytz
from astral.sun import sun
from astral import LocationInfo
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
from streamlit_autorefresh import st_autorefresh
from streamlit_lottie import st_lottie

# --- 1. DESIGN ---
st.set_page_config(page_title="Ramadan & Gebetszeiten", page_icon="🌙")
st.markdown("<style>.stApp { background-color: #0a192f; color: #e6f1ff; }[data-testid='stStatusWidget'] { display: none; }</style>", unsafe_allow_html=True)

# --- 2. HILFSFUNKTIONEN ---
def load_lottieurl(url):
    try:
        return requests.get(url).json()
    except:
        return None

def calculate_qibla(lat, lon):
    kaaba_lat, kaaba_lon = math.radians(21.4225), math.radians(39.8262)
    my_lat, my_lon = math.radians(lat), math.radians(lon)
    y = math.sin(kaaba_lon - my_lon)
    x = math.cos(my_lat) * math.tan(kaaba_lat) - math.sin(my_lat) * math.cos(kaaba_lon - my_lon)
    return (math.degrees(math.atan2(y, x)) + 360) % 360

@st.cache_data(ttl=3600)
def get_ip_info():
    try:
        return requests.get('https://ipapi.co').json()
    except:
        return {"city": "Aachen", "country_code": "DE"}

# --- 3. DATEN LADEN ---
st_autorefresh(interval=1000, key="refresh")
ani_lantern = load_lottieurl("https://lottie.host")
ip_info = get_ip_info()

st.title("🌙 Ramadan Live-Timer")
if ani_lantern:
    st_lottie(ani_lantern, height=150)

city_input = st.text_input("📍 Ort anpassen:", value=ip_info.get("city", "Aachen"))

# --- 4. HAUPTLOGIK ---
try:
    geolocator = Nominatim(user_agent="ramadan_v30")
    location = geolocator.geocode(city_input)
    
    if location:
        lat, lon = location.latitude, location.longitude
        tf = TimezoneFinder()
        tz_name = tf.timezone_at(lng=lon, lat=lat)
        local_tz = pytz.timezone(tz_name)
        now = datetime.now(local_tz)

        # Sonnenzeiten
        city_info = LocationInfo(city_input, "World", tz_name, lat, lon)
        s = sun(city_info.observer, date=now.date(), tzinfo=local_tz)
        
        st.write(f"🕒 Zeit vor Ort: **{now.strftime('%H:%M:%S')}**")

        # Timer-Bereich
        col1, col2 = st.columns(2)
        ramadan_start = local_tz.localize(datetime(2026, 2, 18, 0, 0, 0))
        
        if now < ramadan_start:
            diff = ramadan_start - now
            col1.metric("Bis Ramadan", f"{diff.days}T {diff.seconds//3600}h")
        
        if now < s['sunset']:
            d = s['sunset'] - now
            h, rem = divmod(int(d.total_seconds()), 3600)
            col2.metric("Iftar in", f"{h:02d}:{(rem//60)%60:02d}:{rem%60:02d}")
        else:
            col2.success("Iftar war bereits!")

        # Karte & Qibla
        st.map(pd.DataFrame({'lat': [lat], 'lon': [lon]}))
        st.info(f"🕋 Qibla: {calculate_qibla(lat, lon):.1f}°")

        # Tabelle
        st.subheader("Gebetszeiten")
        asr_time = s['noon'] + (s['sunset'] - s['noon']) * 0.5 
        prayers = {
            "Fajr": s['dawn'].strftime("%H:%M"),
            "Dhuhr": s['noon'].strftime("%H:%M"),
            "Asr": asr_time.strftime("%H:%M"),
            "Maghrib (Iftar)": s['sunset'].strftime("%H:%M"),
            "Isha": s['dusk'].strftime("%H:%M")
        }
        st.table(pd.DataFrame(prayers.items(), columns=["Gebet", "Zeit"]))
except:
    st.error("Fehler beim Laden der Daten. Bitte Stadt prüfen.")
