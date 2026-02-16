import streamlit as st
import pandas as pd
import time
from datetime import datetime
import pytz
from astral.sun import sun
from astral import LocationInfo
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder

st.set_page_config(page_title="Ramadan & Iftar Timer", page_icon="🌙")
st.title("🌙 Ramadan & Iftar Live-Timer")

city_input = st.text_input("Stadt eingeben:", "Aachen")

geolocator = Nominatim(user_agent="ramadan_timer_v3")
tf = TimezoneFinder()

try:
    location = geolocator.geocode(city_input, language="de")
    if location:
        lat, lon = location.latitude, location.longitude
        tz_name = tf.timezone_at(lng=lon, lat=lat)
        local_tz = pytz.timezone(tz_name)
        now = datetime.now(local_tz)

        # Karte
        st.map(pd.DataFrame({'lat': [lat], 'lon': [lon]}))

        # Ramadan-Zeiten 2026
        ramadan_start = local_tz.localize(datetime(2026, 2, 18, 0, 0, 0))
        ramadan_ende = local_tz.localize(datetime(2026, 3, 19, 23, 59, 59))

        # PLATZHALTER FÜR LIVE-TIMER
        timer_placeholder = st.empty()

        # FALL 1: Vor Ramadan
        if now < ramadan_start:
            diff = ramadan_start - now
            tage = diff.days
            stunden, rest = divmod(diff.seconds, 3600)
            minuten, sekunden = divmod(rest, 60)
            timer_placeholder.metric("Countdown bis Ramadan", f"{tage}T {stunden}Std {minuten}Min")
            st.info(f"📍 {location.address}")

        # FALL 2: Während Ramadan (Iftar Countdown)
        elif ramadan_start <= now <= ramadan_ende:
            city_info = LocationInfo(city_input, "Welt", tz_name, lat, lon)
            s_data = sun(city_info.observer, date=now.date(), tzinfo=local_tz)
            iftar_heute = s_data['sunset']
            
            if now < iftar_heute:
                diff = iftar_heute - now
                h, rem = divmod(int(diff.total_seconds()), 3600)
                m, s = divmod(rem, 60)
                timer_placeholder.metric("Zeit bis Iftar heute", f"{h:02d}:{m:02d}:{s:02d}")
                st.write(f"Iftar ist heute um {iftar_heute.strftime('%H:%M')} Uhr")
            else:
                timer_placeholder.success("Afiyet olsun! / Guten Appetit! Der Iftar war bereits.")
        
        else:
            st.write("Ramadan 2026 ist beendet.")

except:
    st.write("Suche läuft...")

# Ein automatisches Refresh-Intervall (optional, alle 60 Sek)
if st.button("Jetzt aktualisieren 🔄"):
    st.rerun()
