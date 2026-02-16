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
st.set_page_config(page_title="Ramadan Live Planer", page_icon="🌙")

st.markdown("""
    <style>
    .stApp { background-color: #0a192f; color: #e6f1ff; }
    [data-testid="stStatusWidget"] { display: none; }
    .stTable { background-color: rgba(255, 255, 255, 0.05); border-radius: 10px; }
    /* Verhindert das Flackern bei Updates */
    .stApp { filter: none !important; opacity: 1 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. STANDORT-LOGIK ---
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

# --- 3. BERECHNUNG ---
try:
    geolocator = Nominatim(user_agent="ramadan_live_v33")
    location = geolocator.geocode(city_input, language="de")
    
    if location:
        lat, lon = location.latitude, location.longitude
        tf = TimezoneFinder()
        tz_name = tf.timezone_at(lng=lon, lat=lat) or "UTC"
        local_tz = pytz.timezone(tz_name)
        now = datetime.now(local_tz)

        city_info = LocationInfo(city_input, "World", tz_name, lat, lon)
        s = sun(city_info.observer, date=now.date(), tzinfo=local_tz)
        
        # Daten für JavaScript
        ramadan_start_js = "Feb 18, 2026 00:00:00"
        iftar_today_js = s['sunset'].strftime("%b %d, %Y %H:%M:%S")

        # --- LIVE JAVASCRIPT COUNTDOWN ---
        # Dieser Teil sorgt für das automatische Ticken OHNE Seite-Neuladen
        html_code = f"""
        <div id="box" style="background: rgba(255,255,255,0.1); color: #ffd700; padding: 20px; border-radius: 15px; text-align: center; font-family: sans-serif; border: 2px solid #ffd700;">
            <h3 id="label" style="margin:0; font-size: 1rem;">Lade Countdown...</h3>
            <h1 id="timer" style="font-size: 2.8rem; margin: 10px 0; font-weight: bold;">...</h1>
        </div>
        <script>
            var ramadanStart = new Date("{ramadan_start_js}").getTime();
            var iftarToday = new Date("{iftar_today_js}").getTime();

            function tick() {{
                var now = new Date().getTime();
                
                if (now < ramadanStart) {{
                    var d = ramadanStart - now;
                    document.getElementById("label").innerHTML = "Countdown bis Ramadan-Beginn";
                    var days = Math.floor(d / 86400000);
                    var hrs = Math.floor((d % 86400000) / 3600000);
                    var min = Math.floor((d % 3600000) / 60000);
                    var sec = Math.floor((d % 60000) / 1000);
                    document.getElementById("timer").innerHTML = days + "T " + hrs + ":" + min + ":" + sec;
                }} else {{
                    if (now < iftarToday) {{
                        var d = iftarToday - now;
                        document.getElementById("label").innerHTML = "Zeit bis Iftar (Fastenbrechen)";
                        var hrs = Math.floor(d / 3600000);
                        var min = Math.floor((d % 3600000) / 60000);
                        var sec = Math.floor((d % 60000) / 1000);
                        document.getElementById("timer").innerHTML = hrs + "h " + min + "m " + sec + "s";
                    } else {{
                        document.getElementById("label").innerHTML = "Iftar für heute beendet";
                        document.getElementById("timer").innerHTML = "Guten Appetit! 🍽️";
                    }}
                }}
            }}
            setInterval(tick, 1000); tick();
        </script>
        """
        st.components.v1.html(html_code, height=200)

        # 4. KARTE & GEBETE
        st.map(pd.DataFrame({'lat': [lat], 'lon': [lon]}))

        st.subheader("Gebetszeiten")
        asr_calc = s['noon'] + (s['sunset'] - s['noon']) * 0.5 
        prayer_data = [
            ["Fajr (Sahur-Ende)", s['dawn'].strftime("%H:%M")],
            ["Dhuhr", s['noon'].strftime("%H:%M")],
            ["Asr", asr_calc.strftime("%H:%M")],
            ["Maghrib (Iftar)", s['sunset'].strftime("%H:%M")],
            ["Isha", s['dusk'].strftime("%H:%M")]
        ]
        st.table(pd.DataFrame(prayer_data, columns=["Gebet", "Uhrzeit"]))
        st.write(f"🕒 Lokale Uhrzeit: **{now.strftime('%H:%M:%S')}**")

    else:
        st.error("Stadt nicht gefunden.")
except Exception as e:
    st.info("Suche Standort...")
