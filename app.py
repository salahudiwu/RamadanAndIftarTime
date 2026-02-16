import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import pytz
from astral.sun import sun
from astral import LocationInfo
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder

# --- 1. DESIGN & CSS (Anti-Blur) ---
st.set_page_config(page_title="Ramadan Planer", page_icon="🌙")

st.markdown("""
    <style>
    .stApp { background-color: #0a192f; color: #e6f1ff; }
    [data-testid="stStatusWidget"] { display: none; }
    .stTable { background-color: rgba(255, 255, 255, 0.05); border-radius: 10px; }
    div[data-testid="stMetricValue"] {
        color: #ffd700 !important;
        background-color: rgba(255, 255, 255, 0.1);
        padding: 15px; border-radius: 15px; border: 1px solid #ffd700;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. IP-ORTUNG ---
@st.cache_data(ttl=3600)
def get_ip_info():
    try:
        r = requests.get('https://ipapi.co', timeout=5)
        return r.json()
    except:
        return {"city": "Aachen", "country_code": "DE"}

ip_info = get_ip_info()

st.title("🌙 Ramadan Live-Timer")

# Stadt-Eingabe (Automatisch via IP)
city_input = st.text_input("📍 Standort:", value=ip_info.get("city", "Aachen"))

# --- 3. LOGIK & BERECHNUNG ---
try:
    geolocator = Nominatim(user_agent="ramadan_timer_v30")
    location = geolocator.geocode(city_input, language="de")
    
    if location:
        lat, lon = location.latitude, location.longitude
        tf = TimezoneFinder()
        tz_name = tf.timezone_at(lng=lon, lat=lat) or "UTC"
        local_tz = pytz.timezone(tz_name)
        now = datetime.now(local_tz)

        city_info = LocationInfo(city_input, "World", tz_name, lat, lon)
        s = sun(city_info.observer, date=now.date(), tzinfo=local_tz)
        
        # --- OFFLINE-TIMER BOX (JAVASCRIPT) ---
        # Keine doppelten Klammern mehr, damit Python nicht abstürzt
        html_code = """
        <div style="background: rgba(255,255,255,0.1); color: #ffd700; padding: 20px; border-radius: 15px; text-align: center; font-family: sans-serif; border: 2px solid #ffd700;">
            <h3 style="margin:0;">Countdown bis Ramadan 2026</h3>
            <h1 id="timer_val" style="font-size: 2.5rem; margin: 10px 0;">...</h1>
            <p style="margin:0; font-size: 0.8rem; color: #8892b0;">Läuft lokal auf deinem Gerät ✅</p>
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
                    document.getElementById("timer_val").innerHTML = days + "T " + hrs + ":" + min + ":" + sec;
                } else { document.getElementById("timer_val").innerHTML = "🌙 Ramadan Mubarak!"; }
            }
            setInterval(update, 1000); update();
        </script>
        """
        st.components.v1.html(html_code, height=180)

        # Karte
        st.map(pd.DataFrame({'lat': [lat], 'lon': [lon]}))

        # --- GEBETSZEITEN TABELLE (INKL. ASR) ---
        st.subheader("Gebetszeiten für heute")
        # Asr Berechnung (Mitte zwischen Mittag und Sonnenuntergang)
        asr_time = s['noon'] + (s['sunset'] - s['noon']) * 0.5 
        
        prayer_data = [
            ["Fajr (Sahur-Ende)", s['dawn'].strftime("%H:%M")],
            ["Dhuhr", s['noon'].strftime("%H:%M")],
            ["Asr", asr_time.strftime("%H:%M")],
            ["Maghrib (Iftar)", s['sunset'].strftime("%H:%M")],
            ["Isha", s['dusk'].strftime("%H:%M")]
        ]
        
        df_prayers = pd.DataFrame(prayer_data, columns=["Gebet", "Uhrzeit"])
        st.table(df_prayers)
        
        st.write(f"🕒 Aktuelle Zeit vor Ort: {now.strftime('%H:%M:%S')}")
        st.caption(f"📍 {location.address}")

    else:
        st.error("Stadt wurde nicht gefunden. Bitte überprüfe die Schreibweise.")

except Exception as e:
    st.info("Suche Standort...")
