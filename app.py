import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import pytz
from astral.sun import sun
from astral import LocationInfo
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder

# --- 1. AUTOMATISCHE SPRACH-ERKENNUNG ---
@st.cache_data(ttl=3600)
def get_user_lang():
    try:
        # Checkt das Land via IP-Adresse
        data = requests.get('https://ipapi.co').json()
        country = data.get('country_code', 'DE')
        # Wenn nicht DE, AT oder CH, dann Englisch
        return 'en' if country not in ['DE', 'AT', 'CH'] else 'de'
    except:
        return 'de'

user_lang = get_user_lang()

# Wörterbuch für die Sprachen
texts = {
    "de": {
        "title": "🌙 Ramadan & Iftar Timer",
        "input": "Stadt eingeben:",
        "cd": "Countdown bis Ramadan",
        "sahur": "Zeit bis Sahur",
        "iftar": "Zeit bis Iftar",
        "msg": "Voraussichtlicher Beginn: 18.02.2026",
        "finish": "Guten Appetit!"
    },
    "en": {
        "title": "🌙 Ramadan & Iftar Timer",
        "input": "Enter City:",
        "cd": "Countdown to Ramadan",
        "sahur": "Time until Sahur",
        "iftar": "Time until Iftar",
        "msg": "Expected start: 2026-02-18",
        "finish": "Enjoy your meal!"
    }
}
T = texts[user_lang]

# --- 2. APP DESIGN ---
st.set_page_config(page_title="Ramadan Timer", page_icon="🌙")
st.title(T["title"])

city_input = st.text_input(T["input"], "Aachen")

geolocator = Nominatim(user_agent="ramadan_timer_global")
tf = TimezoneFinder()

try:
    location = geolocator.geocode(city_input, language=user_lang)
    if location:
        lat, lon = location.latitude, location.longitude
        tz_name = tf.timezone_at(lng=lon, lat=lat)
        local_tz = pytz.timezone(tz_name)
        now = datetime.now(local_tz)

        # Karte
        st.map(pd.DataFrame({'lat': [lat], 'lon': [lon]}))

        # Ramadan Logik
        ramadan_start = local_tz.localize(datetime(2026, 2, 18, 0, 0, 0))

        if now < ramadan_start:
            diff = ramadan_start - now
            h, rem = divmod(int(diff.total_seconds()), 3600)
            m, s = divmod(rem, 60)
            st.metric(T["cd"], f"{diff.days}T {h%24}Std {m}Min")
            st.info(T["msg"])
        else:
            city_info = LocationInfo(city_input, "World", tz_name, lat, lon)
            s_data = sun(city_info.observer, date=now.date(), tzinfo=local_tz)
            
            # Iftar Check
            if now < s_data['sunset']:
                d = s_data['sunset'] - now
                st.metric(T["iftar"], f"{d.seconds//3600:02d}:{(d.seconds//60)%60:02d}")
            else:
                st.success(T["finish"])
                
        st.write(f"📍 {location.address}")
except:
    st.write("...")

if st.button("🔄"):
    st.rerun()
