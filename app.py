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

# Taktet die Seite jede Sekunde neu für den Live-Effekt
st_autorefresh(interval=1000, key="countdown")

# --- IP-ORTUNG ---
@st.cache_data(ttl=3600)
def get_ip_info():
    try:
        # Holt Stadt und Land via IP-API
        data = requests.get('https://ipapi.co').json()
        return {
            "city": data.get('city', 'Aachen'), 
            "country": data.get('country_code', 'DE')
        }
    except:
        return {"city": "Berlin", "country": "DE"}

# Daten abrufen
ip_info = get_ip_info()

st.title("🌙 Ramadan & Iftar Live-Timer")

# --- STADT-EINGABE (Mit IP-Stadt als Standardwert) ---
city_input = st.text_input("Stadt:", value=ip_info["city"])

geolocator = Nominatim(user_agent="ramadan_final_timer_v7")
tf = TimezoneFinder()

try:
    location = geolocator.geocode(city_input)
    if location:
        lat, lon = location.latitude, location.longitude
        tz_name = tf.timezone_at(lng=lon, lat=lat)
        local_tz = pytz.timezone(tz_name)
        now = datetime.now(local_tz)

        # Ramadan Start: 18.02.2026
        ramadan_start = local_tz.localize(datetime(2026, 2, 18, 0, 0, 0))
        
        city_info = LocationInfo(city_input, "World", tz_name, lat, lon)
        s_data = sun(city_info.observer, date=now.date(), tzinfo=local_tz)
        iftar_time = s_data['sunset']

        # TIMER LOGIK
        if now < ramadan_start:
            # Phase: Warten auf Ramadan
            diff = ramadan_start - now
            h, rem = divmod(int(diff.total_seconds()), 3600)
            m, s = divmod(rem, 60)
            st.metric("Countdown bis Ramadan-Beginn", f"{diff.days}T {h%24:02d}:{m:02d}:{s:02d}")
            st.info(f"Voraussichtlicher Iftar am ersten Tag: **{iftar_time.strftime('%H:%M')} Uhr**")
        else:
            # Phase: Während Ramadan
            if now < iftar_time:
                diff = iftar_time - now
                h, rem = divmod(int(diff.total_seconds()), 3600)
                m, s = divmod(rem, 60)
                st.metric("Zeit bis Iftar", f"{h:02d}:{m:02d}:{s:02d}")
            else:
                st.success("Guten Appetit! Iftar war bereits.")

        # Karte anzeigen
        st.map(pd.DataFrame({'lat': [lat], 'lon': [lon]}))
        
        # Gebetszeiten Tabelle
        st.subheader("Heutige Zeiten")
        times = {
            "Sahur Ende (Fajr)": s_data['dawn'].strftime("%H:%M"),
            "Iftar (Maghrib)": s_data['sunset'].strftime("%H:%M"),
            "Nacht (Isha)": s_data['dusk'].strftime("%H:%M")
        }
        st.table(pd.DataFrame(times.items(), columns=["Ereignis", "Uhrzeit"]))

except:
    st.write("Suche läuft...")
