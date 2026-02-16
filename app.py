import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder

st.title("🌙 Ramadan Timer & Karte")

city_input = st.text_input("Stadt:", "Aachen")
geolocator = Nominatim(user_agent="ramadan_timer")
tf = TimezoneFinder()

try:
    location = geolocator.geocode(city_input)
    if location:
        # Karte anzeigen
        map_data = pd.DataFrame({'lat': [location.latitude], 'lon': [location.longitude]})
        st.map(map_data)
        st.write(f"Koordinaten: {location.latitude}, {location.longitude}")
except:
    st.write("Suche...")
