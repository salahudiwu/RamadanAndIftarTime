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

# --- 1. DESIGN ---
st.set_page_config(page_title="Ramadan & Quran App", page_icon="🌙")
st.markdown("""
    <style>
    .stApp { background-color: #0a192f; color: #e6f1ff; }
    [data-testid="stStatusWidget"] { display: none; }
    .stTable { background-color: rgba(255, 255, 255, 0.05); border-radius: 10px; }
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

# --- 3. START ---
ip_info = get_ip_info()
st.title("🌙 Ramadan & Quran Live")

# --- FEATURE: ALLE 114 SUREN HÖREN ---
st.subheader("🎧 Koran Rezitation (Mishary Rashid Alafasy)")

# Wir erstellen eine Liste von 1 bis 114
surah_number = st.number_input("Sure wählen (1-114):", min_value=1, max_value=114, value=1)

# Formatierung der Nummer für die URL (z.B. 1 wird zu 001)
formatted_num = f"{surah_number:03d}"

# Audio-Quelle (Server von mp3quran.net)
audio_url = f"https://server7.mp3quran.net{formatted_num}.mp3"
st.audio(audio_url, format="audio/mp3")
st.caption(f"Du hörst gerade Sure Nr. {surah_number}")

# --- STANDORT & TIMER ---
city_input = st.text_input("📍 Stadt eingeben:", value=ip_info.get("city", "Aachen"))

if city_input:
    try:
        geolocator = Nominatim(user_agent="ramadan_quran_final")
        location = geolocator.geocode(city_input, language="de")
        
        if location:
            lat, lon = location.latitude, location.longitude
            tf = TimezoneFinder()
            tz_name = tf.timezone_at(lng=lon, lat=lat) or "UTC"
            local_tz = pytz.timezone(tz_name)
            now = datetime.now(local_tz)

            city_info = LocationInfo(city_input, "World", tz_name, lat, lon)
            s = sun(city_info.observer, date=now.date(), tzinfo=local_tz)
            
            # JavaScript Offline Timer
            html_code = """
            <div style="background: rgba(255,255,255,0.1); color: #ffd700; padding: 20px; border-radius: 15px; text-align: center; font-family: sans-serif; border: 2px solid #ffd700;">
                <h1 id="timer" style="font-size: 2.5rem; margin: 0;">...</h1>
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
                        document.getElementById("timer").innerHTML = days + "T " + hrs + ":" + min + ":" + sec;
                    } else { document.getElementById("timer").innerHTML = "🌙 Ramadan Mubarak!"; }
                }
                setInterval(up, 1000); up();
            </script>
            """
            st.components.v1.html(html_code, height=150)

            st.map(pd.DataFrame({'lat': [lat], 'lon': [lon]}))
            
            # Gebetszeiten
            st.subheader("Gebetszeiten")
            prayer_list = [
                ["Fajr (Sahur-Ende)", s['dawn'].strftime("%H:%M")],
                ["Dhuhr", s['noon'].strftime("%H:%M")],
                ["Maghrib (Iftar)", s['sunset'].strftime("%H:%M")],
                ["Isha", s['dusk'].strftime("%H:%M")]
            ]
            st.table(pd.DataFrame(prayer_list, columns=["Gebet", "Uhrzeit"]))
            st.info(f"🕋 Qibla: {calculate_qibla(lat, lon):.1f}°")

    except:
        st.error("Fehler bei der Standortermittlung.")
