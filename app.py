import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import pytz
from astral.sun import sun
from astral import LocationInfo
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder

# 1. DESIGN & ANTI-BLUR
st.set_page_config(page_title="Ramadan App", page_icon="🌙")
st.markdown("<style>.stApp{background-color:#0a192f;color:#e6f1ff;}[data-testid='stStatusWidget']{display:none;}</style>", unsafe_allow_html=True)

# 2. IP-ORTUNG
@st.cache_data(ttl=3600)
def get_ip_info():
    try:
        return requests.get('https://ipapi.co', timeout=5).json()
    except:
        return {"city": "Aachen"}

ip_info = get_ip_info()
st.title("🌙 Ramadan & Quran Live")

# 3. KORAN PLAYER (Neuer, stabiler Server)
st.subheader("🎧 Koran hören")
surah_idx = st.selectbox("Sure wählen (1-114):", range(1, 115), index=0)
formatted_num = f"{surah_idx:03d}"
# Dieser Server (Server 8) ist extrem schnell und erlaubt Streaming
audio_url = f"https://server8.mp3quran.net{formatted_num}.mp3"
st.audio(audio_url) 

# 4. STANDORT & ZEITEN
city_input = st.text_input("📍 Stadt:", value=ip_info.get("city", "Aachen"))

try:
    geolocator = Nominatim(user_agent="ramadan_final_check")
    location = geolocator.geocode(city_input)
    if location:
        lat, lon = location.latitude, location.longitude
        tf = TimezoneFinder()
        tz_name = tf.timezone_at(lng=lon, lat=lat) or "UTC"
        local_tz = pytz.timezone(tz_name)
        now = datetime.now(local_tz)
        city_info = LocationInfo(city_input, "World", tz_name, lat, lon)
        s = sun(city_info.observer, date=now.date(), tzinfo=local_tz)

        # OFFLINE TIMER
        st.components.v1.html(f"""
        <div style="background:rgba(255,255,255,0.1);color:#ffd700;padding:20px;border-radius:15px;text-align:center;font-family:sans-serif;border:2px solid #ffd700;">
            <h1 id="timer" style="font-size:2.5rem;margin:0;">...</h1>
        </div>
        <script>
            var target = new Date("Feb 18, 2026 00:00:00").getTime();
            function up() {{
                var n = new Date().getTime();
                var d = target - n;
                if (d > 0) {{
                    var days = Math.floor(d / 86400000);
                    var hrs = Math.floor((d % 86400000) / 3600000);
                    var min = Math.floor((d % 3600000) / 60000);
                    var sec = Math.floor((d % 60000) / 1000);
                    document.getElementById("timer").innerHTML = days + "T " + hrs + ":" + min + ":" + sec;
                }} else {{ document.getElementById("timer").innerHTML = "🌙 Ramadan Mubarak!"; }}
            }}
            setInterval(up, 1000); up();
        </script>
        """, height=150)

        # GEBETSZEITEN (Asr ist wieder da!)
        st.subheader("Gebetszeiten")
        asr_time = s['noon'] + (s['sunset'] - s['noon']) * 0.5 
        prayer_data = [
            ["Fajr (Sahur)", s['dawn'].strftime("%H:%M")],
            ["Dhuhr", s['noon'].strftime("%H:%M")],
            ["Asr", asr_time.strftime("%H:%M")],
            ["Maghrib (Iftar)", s['sunset'].strftime("%H:%M")],
            ["Isha", s['dusk'].strftime("%H:%M")]
        ]
        st.table(pd.DataFrame(prayer_data, columns=["Gebet", "Zeit"]))
        st.map(pd.DataFrame({'lat': [lat], 'lon': [lon]}))

except:
    st.error("Stadt nicht gefunden.")
