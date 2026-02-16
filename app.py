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

# --- AUTO-REFRESH (Alle 1000ms = 1 Sekunde) ---
st_autorefresh(interval=1000, key="datarefresh")

# --- 1. IP-ORTUNG & SPRACHE ---
@st.cache_data(ttl=3600)
def get_ip_info():
    try:
        data = requests.get('https://ipapi.co').json()
        return {"city": data.get('city', 'Aachen'), "country": data.get('country_code', 'DE')}
    except:
        return {"city": "Aachen", "country": "DE"}

ip_data = get_ip_info()
user_lang = 'en' if ip_data["country"] not in ['DE', 'AT', 'CH'] else 'de'

texts = {
    "de": {"cd": "Bis Ramadan", "iftar": "Zeit bis Iftar", "pray": "Gebetszeiten"},
    "en": {"cd": "To Ramadan", "iftar": "Time to Iftar", "pray": "Prayer Times"}
}
T = texts[user_lang]

st.set_page_config(page_title="Ramadan Live-Timer", page_icon="🌙")
st.title(f"🌙 {T['iftar'] if user_lang == 'en' else 'Ramadan Live-Timer'}")

city_input = st.text_input("Stadt:", value=ip_data["city"])

geolocator = Nominatim(user_agent="ramadan_live_timer_v6")
tf = TimezoneFinder()

try:
    location = geolocator.geocode(city_input, language=user_lang)
    if location:
        lat, lon = location.latitude, location.longitude
        tz_name = tf.timezone_at(lng=lon, lat=lat)
        local_tz = pytz.timezone(tz_name)
        now = datetime.now(local_tz)

        # BERECHNUNGEN
        city_info = LocationInfo(city_input, "World", tz_name, lat, lon)
        s_data = sun(city_info.observer, date=now.date(), tzinfo=local_tz)
        
        # Ramadan Start 18.02.2026
        ramadan_start = local_tz.localize(datetime(2026, 2, 18, 0, 0, 0))

        col1, col2 = st.columns(2)

        # Countdown bis Ramadan mit Sekunden
        diff_ram = ramadan_start - now
        if diff_ram.total_seconds() > 0:
            h, rem = divmod(int(diff_ram.total_seconds()), 3600)
            m, s = divmod(rem, 60)
            col1.metric(T["cd"], f"{diff_ram.days}T {h%24:02d}:{m:02d}:{s:02d}")

        # Iftar Countdown mit Sekunden
        iftar_heute = s_data['sunset']
        if now < iftar_heute:
            d = iftar_heute - now
            h, rem = divmod(int(d.total_seconds()), 3600)
            m, s = divmod(rem, 60)
            col2.metric(T["iftar"], f"{h:02d}:{m:02d}:{s:02d}")
        else:
            col2.success("Iftar vorbei! ✨")

        # Tabelle und Karte
        st.map(pd.DataFrame({'lat': [lat], 'lon': [lon]}))
        
        st.subheader(T["pray"])
        prayers = {
            "Fajr": s_data['dawn'].strftime("%H:%M"),
            "Maghrib (Iftar)": s_data['sunset'].strftime("%H:%M"),
            "Isha": s_data['dusk'].strftime("%H:%M")
        }
        st.table(pd.DataFrame(prayers.items(), columns=["Gebet", "Uhrzeit"]))

except:
    st.write("Suche läuft...")
