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
    /* Audio Player Gold-Design */
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

def calculate_qibla(lat, lon):
    kaaba_lat, kaaba_lon = math.radians(21.4225), math.radians(39.8262)
    my_lat, my_lon = math.radians(lat), math.radians(lon)
    y = math.sin(kaaba_lon - my_lon)
    x = math.cos(my_lat) * math.tan(kaaba_lat) - math.sin(my_lat) * math.cos(kaaba_lon - my_lon)
    return (math.degrees(math.atan2(y, x)) + 360) % 360

# --- 3. START & KORAN PLAYER ---
ip_info = get_ip_info()
st.title("🌙 Ramadan & Quran Live")

st.subheader("🎧 Koran Rezitation (Mishary Alafasy)")
# Auswahlbox für alle 114 Suren
surah_idx = st.selectbox("Wähle eine Sure (1-114):", range(1, 115), index=0)

# WICHTIG: Dreistellige Nummer für den Server (001, 002...)
formatted_num = f"{surah_idx:03d}"
# Stabiler Audio-Server (HTTPS ist wichtig!)
audio_url = f"https://server7.mp3quran.net{formatted_num}.mp3"

# Player anzeigen
st.audio(audio_url, format="audio/mp3")
st.caption(f"Quelle: mp3quran.net | Rezitator: Mishary Rashid Alafasy")

# --- 4. STANDORT & TIMER ---
city_input = st.text_input("📍 Standort anpassen:", value=ip_info.get("city", "Aachen"))

try:
    geolocator = Nominatim(user_agent="ramadan_quran_final_2026")
    location = geolocator.geocode(city_input)
    
    if location:
        lat, lon = location.latitude, location.longitude
        tf = TimezoneFinder()
        tz_name = tf.timezone_at(lng=lon, lat=lat) or "UTC"
        local_tz = pytz.timezone(tz_name)
        now = datetime.now(local_tz)

        city_info = LocationInfo(city_input, "World", tz_name, lat, lon)
        s = sun(city_info.observer, date=now.date(), tzinfo=local_tz)
        
        # --- OFFLINE-TIMER BOX (JAVASCRIPT) ---
        # Dieser Teil läuft im Browser des Nutzers weiter
        st.components.v1.html(f"""
        <div style="background: rgba(255,255,255,0.1); color: #ffd700; padding: 20px; border-radius: 15px; text-align: center; font-family: sans-serif; border: 2px solid #ffd700;">
            <h3 style="margin:0;">Countdown bis Ramadan 2026</h3>
            <h1 id="timer_display" style="font-size: 2.5rem; margin: 10px 0;">...</h1>
            <p style="margin:0; font-size: 0.8rem; color: #8892b0;">Berechnet lokal auf deinem Gerät ✅</p>
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

        # --- GEBETSZEITEN TABELLE ---
        st.subheader("Gebetszeiten für heute")
        prayer_list = [
            ["Fajr (Sahur-Ende)", s['dawn'].strftime("%H:%M")],
            ["Dhuhr", s['noon'].strftime("%H:%M")],
            ["Maghrib (Iftar)", s['sunset'].strftime("%H:%M")],
            ["Isha", s['dusk'].strftime("%H:%M")]
        ]
        st.table(pd.DataFrame(prayer_list, columns=["Gebet", "Uhrzeit"]))
        
        st.info(f"🕋 Qibla-Richtung: {calculate_qibla(lat, lon):.2f}°")
        st.write(f"🕒 Lokale Uhrzeit: {now.strftime('%H:%M')}")

    else:
        st.error("Stadt nicht gefunden.")

except Exception as e:
    st.info("Suche Standort...")
