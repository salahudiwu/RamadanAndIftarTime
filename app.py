import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import pytz
from astral.sun import sun
from astral import LocationInfo
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder

# --- 1. DESIGN & CSS ---
st.set_page_config(page_title="Ramadan Planer", page_icon="🌙")

st.markdown("""
<style>
.stApp { background-color: #0a192f; color: #e6f1ff; }
[data-testid="stStatusWidget"] { display: none; }
.stTable { background-color: rgba(255,255,255,0.05); border-radius: 10px; }
div[data-testid="stMetricValue"] {
    color: #ffd700 !important;
    background-color: rgba(255,255,255,0.1);
    padding: 15px; border-radius: 15px; border: 1px solid #ffd700;
}
</style>
""", unsafe_allow_html=True)

st.title("🌙 Ramadan & Iftar Timer")

# --- 2. IP Standort ---
@st.cache_data(ttl=3600)
def get_ip_info():
    try:
        r = requests.get("https://ipapi.co", timeout=5)
        return r.json()
    except:
        return {"city": "Berlin", "country_code": "DE"}

ip_info = get_ip_info()

# Stadt Eingabe
city_input = st.text_input("📍 Standort:", value=ip_info.get("city", "Berlin"))

# --- 3. Funktionen ---
def get_location(city_name):
    geolocator = Nominatim(user_agent="ramadan_timer_v2")
    location = geolocator.geocode(city_name)
    if location:
        lat, lon = location.latitude, location.longitude
        tz_name = TimezoneFinder().timezone_at(lng=lon, lat=lat) or "UTC"
        local_tz = pytz.timezone(tz_name)
        return location, lat, lon, local_tz
    return None, None, None, None

def get_prayer_times(lat, lon, city_name, local_tz):
    city_info = LocationInfo(city_name, "World", str(local_tz), lat, lon)
    s = sun(city_info.observer, date=datetime.now(local_tz).date(), tzinfo=local_tz)
    asr_time = s["noon"] + (s["sunset"] - s["noon"]) * 0.5
    prayers = [
        ["Fajr (Sahur-Ende)", s["dawn"].strftime("%H:%M")],
        ["Dhuhr", s["noon"].strftime("%H:%M")],
        ["Asr", asr_time.strftime("%H:%M")],
        ["Maghrib (Iftar)", s["sunset"].strftime("%H:%M")],
        ["Isha", s["dusk"].strftime("%H:%M")]
    ]
    return pd.DataFrame(prayers, columns=["Gebet", "Uhrzeit"]), s["sunset"]

def ramadan_countdown():
    now = datetime.now()
    year = now.year
    ramadan_start = datetime(year, 2, 18)  # Beispiel: 18. Feb 2026
    if now > ramadan_start:
        ramadan_start = datetime(year + 1, 2, 18)
    return ramadan_start

# --- 4. Standort & Gebetszeiten ---
try:
    location, lat, lon, local_tz = get_location(city_input)
    if location:
        now = datetime.now(local_tz)
        st.caption(f"📍 {location.address}")
        st.write(f"🕒 Aktuelle Uhrzeit: {now.strftime('%H:%M:%S')}")

        # Karte
        st.map(pd.DataFrame({'lat': [lat], 'lon': [lon]}))

        # Gebetszeiten
        df_prayers, maghrib_time = get_prayer_times(lat, lon, city_input, local_tz)
        st.subheader("Gebetszeiten für heute")
        st.table(df_prayers)

        # --- IFTAR Countdown ---
        st.subheader("🥘 Countdown bis Iftar")
        maghrib_str = maghrib_time.strftime("%b %d, %Y %H:%M:%S")
        st.components.v1.html(f"""
        <h2 id="iftar">...</h2>
        <script>
        var target = new Date("{maghrib_str}").getTime();
        function updateIftar(){{
            var now = new Date().getTime();
            var diff = target - now;
            if(diff>0){{
                var h=Math.floor((diff % (1000*60*60*24))/(1000*60*60));
                var m=Math.floor((diff % (1000*60*60))/(1000*60));
                var s=Math.floor((diff % (1000*60))/1000);
                document.getElementById("iftar").innerHTML = h+"h "+m+"m "+s+"s";
            }}else{{
                document.getElementById("iftar").innerHTML = "🌙 Iftar!";
            }}
        }}
        setInterval(updateIftar,1000);
        updateIftar();
        </script>
        """, height=100)

        # --- RAMADAN Countdown ---
        st.subheader("🕌 Countdown bis Ramadan")
        ramadan_date = ramadan_countdown().strftime("%b %d, %Y %H:%M:%S")
        st.components.v1.html(f"""
        <h2 id="ramadan">...</h2>
        <script>
        var target = new Date("{ramadan_date}").getTime();
        function updateRamadan(){{
            var now = new Date().getTime();
            var diff = target - now;
            if(diff>0){{
                var d=Math.floor(diff/(1000*60*60*24));
                document.getElementById("ramadan").innerHTML = d+" Tage";
            }}else{{
                document.getElementById("ramadan").innerHTML = "🌙 Ramadan Mubarak!";
            }}
        }}
        setInterval(updateRamadan,1000);
        updateRamadan();
        </script>
        """, height=80)

    else:
        st.error("Stadt wurde nicht gefunden. Bitte überprüfe die Schreibweise.")

except Exception as e:
    st.error(f"Fehler beim Laden: {e}")
