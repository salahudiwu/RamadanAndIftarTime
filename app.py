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

# --- 1. DESIGN: RAMADAN NIGHT STYLE ---
st.markdown(
    """
    <style>
    .stApp {
        background-color: #0a192f;
        color: #e6f1ff;
    }
    div[data-testid="stMetricValue"] {
        color: #ffd700 !important;
        background-color: rgba(255, 255, 255, 0.1);
        padding: 15px;
        border-radius: 15px;
        border: 1px solid #ffd700;
    }
    [data-testid="stStatusWidget"] { display: none; }
    /* Tabelle lesbar machen */
    .stTable { background-color: rgba(255, 255, 255, 0.05); border-radius: 10px; }
    </style>
    """,
    unsafe_allow_html=True
)

# --- 2. HILFSFUNKTIONEN ---
def load_lottieurl(url):
    try:
        r = requests.get(url)
        if r.status_code != 200: return None
        return r.json()
    except:
        return None

def calculate_qibla(lat, lon):
    # Formel zur Berechnung der Qibla-Richtung
    kaaba_lat = math.radians(21.4225)
    kaaba_lon = math.radians(39.8262)
    my_lat = math.radians(lat)
    my_lon = math.radians(lon)
    
    delta_lon = kaaba_lon - my_lon
    y = math.sin(delta_lon)
    x = math.cos(my_lat) * math.tan(kaaba_lat) - math.sin(my_lat) * math.cos(delta_lon)
    qibla_rad = math.atan2(y, x)
    return (math.degrees(qibla_rad) + 360) % 360

@st.cache_data(ttl=3600)
def get_ip_info():
    try:
        data = requests.get('https://ipapi.co').json()
        return {"city": data.get('city', 'Aachen'), "country": data.get('country_code', 'DE')}
    except:
        return {"city": "Aachen", "country": "DE"}

# --- 3. DATEN LADEN ---
# Korrekter Lottie-Link (Wichtig!)
ani_lantern = load_lottieurl("https://lottie.host")

# Live-Update jede Sekunde
st_autorefresh(interval=1000, key="ramadan_live_final")

# --- 4. APP LOGIK ---
ip_info = get_ip_info()
st.title("🌙 Ramadan & Gebetszeiten Live")

if ani_lantern:
    st_lottie(ani_lantern, height=200, key="lantern_final")

city_input = st.text_input("📍 Standort anpassen:", value=ip_info["city"])

geolocator = Nominatim(user_agent="ramadan_pro_final_v20")
tf = TimezoneFinder()

try:
    location = geolocator.geocode(city_input, language="de")
    if location:
        lat, lon = location.latitude, location.longitude
        tz_name = tf.timezone_at(lng=lon, lat=lat)
        local_tz = pytz.timezone(tz_name)
        now = datetime.now(local_tz)

        # Sonnenzeiten
        city_info = LocationInfo(city_input, "World", tz_name, lat, lon)
        s = sun(city_info.observer, date=now.date(), tzinfo=local_tz)
        
        # Ramadan Start 18.02.2026
        ramadan_start = local_tz.localize(datetime(2026, 2, 18, 0, 0, 0))
        
        col1, col2 = st.columns(2)
        
        # Timer 1: Ramadan Countdown
        if now < ramadan_start:
            diff = ramadan_start - now
            h, rem = divmod(int(diff.total_seconds()), 3600)
            m, s_val = divmod(rem, 60)
            col1.metric("Bis Ramadan 2026", f"{diff.days}T {h%24:02d}:{m:02d}:{s_val:02d}")
        
        # Timer 2: Iftar heute
        iftar_time = s['sunset']
        if now < iftar_time:
            d = iftar_time - now
            h, rem = divmod(int(d.total_seconds()), 3600)
            m, s_val = divmod(rem, 60)
            col2.metric("Iftar heute in", f"{h:02d}:{m:02d}:{s_val:02d}")
        else:
            col2.success("Guten Appetit! 🍽️")

        # Karte & Qibla
        st.map(pd.DataFrame({'lat': [lat], 'lon': [lon]}))
        qibla_deg = calculate_qibla(lat, lon)
        st.info(f"🕋 **Qibla-Richtung:** {qibla_deg:.2f}° (von Norden im Uhrzeigersinn)")
        
        # Gebetszeiten Tabelle
        st.subheader("Gebetszeiten")
        asr_time = s['noon'] + (s['sunset'] - s['noon']) * 0.5 
        prayers = {
            "Fajr (Sahur-Ende)": s['dawn'].strftime("%H:%M"),
            "Shuruq": s['sunrise'].strftime("%H:%M"),
            "Dhuhr": s['noon'].strftime("%H:%M"),
            "Asr": asr_time.strftime("%H:%M"),
            "Maghrib (Iftar)": s['sunset'].strftime("%H:%M"),
            "Isha": s['dusk'].strftime("%H:%M")
        }
        st.table(pd.DataFrame(prayers.items(), columns=["Gebet", "Uhrzeit"]))

except Exception as e:
    st.write("Suche Standort...")
