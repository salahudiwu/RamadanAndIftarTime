import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
from astral.sun import sun
from astral import LocationInfo
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder

st.set_page_config(page_title="Ramadan & Gebetszeiten", page_icon="🌙")
st.title("🌙 Ramadan & Gebetszeiten")

city_input = st.text_input("Stadt eingeben:", "Aachen")

geolocator = Nominatim(user_agent="ramadan_prayer_timer")
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

        # Daten-Berechnung
        city_info = LocationInfo(city_input, "Welt", tz_name, lat, lon)
        s_data = sun(city_info.observer, date=now.date(), tzinfo=local_tz)

        # 1. LIVE-TIMER (Sahur & Iftar)
        ramadan_start = local_tz.localize(datetime(2026, 2, 18, 0, 0, 0))
        
        if now < ramadan_start:
            diff = ramadan_start - now
            st.metric("Countdown bis Ramadan", f"{diff.days}T {diff.seconds//3600}Std")
        else:
            col1, col2 = st.columns(2)
            # Sahur (Fajr/Dawn)
            if now < s_data['dawn']:
                d = s_data['dawn'] - now
                col1.metric("Zeit bis Sahur", f"{d.seconds//3600:02d}:{(d.seconds//60)%60:02d}")
            else:
                col1.write("Sahur vorbei")
            # Iftar (Maghrib/Sunset)
            if now < s_data['sunset']:
                d = s_data['sunset'] - now
                col2.metric("Zeit bis Iftar", f"{d.seconds//3600:02d}:{(d.seconds//60)%60:02d}")
            else:
                col2.success("Guten Appetit!")

        # 2. GEBETSZEITEN TABELLE
        st.subheader("Gebetszeiten für heute")
        
        # Wir berechnen die Standard-Zeiten
        prayer_times = {
            "Fajr (Morgendämmerung)": s_data['dawn'].strftime("%H:%M"),
            "Dhuhr (Mittag)": s_data['noon'].strftime("%H:%M"),
            "Asr (Nachmittag)": (s_data['noon'] + (s_data['sunset'] - s_data['noon']) / 2).strftime("%H:%M"), # Annäherung
            "Maghrib (Abend/Iftar)": s_data['sunset'].strftime("%H:%M"),
            "Isha (Nacht)": s_data['dusk'].strftime("%H:%M")
        }
        
        df_prayers = pd.DataFrame(prayer_times.items(), columns=["Gebet", "Uhrzeit"])
        st.table(df_prayers)

        st.write(f"📍 Standort: {location.address}")

except Exception:
    st.write("Suche läuft...")

if st.button("Aktualisieren 🔄"):
    st.rerun()
