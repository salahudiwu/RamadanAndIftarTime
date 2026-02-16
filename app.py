import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import pytz
from astral.sun import sun
from astral import LocationInfo
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
from streamlit_autorefresh import st_autorefresh

# Live-Update jede Sekunde
st_autorefresh(interval=1000, key="countdown")

@st.cache_data(ttl=3600)
def get_ip_info():
    try:
        data = requests.get('https://ipapi.co').json()
        return {"city": data.get('city', 'Aachen'), "country": data.get('country_code', 'DE')}
    except:
        return {"city": "Aachen", "country": "DE"}

ip_info = get_ip_info()

st.title("🌙 Ramadan & Gebetszeiten Live")

# Standort-Anzeige & Eingabe
st.markdown(f"#### 📍 Automatisch erkannt: `{ip_info['city']}`")
city_input = st.text_input("Ort anpassen:", value=ip_info["city"])

geolocator = Nominatim(user_agent="ramadan_prayer_full_v9")
tf = TimezoneFinder()

try:
    location = geolocator.geocode(city_input)
    if location:
        lat, lon = location.latitude, location.longitude
        tz_name = tf.timezone_at(lng=lon, lat=lat)
        local_tz = pytz.timezone(tz_name)
        now = datetime.now(local_tz)

        # Ramadan-Logik
        ramadan_start = local_tz.localize(datetime(2026, 2, 18, 0, 0, 0))
        
        city_info = LocationInfo(city_input, "World", tz_name, lat, lon)
        s = sun(city_info.observer, date=now.date(), tzinfo=local_tz)
        
        # --- TIMER ANZEIGE ---
        if now < ramadan_start:
            diff = ramadan_start - now
            h, rem = divmod(int(diff.total_seconds()), 3600)
            m, s_val = divmod(rem, 60)
            st.metric("Countdown bis Ramadan", f"{diff.days}T {h%24:02d}:{m:02d}:{s_val:02d}")
        else:
            iftar_time = s['sunset']
            if now < iftar_time:
                diff = iftar_time - now
                h, rem = divmod(int(diff.total_seconds()), 3600)
                m, s_val = divmod(rem, 60)
                st.metric("Zeit bis Iftar", f"{h:02d}:{m:02d}:{s_val:02d}")
            else:
                st.success("Guten Appetit! Iftar war bereits.")

        st.map(pd.DataFrame({'lat': [lat], 'lon': [lon]}))
        
        # --- ALLE GEBETSZEITEN ---
        st.subheader("Alle Gebetszeiten für heute")
        
        # Berechnung für Asr (Mitte zwischen Mittag und Sonnenuntergang als Annäherung)
        asr_time = s['noon'] + (s['sunset'] - s['noon']) * 0.5 
        
        times = {
            "Fajr (Morgendämmerung / Sahur Ende)": s['dawn'].strftime("%H:%M"),
            "Shuruq (Sonnenaufgang)": s['sunrise'].strftime("%H:%M"),
            "Dhuhr (Mittagsgebet)": s['noon'].strftime("%H:%M"),
            "Asr (Nachmittagsgebet)": asr_time.strftime("%H:%M"),
            "Maghrib (Abendgebet / Iftar)": s['sunset'].strftime("%H:%M"),
            "Isha (Nachtgebet)": s['dusk'].strftime("%H:%M")
        }
        
        df_prayers = pd.DataFrame(times.items(), columns=["Gebet", "Uhrzeit"])
        st.table(df_prayers)

except Exception:
    st.write("Suche Standort...")
