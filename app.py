import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import pytz
from astral.sun import sun
from astral import LocationInfo
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder

# --- 1. DESIGN ---
st.set_page_config(page_title="Ramadan & Iftar Timer", page_icon="🌙")
st.markdown("""
    <style>
    .stApp { background-color: #0a192f; color: #e6f1ff; }
    [data-testid="stStatusWidget"] { display: none; }
    .stTable { background-color: rgba(255, 255, 255, 0.05); border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. IP-ORTUNG ---
@st.cache_data(ttl=3600)
def get_ip_info():
    try:
        r = requests.get('https://ipapi.co', timeout=5)
        return r.json()
    except:
        return {"city": "Aachen"}

ip_info = get_ip_info()
st.title("🌙 Ramadan & Iftar Live-Timer")
city_input = st.text_input("📍 Stadt:", value=ip_info.get("city", "Aachen"))

# --- 3. LOGIK ---
try:
    geolocator = Nominatim(user_agent="ramadan_timer_v34")
    location = geolocator.geocode(city_input, language="de")
    
    if location:
        lat, lon = location.latitude, location.longitude
        tf = TimezoneFinder()
        tz_name = tf.timezone_at(lng=lon, lat=lat) or "UTC"
        local_tz = pytz.timezone(tz_name)
        now = datetime.now(local_tz)
        city_info = LocationInfo(city_input, "World", tz_name, lat, lon)
        s = sun(city_info.observer, date=now.date(), tzinfo=local_tz)
        
        # Zeit-Strings für JavaScript
        ramadan_start_js = "2026-02-18T00:00:00"
        iftar_today_js = s['sunset'].isoformat()

        # --- LIVE JAVASCRIPT TIMER (FIXED) ---
        # Wir nutzen hier keine f-Strings mit {}, um Python-Fehler zu vermeiden
        html_code = f"""
        <div style="background: rgba(255,255,255,0.1); color: #ffd700; padding: 20px; border-radius: 15px; text-align: center; font-family: sans-serif; border: 2px solid #ffd700;">
            <h3 id="lbl" style="margin:0;">Lade...</h3>
            <h1 id="tmr" style="font-size: 2.5rem; margin: 10px 0;">...</h1>
        </div>
        <script>
            var rStart = new Date("{ramadan_start_js}").getTime();
            var iToday = new Date("{iftar_today_js}").getTime();

            function tick() {{
                var now = new Date().getTime();
                var lbl = document.getElementById("lbl");
                var tmr = document.getElementById("tmr");

                if (now < rStart) {{
                    var d = rStart - now;
                    lbl.innerHTML = "Countdown bis Ramadan-Beginn";
                    var days = Math.floor(d / 86400000);
                    var hrs = Math.floor((d % 86400000) / 3600000);
                    var min = Math.floor((d % 3600000) / 60000);
                    var sec = Math.floor((d % 60000) / 1000);
                    tmr.innerHTML = days + "T " + hrs + ":" + min + ":" + sec;
                }} else if (now < iToday) {{
                    var d = iToday - now;
                    lbl.innerHTML = "Zeit bis Iftar (Fastenbrechen)";
                    var hrs = Math.floor(d / 3600000);
                    var min = Math.floor((d % 3600000) / 60000);
                    var sec = Math.floor((d % 60000) / 1000);
                    tmr.innerHTML = hrs + "h " + min + "m " + sec + "s";
                }} else {{
                    lbl.innerHTML = "Iftar vorbei!";
                    tmr.innerHTML = "Guten Appetit! 🍽️";
                }}
            }}
            setInterval(tick, 1000); tick();
        </script>
        """
        st.components.v1.html(html_code, height=200)

        # Tabelle & Karte
        st.map(pd.DataFrame({'lat': [lat], 'lon': [lon]}))
        st.subheader("Gebetszeiten")
        asr_val = s['noon'] + (s['sunset'] - s['noon']) * 0.5 
        df = pd.DataFrame([
            ["Fajr", s['dawn'].strftime("%H:%M")],
            ["Dhuhr", s['noon'].strftime("%H:%M")],
            ["Asr", asr_val.strftime("%H:%M")],
            ["Maghrib", s['sunset'].strftime("%H:%M")],
            ["Isha", s['dusk'].strftime("%H:%M")]
        ], columns=["Gebet", "Zeit"])
        st.table(df)

    else:
        st.error("Stadt nicht gefunden.")
except Exception as e:
    st.info("Suche Standort...")
