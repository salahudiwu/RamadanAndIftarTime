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

# 1. ANTI-BLUR CSS (Verhindert das Flackern/Verschwimmen beim Update)
st.markdown(
    """
    <style>
    [data-testid="stStatusWidget"] { display: none; }
    .stApp { opacity: 1 !important; filter: none !important; }
    div[data-testid="stMetricValue"] { filter: none !important; opacity: 1 !important; }
    .st-emotion-cache-6q9sum.ef3psqc4 { filter: none !important; }
    </style>
    """,
    unsafe_allow_html=True
)

# 2. LIVE-UPDATE (Alle 1 Sekunde)
st_autorefresh(interval=1000, key="ramadan_timer")

# 3. IP-BASIERTE ORTUNG
@st.cache_data(ttl=3600)
def get_ip_info():
    try:
        data = requests.get('https://ipapi.co').json()
        return {"city": data.get('city', 'Aachen'), "country": data.get('country_code', 'DE')}
    except:
        return {"city": "Aachen", "country": "DE"}

ip_info = get_ip_info()
user_lang = 'en' if ip_info["country"] not in ['DE', 'AT', 'CH'] else 'de'

# Texte
texts = {
    "de": {"title": "🌙 Ramadan & Gebetszeiten Live", "input": "Stadt ändern:", "cd": "Bis Ramadan", "iftar": "Zeit bis Iftar", "pray": "Alle Gebetszeiten"},
    "en": {"title": "🌙 Ramadan & Prayer Times Live", "input": "Change City:", "cd": "Until Ramadan", "iftar": "Time to Iftar", "pray": "All Prayer Times"}
}
T = texts[user_lang]

st.title(T["title"])

# 4. STADT-EINGABE (Mit IP als Standard)
st.markdown(f"#### 📍 Standort: `{ip_info['city']}`")
city_input = st.text_input(T["input"], value=ip_info["city"])

geolocator = Nominatim(user_agent="ramadan_final_app_v10")
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

        # Berechnungen (Astral)
        city_info = LocationInfo(city_input, "World", tz_name, lat, lon)
        s = sun(city_info.observer, date=now.date(), tzinfo=local_tz)
        
        # Ramadan Start 18.02.2026
        ramadan_start = local_tz.localize(datetime(2026, 2, 18, 0, 0, 0))

        col1, col2 = st.columns(2)

        # TIMER 1: Countdown bis Ramadan
        if now < ramadan_start:
            diff = ramadan_start - now
            h, rem = divmod(int(diff.total_seconds()), 3600)
            m, s_val = divmod(rem, 60)
            col1.metric(T["cd"], f"{diff.days}T {h%24:02d}:{m:02d}:{s_val:02d}")
        else:
            col1.info("Ramadan hat begonnen!")

        # TIMER 2: Iftar Countdown
        iftar_heute = s['sunset']
        if now < iftar_heute:
            d = iftar_heute - now
            h, rem = divmod(int(d.total_seconds()), 3600)
            m, s_val = divmod(rem, 60)
            col2.metric(T["iftar"], f"{h:02d}:{m:02d}:{s_val:02d}")
        else:
            col2.success("Guten Appetit! 🍽️")

        # 5. GEBETSZEITEN TABELLE
        st.subheader(T["pray"])
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

except:
    st.write("Suche läuft...")
