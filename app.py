import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import pytz
from astral.sun import sun
from astral import LocationInfo
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder

st.set_page_config(page_title="Ramadan & Iftar Timer", page_icon="🌙")
st.title("🌙 Ramadan Live-Planer")

city_input = st.text_input("Stadt eingeben:", "Aachen")

geolocator = Nominatim(user_agent="ramadan_timer_final")
tf = TimezoneFinder()

try:
    location = geolocator.geocode(city_input, language="de")
    if location:
        lat, lon = location.latitude, location.longitude
        tz_name = tf.timezone_at(lng=lon, lat=lat)
        local_tz = pytz.timezone(tz_name)
        now = datetime.now(local_tz)

        st.map(pd.DataFrame({'lat': [lat], 'lon': [lon]}))

        # Ramadan-Daten 2026
        ramadan_start = local_tz.localize(datetime(2026, 2, 18, 0, 0, 0))
        ramadan_ende = local_tz.localize(datetime(2026, 3, 19, 23, 59, 59))

        # PHASE 1: Vor Ramadan
        if now < ramadan_start:
            diff = ramadan_start - now
            h, rem = divmod(int(diff.total_seconds()), 3600)
            m, s = divmod(rem, 60)
            st.metric("Countdown bis Ramadan", f"{diff.days}T {h%24}Std {m}Min")
            st.info(f"📍 Standort: {location.address}")

        # PHASE 2: Während Ramadan
        elif ramadan_start <= now <= ramadan_ende:
            city_info = LocationInfo(city_input, "World", tz_name, lat, lon)
            s_data = sun(city_info.observer, date=now.date(), tzinfo=local_tz)
            
            # Sahur ist meistens zum Zeitpunkt 'dawn' (Morgendämmerung)
            sahur_heute = s_data['dawn']
            # Iftar ist 'sunset' (Sonnenuntergang)
            iftar_heute = s_data['sunset']
            
            col1, col2 = st.columns(2)

            # Logik für Sahur (Morgen)
            if now < sahur_heute:
                diff = sahur_heute - now
                h, rem = divmod(int(diff.total_seconds()), 3600)
                m, s = divmod(rem, 60)
                col1.metric("Zeit bis Sahur", f"{h:02d}:{m:02d}:{s:02d}")
                col1.write(f"Sahur-Ende: {sahur_heute.strftime('%H:%M')}")
            else:
                col1.write("Sahur ist für heute vorbei.")

            # Logik für Iftar (Abend)
            if now < iftar_heute:
                diff = iftar_heute - now
                h, rem = divmod(int(diff.total_seconds()), 3600)
                m, s = divmod(rem, 60)
                col2.metric("Zeit bis Iftar", f"{h:02d}:{m:02d}:{s:02d}")
                col2.write(f"Iftar: {iftar_heute.strftime('%H:%M')}")
            else:
                col2.success("Guten Appetit beim Iftar!")
        
        else:
            st.write("Ramadan 2026 ist beendet.")

except Exception as e:
    st.write("Suche läuft...")

if st.button("Jetzt aktualisieren 🔄"):
    st.rerun()
