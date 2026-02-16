import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
from astral.sun import sun
from astral import LocationInfo
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder

st.set_page_config(page_title="Ramadan Timer", page_icon="🌙")
st.title("🌙 Ramadan & Iftar Timer")

city_input = st.text_input("Stadt eingeben (z.B. Aachen, Moskau, New York):", "Aachen")

geolocator = Nominatim(user_agent="ramadan_timer_new")
tf = TimezoneFinder()

try:
    location = geolocator.geocode(city_input, language="de")
    if location:
        lat, lon = location.latitude, location.longitude
        tz_name = tf.timezone_at(lng=lon, lat=lat)
        local_tz = pytz.timezone(tz_name)
        now = datetime.now(local_tz)

        # Karte anzeigen
        st.map(pd.DataFrame({'lat': [lat], 'lon': [lon]}))

        # Ramadan-Berechnung
        ramadan_start = local_tz.localize(datetime(2026, 2, 18, 0, 0, 0))

        if now < ramadan_start:
            diff = ramadan_start - now
            st.metric("Tage bis Ramadan", f"{diff.days}")
            st.info(f"Voraussichtlicher Beginn: 18.02.2026")
        else:
            city_info = LocationInfo(city_input, "Welt", tz_name, lat, lon)
            s = sun(city_info.observer, date=now.date(), tzinfo=local_tz)
            st.metric("Iftar heute um", s['sunset'].strftime("%H:%M Uhr"))

        st.write(f"📍 {location.address}")
except:
    st.write("Suche läuft...")

if st.button("Aktualisieren 🔄"):
    st.rerun()
