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
    audio { width: 100%; border-radius: 10px; margin: 10px 0; }
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

# --- 3. KORAN PLAYER MIT NAMEN ---
ip_info = get_ip_info()
st.title("🌙 Ramadan & Quran Live")

st.subheader("🎧 Koran Rezitation (Mishary Alafasy)")

# Liste der Suren-Namen (Beispielhaft, die App nutzt Nummern 1-114)
surah_names = [
    "1. Al-Fatihah", "2. Al-Baqarah", "3. Al-Imran", "4. An-Nisa'", "5. Al-Ma'idah", 
    "6. Al-An'am", "7. Al-A'raf", "8. Al-Anfal", "9. At-Tawbah", "10. Yunus",
    "18. Al-Kahf", "36. Ya-Sin", "55. Ar-Rahman", "67. Al-Mulk", "112. Al-Ikhlas", "114. An-Nas"
]

# Auswahlbox (Nummern 1 bis 114)
surah_number = st.selectbox("Wähle eine Sure:", range(1, 115), format_func=lambda x: f"Sure {x}")

formatted_num = f"{surah_number:03d}"
audio_url = f"https://server7.mp3quran.net{formatted_num}.mp3"

st.audio(audio_url, format="audio/mp3")
st.caption(f"Quelle: mp3quran.net | Rezitator: Mishary Rashid Alafasy")

# --- 4. STANDORT & TIMER ---
city_input = st.text_input("📍 Standort anpassen:", value=ip_info.get("city", "Aachen"))

try:
    geolocator = Nominatim(user_agent="ramadan_quran_final_v1")
    location = geolocator.geocode(city_input)
    
    if location:
        lat, lon = location.latitude, location.longitude
        tf = TimezoneFinder()
        tz_name = tf.timezone_at(lng=lon, lat=lat) or "UTC"
        local_tz = pytz.timezone(tz_name)
        now = datetime.now(local_tz)

        city_info = LocationInfo(city_input, "World", tz_name, lat, lon)
        s = sun(city_info.observer, date=now.date(), tzinfo=local_tz)
        
        # OFFLINE-TIMER BOX (JavaScript)
        html_code = """
        <div style="background: rgba(255,255,255,0.1); color: #ffd700; padding: 20px; border-radius: 15px; text-align: center; font-family: sans-serif; border: 2px solid #ffd700;">
            <h3 style="margin:0;">Countdown bis Ramadan 2026</h3>
            <h1 id="cd_timer" style="font-size: 2.5rem; margin: 10px 0;">...</h1>
            <p style="margin:0; font-size: 0.8rem; color: #8892b0;">Berechnet lokal auf deinem Gerät ✅</p>
        </div>
        <script>
            var target = new Date("Feb 18, 2026 00:00:00").getTime();
            function up() {
                var n = new Date().getTime();
                var d = target - n;
                if (d > 0) {
                    var days = Math.floor(d / 86400000);
                    var hrs = Math.floor((d % 86400000) / 3600000);
                    var min = Math.floor((d % 3600000) / 60000);
                    var sec = Math.floor((d % 60000) / 1000);
                    document.getElementById("cd_timer").innerHTML = days + "T " + hrs + ":" + min + ":" + sec;
                } else { document.getElementById("cd_timer").innerHTML = "🌙 Ramadan Mubarak!"; }
            }
            setInterval(up, 1000); up();
        </script>
        """
        st.components.v1.html(html_code, height=180)

        st.map(pd.DataFrame({'lat': [lat], 'lon': [lon]}))

        # GEBETSZEITEN TABELLE
        st.subheader("Gebetszeiten")
        prayer_list = [
            ["Fajr (Sahur-Ende)", s['dawn'].strftime("%H:%M")],
            ["Dhuhr", s['noon'].strftime("%H:%M")],
            ["Maghrib (Iftar)", s['sunset'].strftime("%H:%M")],
            ["Isha", s['dusk'].strftime("%H:%M")]
        ]
        st.table(pd.DataFrame(prayer_list, columns=["Gebet", "Uhrzeit"]))
        
        st.info(f"🕋 Qibla-Richtung: {calculate_qibla(lat, lon):.2f}°")
        st.write(f"🕒 Aktuelle Uhrzeit vor Ort: {now.strftime('%H:%M')}")

    else:
        st.error("Stadt nicht gefunden.")

except Exception:
    st.info("Suche Standort...")
