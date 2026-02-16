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

# --- 3. KORAN PLAYER ---
ip_info = get_ip_info()
st.title("🌙 Ramadan & Quran Live")

st.subheader("🎧 Koran Rezitation (Mishary Alafasy)")

# Auswahlbox für alle 114 Suren
surah_idx = st.selectbox("Wähle eine Sure aus:", range(1, 115), format_func=lambda x: f"Sure {x}")

# Formatierung für den EveryAyah Server (001, 002...)
formatted_num = f"{surah_idx:03d}"

# Stabiler Server Link
audio_url = f"https://www.everyayah.com{formatted_num}.mp3"

# Player mit Fehlerabfang
try:
    st.audio(audio_url, format="audio/mp3")
    st.caption(f"Quelle: EveryAyah.com | Rezitator: Mishary Rashid Alafasy")
except:
    st.error("Audio konnte nicht geladen werden. Bitte Seite neu laden.")

# --- 4. STANDORT & TIMER ---
city_input = st.text_input("📍 Standort anpassen:", value=ip_info.get("city", "Aachen"))

try:
    geolocator = Nominatim(user_agent="ramadan_quran_final_stable")
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
            <h1 id="cd_val" style="font-size: 2.5rem; margin: 10px 0;">...</h1>
        </div>
        <script>
            var target = new Date("Feb 18, 2026 00:00:00").getTime();
            function update() {
                var n = new Date().getTime();
                var d = target - n;
                if (d > 0) {
                    var days = Math.floor(d / 86400000);
                    var hrs = Math.floor((d % 86400000) / 3600000);
                    var min = Math.floor((d % 3600000) / 60000);
                    var sec = Math.floor((d % 60000) / 1000);
                    document.getElementById("cd_val").innerHTML = days + "T " + hrs + ":" + min + ":" + sec;
                } else { document.getElementById("cd_val").innerHTML = "🌙 Ramadan Mubarak!"; }
            }
            setInterval(update, 1000); update();
        </script>
        """
        st.components.v1.html(html_code, height=160)

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
        
        st.info(f"🕋 Qibla: {calculate_qibla(lat, lon):.1f}° | 🕒 {now.strftime('%H:%M')} Uhr")

    else:
        st.error("Stadt nicht gefunden.")

except Exception as e:
    st.info("Suche Standort...")
