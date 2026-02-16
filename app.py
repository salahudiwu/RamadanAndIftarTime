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
        return {"city": "Aachen"}

ip_info = get_ip_info()
st.title("🌙 Ramadan & Iftar Live-Timer")
city_input = st.text_input("📍 Standort anpassen:", value=ip_info.get("city", "Aachen"))

# --- 3. LOGIK ---
try:
    geolocator = Nominatim(user_agent="ramadan_timer_final_v1")
    location = geolocator.geocode(city_input, language="de")
    
    if location:
        lat, lon = location.latitude, location.longitude
        tf = TimezoneFinder()
        tz_name = tf.timezone_at(lng=lon, lat=lat) or "UTC"
        local_tz = pytz.timezone(tz_name)
        
        # WICHTIG: Aktuelle Zeit der gewählten Stadt
        now_city = datetime.now(local_tz)

        city_info = LocationInfo(city_input, "World", tz_name, lat, lon)
        s = sun(city_info.observer, date=now_city.date(), tzinfo=local_tz)
        
        # Zeit-Strings für JavaScript (ISO-Format mit Zeitzone)
        ramadan_start_js = local_tz.localize(datetime(2026, 2, 18, 0, 0, 0)).isoformat()
        iftar_today_js = s['sunset'].isoformat()
        # Aktuelle Zeit der Stadt mitschicken, damit JS nicht die falsche PC-Zeit nutzt
        now_city_js = now_city.isoformat()

        # --- LIVE JAVASCRIPT TIMER (SYNCHRONISIERT) ---
        html_code = f"""
        <div style="background: rgba(255,255,255,0.1); color: #ffd700; padding: 20px; border-radius: 15px; text-align: center; font-family: sans-serif; border: 2px solid #ffd700;">
            <h3 id="lbl" style="margin:0;">Berechne für {city_input}...</h3>
            <h1 id="tmr" style="font-size: 2.5rem; margin: 10px 0;">...</h1>
        </div>
        <script>
            var rStart = new Date("{ramadan_start_js}").getTime();
            var iToday = new Date("{iftar_today_js}").getTime();
            
            function tick() {{
                // Wir nutzen die aktuelle Zeit basierend auf der berechneten Stadt-Zeit
                var now = new Date().getTime();
                var lbl = document.getElementById("lbl");
                var tmr = document.getElementById("tmr");

                if (now < rStart) {{
                    var d = rStart - now;
                    lbl.innerHTML = "Countdown bis Ramadan (" + "{city_input}" + ")";
                    var days = Math.floor(d / 86400000);
                    var hrs = Math.floor((d % 86400000) / 3600000);
                    var min = Math.floor((d % 3600000) / 60000);
                    var sec = Math.floor((d % 60000) / 1000);
                    tmr.innerHTML = days + "T " + hrs + ":" + min + ":" + sec;
                }} else if (now < iToday) {{
                    var d = iToday - now;
                    lbl.innerHTML = "Zeit bis Iftar in " + "{city_input}";
                    var hrs = Math.floor(d / 3600000);
                    var min = Math.floor((d % 3600000) / 60000);
                    var sec = Math.floor((d % 60000) / 1000);
                    tmr.innerHTML = hrs + "h " + min + "m " + sec + "s";
                }} else {{
                    lbl.innerHTML = "Iftar in " + "{city_input}" + " vorbei!";
                    tmr.innerHTML = "Guten Appetit! 🍽️";
                }}
            }}
            setInterval(tick, 1000); tick();
        </script>
        """
        st.components.v1.html(html_code, height=200)

        # Tabelle & Karte
        st.map(pd.DataFrame({'lat': [lat], 'lon': [lon]}))
        st.subheader("Gebetszeiten (Ortszeit)")
        asr_val = s['noon'] + (s['sunset'] - s['noon']) * 0.5 
        df = pd.DataFrame([
            ["Fajr (Sahur-Ende)", s['dawn'].strftime("%H:%M")],
            ["Dhuhr", s['noon'].strftime("%H:%M")],
            ["Asr", asr_val.strftime("%H:%M")],
            ["Maghrib (Iftar)", s['sunset'].strftime("%H:%M")],
            ["Isha", s['dusk'].strftime("%H:%M")]
        ], columns=["Gebet", "Uhrzeit"])
        st.table(df)
        st.write(f"🕒 Aktuelle Uhrzeit in {city_input}: **{now_city.strftime('%H:%M:%S')}**")

    else:
        st.error("Stadt nicht gefunden.")
except Exception as e:
    st.info("Suche Standort...")


# --- SURAH PLAYER ---

st.markdown("## 🎧 Quran Player")

@st.cache_data(ttl=86400)
def get_surah_list():
    url = "https://api.alquran.cloud/v1/surah"
    r = requests.get(url, timeout=10)
    return r.json()["data"]

surahs = get_surah_list()

options = [f"{s['number']} — {s['englishName']}" for s in surahs]
selected = st.selectbox("Sure auswählen:", options)

surah_num = int(selected.split(" — ")[0])

# komplette Sure als EIN Stream
audio_url = f"https://cdn.islamic.network/quran/audio-surah/128/ar.alafasy/{surah_num}.mp3"

if st.button("▶ Sure starten"):
    st.success("Auto-Wiedergabe läuft…")

    st.audio(audio_url, format="audio/mp3")



# --- 4. QURAN SUREN INTERFACE ---
st.markdown("## 📖 Quran  ")

@st.cache_data(ttl=86400)
def get_surahs():
    url = "https://api.alquran.cloud/v1/surah"
    r = requests.get(url, timeout=10)
    return r.json()["data"]

@st.cache_data(ttl=86400)
def get_surah_text(num):
    url = f"https://api.alquran.cloud/v1/surah/{num}/de.asad"
    r = requests.get(url, timeout=10)
    return r.json()["data"]

try:
    surahs = get_surahs()

    # Dropdown Auswahl
    surah_names = [f"{s['number']}. {s['englishName']}" for s in surahs]
    selected = st.selectbox("Sure auswählen:", surah_names)

    # Nummer extrahieren
    surah_num = int(selected.split(".")[0])

    # Text laden
    surah = get_surah_text(surah_num)

    # Anzeige im passenden Design
    st.markdown(f"""
    <div style="
        background: rgba(255,255,255,0.05);
        padding: 20px;
        border-radius: 15px;
        border: 1px solid #ffd700;
        max-height: 400px;
        overflow-y: auto;">
        <h3 style="color:#ffd700;">{surah['englishName']} ({surah['name']})</h3>
    """, unsafe_allow_html=True)

    for ayah in surah["ayahs"]:
        st.markdown(
            f"<p style='margin-bottom:10px'><b>{ayah['numberInSurah']}.</b> {ayah['text']}</p>",
            unsafe_allow_html=True
        )

    st.markdown("</div>", unsafe_allow_html=True)

except Exception as e:
    st.warning("Suren konnten nicht geladen werden.")


    