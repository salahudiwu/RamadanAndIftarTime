import streamlit as st
from datetime import datetime
import pytz
from astral.sun import sun
from astral import LocationInfo
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder

st.set_page_config(page_title="Ramadan Timer", page_icon="🌙")
st.title("🌙 Ramadan & Iftar Welt-Timer")

city_input = st.text_input("Stadt eingeben:", "Aachen")
geolocator = Nominatim(user_agent="ramadan_app")
tf = TimezoneFinder()

try:
    location = geolocator.geocode(city_input, language="de")
    if location:
        tz_name = tf.timezone_at(lng=location.longitude, lat=location.latitude)
        local_tz = pytz.timezone(tz_name)
        city = LocationInfo(city_input, "Welt", tz_name, location.latitude, location.longitude)

        now = datetime.now(local_tz)
        RAMADAN_START = local_tz.localize(datetime(2026, 2, 18, 0, 0, 0))

        if now < RAMADAN_START:
            diff = RAMADAN_START - now
            st.metric("Countdown bis Ramadan", f"{diff.days}T {diff.seconds//3600}Std {(diff.seconds//60)%60}Min")
        else:
            s_data = sun(city.observer, date=now.date(), tzinfo=local_tz)
            iftar = s_data['sunset']
            st.metric(f"Iftar in {city.name}", iftar.strftime("%H:%M Uhr"))

        if st.button("Aktualisieren"):
            st.rerun()
except:
    st.write("Suche...")
