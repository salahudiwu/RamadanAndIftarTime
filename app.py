import streamlit as st
import pandas as pd
import requests
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
    .stApp { opacity: 1 !important; filter: none !important; }
    </style>
    """,
    unsafe_allow_html=True
)

# --- 2. HILFSFUNKTIONEN ---
def load_lottieurl(url):
    r = requests.get(url)
    return r.json() if r.status_code == 200 else None

@st.cache_data(ttl=3600)
def get_ip_info():
    try:
        data = requests.get('https://ipapi.co').json()
        return {"city": data.get('city', 'Aachen'), "country": data.get('country_code', 'DE')}
    except:
        return {"city": "Aachen", "country": "DE"}

# Animation laden (Schwingende Laterne)
ani_lantern = load_lottieurl("https://lottie.host")

# Live-Update jede Sekunde
st_autorefresh(interval=1000, key="ramadan_live")

# --- 3. APP LOGIK ---
ip_info = get_ip_info()
st.title("🌙 Ramadan & Gebetszeiten Live")

# Animation anzeigen
if ani_lantern:
    st_lottie(ani_lantern, height=200, key="lantern")

city_input = st.text_input("📍 Standort anpassen:", value=ip_info["city"])

geolocator = Nominatim(user_agent="ramadan_final_pro_v15")
tf = TimezoneFinder()

try:
    location = geolocator.geocode(city_input)
    if location:
        lat, lon = location.latitude, location.longitude
        tz_name = tf.timezone_at(lng=lon, lat=lat)
        local_tz = pytz.timezone(tz_name)
        now = datetime.now(local_tz)

        # Ramadan Start 18.02.2026
        ramadan_start = local_tz.localize(datetime(2026, 2, 18, 0, 0, 0))
        
        city_info = LocationInfo(city_input, "World", tz_name, lat, lon)
        s = sun(city_info.observer, date=now.date(), tzinfo=local_tz)
        
        # Countdown bis Ramadan
        if now < ramadan_start:
            diff = ramadan_start - now
            h, rem = divmod(int(diff.total_seconds()), 3600)
            m, s_val = divmod(rem, 60)
            st.metric("Countdown bis Ramadan 2026", f"{diff.days}T {h%24:02d}:{m:02d}:{s_val:02d}")
        
        # Iftar Timer (Immer sichtbar zum Testen)
        iftar_time = s['sunset']
        if now < iftar_time:
            d = iftar_time - now
            h, rem = divmod(int(d.total_seconds()), 3600)
            m, s_val = divmod(rem, 60)
            st.metric("Zeit bis Iftar heute", f"{h:02d}:{m:02d}:{s_val:02d}")
        else:
            st.success("Guten Appetit! Iftar war bereits. 🍽️")

        st.map(pd.DataFrame({'lat': [lat], 'lon': [lon]}))
        
        # Gebetszeiten Tabelle
        st.subheader("Gebetszeiten")
        asr_time = s['noon'] + (s['sunset'] - s['noon']) * 0.5 
        prayers = {
            "Fajr (Sahur-Ende)": s['dawn'].strftime("%H:%M"),
            "Dhuhr": s['noon'].strftime("%H:%M"),
            "Asr": asr_time.strftime("%H:%M"),
            "Maghrib (Iftar)": s['sunset'].strftime("%H:%M"),
            "Isha": s['dusk'].strftime("%H:%M")
        }
        st.table(pd.DataFrame(prayers.items(), columns=["Gebet", "Uhrzeit"]))

except:
    st.write("Suche Standort...")
