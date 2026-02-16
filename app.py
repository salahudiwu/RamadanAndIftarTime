import streamlit as st
import pandas as pd
import requests
import math
from datetime import datetime
import pytz
from astral.sun import sun
from astral import LocationInfo
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder

# --- 1. DESIGN & CSS ---
st.set_page_config(page_title="Ramadan & Quran App", page_icon="🌙")

st.markdown("""
    <style>
    .stApp { background-color: #0a192f; color: #e6f1ff; }
    [data-testid="stStatusWidget"] { display: none; }
    .stTable { background-color: rgba(255, 255, 255, 0.05); border-radius: 10px; }
    audio { width: 100%; border-radius: 15px; margin: 10px 0; border: 2px solid #ffd700; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. HILFSFUNKTIONEN ---
@st.cache_data(ttl=3600)
def get_ip_info():
    try:
        r = requests.get('https://ipapi.co', timeout=5)
        return r.json()
    except:
        return {"city": "Aachen", "country_code": "DE"}

# --- 3. START & KORAN PLAYER ---
ip_info = get_ip_info()
st.title("🌙 Ramadan & Quran Live")

st.subheader("🎧 Koran Rezitation (Mishary Alafasy)")
surah_idx = st.selectbox("Wähle eine Sure (1-114):", range(1, 115), index=0)

# FIX: Wir nutzen EveryAyah mit dreistelliger Formatierung
formatted_num = f"{surah_idx:03d}"
# Dieser Server erlaubt das Abspielen auf externen Webseiten (CORS-friendly)
audio_url = f"https://www.everyayah.com{formatted_num}.mp3"

st.audio(audio_url, format="audio/mp3")
st.caption(f"Quelle: EveryAyah.com | Sure Nr. {surah_idx}")

# --- 4. STANDORT & TIMER ---
city_input = st.text_input("📍 Standort anpassen:", value=ip_info.get("city", "Aachen"))

try:
    geolocator = Nominatim(user_agent="ramadan_app_final_fix")
    location = geolocator.geocode(city_input)
    
    if location:
        lat, lon = location.latitude, location.longitude
        tf = TimezoneFinder()
        tz_name = tf.timezone_at(lng=lon, lat=lat) or "UTC"
        local_tz = pytz.timezone(tz_name)
        now = datetime.now(local_tz)
        city_info = LocationInfo(city_input, "World", tz_name, lat, lon)
        s = sun(city_info.observer, date=now.date(), tzinfo=local_tz)
        
        # OFFLINE-TIMER BOX (JAVASCRIPT)
        st.components.v1.html(f"""
        <div style="background: rgba(255,255,255,0.1); color: #ffd700; padding: 20px; border-radius: 15px; text-align: center; font-family: sans-serif; border: 2px solid #ffd700;">
            <h3 style="margin:0;">Countdown bis Ramadan 2026</h3>
            <h1 id="timer_display" style="font-size: 2.5rem; margin: 10px 0;">...</h1>
        </div>
        <script>
            var target = new Date("Feb 18, 2026 00:00:00").getTime();
            function update_cd() {{
                var n = new Date().getTime();
                var d = target - n;
                if (d > 0) {{
                    var days = Math.floor(d / 86400000);
                    var hrs = Math.floor((d % 86400000) / 3600000);
                    var min = Math.floor((d % 3600000) / 60000);
                    var sec = Math.floor((d % 60000) / 1000);
                    document.getElementById("timer_display").innerHTML = days + "T " + hrs + ":" + min + ":" + sec;
                }} else {{ document.getElementById("timer_display").innerHTML = "🌙 Ramadan Mubarak!"; }}
            }}
            setInterval(update_cd, 1000); update_cd();
        </script>
        """, height=180)

        st.map(pd.DataFrame({'lat': [lat], 'lon': [lon]}))

        # GEBETSZEITEN TABELLE
        st.subheader("Gebetszeiten für heute")
        prayer_list = [
            ["Fajr (Sahur-Ende)", s['dawn'].strftime("%H:%M")],
            ["Dhuhr", s['noon'].strftime("%H:%M")],
            ["Maghrib (Iftar)", s['sunset'].strftime("%H:%M")],
            ["Isha", s['dusk'].strftime("%H:%M")]
        ]
        st.table(pd.DataFrame(prayer_list, columns=["Gebet", "Uhrzeit"]))
        
    else:
        st.error("Stadt nicht gefunden.")
except Exception as e:
    st.info("Suche Standort...")
