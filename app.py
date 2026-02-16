import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import pytz
from astral.sun import sun
from astral import LocationInfo
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder

# 1. DESIGN & CSS (Gegen Blur und für schönes Dunkelblau)
st.set_page_config(page_title="Ramadan Offline-Timer", page_icon="🌙")

st.markdown("""
    <style>
    .stApp { background-color: #0a192f; color: #e6f1ff; }
    [data-testid="stStatusWidget"] { display: none; }
    .stTable { background-color: rgba(255, 255, 255, 0.05); border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 2. IP-ORTUNG (Nur beim ersten Laden nötig)
@st.cache_data(ttl=3600)
def get_ip_info():
    try:
        return requests.get('https://ipapi.co', timeout=5).json()
    except:
        return {"city": "Aachen", "country_code": "DE"}

ip_info = get_ip_info()

st.title("🌙 Ramadan Live-Timer")

# Stadt-Eingabe
city_input = st.text_input("📍 Standort anpassen:", value=ip_info.get("city", "Aachen"))

# 3. STANDORT & GEBETSZEITEN BERECHNEN
try:
    geolocator = Nominatim(user_agent="ramadan_offline_v1")
    location = geolocator.geocode(city_input)
    
    if location:
        lat, lon = location.latitude, location.longitude
        tf = TimezoneFinder()
        tz_name = tf.timezone_at(lng=lon, lat=lat) or "UTC"
        local_tz = pytz.timezone(tz_name)
        now = datetime.now(local_tz)

        # Sonnen-Daten für die Tabelle
        city_info = LocationInfo(city_input, "World", tz_name, lat, lon)
        s = sun(city_info.observer, date=now.date(), tzinfo=local_tz)
        
        # --- OFFLINE-TIMER BOX (JavaScript) ---
        # Dieser Teil berechnet die Sekunden lokal auf dem Gerät des Nutzers!
        st.components.v1.html(
            f"""
            <div id="timer-box" style="background: rgba(255,255,255,0.1); color: #ffd700; padding: 20px; border-radius: 15px; text-align: center; font-family: sans-serif; border: 2px solid #ffd700;">
                <h3 style="margin:0;">Countdown bis Ramadan 2026</h3>
                <h1 id="countdown" style="font-size: 3rem; margin: 10px 0;">Lade...</h1>
                <p style="margin:0; font-size: 0.8rem; color: #8892b0;">Berechnet lokal auf deinem Gerät ✅</p>
            </div>

            <script>
            const target = new Date("Feb 18, 2026 00:00:00").getTime();
            function update() {{
                const now = new Date().getTime();
                const diff = target - now;
                if (diff > 0) {{
                    const d = Math.floor(diff / (1000 * 60 * 60 * 24));
                    const h = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
                    const m = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
                    const s = Math.floor((diff % (1000 * 60)) / 1000);
                    document.getElementById("countdown").innerHTML = d + "T " + h + ":" + m + ":" + s;
                }} else {{
                    document.getElementById("countdown").innerHTML = "🌙 Ramadan Mubarak!";
                }}
            }}
            setInterval(update, 1000);
            update();
            </script>
            """,
            height=200,
        )

        st.map(pd.DataFrame({'lat': [lat], 'lon': [lon]}))

        # Gebetszeiten Tabelle (Wird vom Server berechnet)
        st.subheader("Gebetszeiten für heute")
        prayers = {{
            "Fajr (Sahur)": s['dawn'].strftime("%H:%M"),
            "Dhuhr": s['noon'].strftime("%H:%M"),
            "Maghrib (Iftar)": s['sunset'].strftime("%H:%M"),
            "Isha": s['dusk'].strftime("%H:%M")
        }}
        st.table(pd.DataFrame(prayers.items(), columns=["Gebet", "Uhrzeit"]))
        st.write(f"🕒 Aktuelle Zeit vor Ort: {now.strftime('%H:%M')}")

except Exception as e:
    st.error(f"Suche läuft oder Fehler: {e}")
