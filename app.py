import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import pytz
from astral.sun import sun
from astral import LocationInfo
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder

# --- PAGE CONFIG ---
st.set_page_config(page_title="Ramadan & Quran App", page_icon="🌙", layout="centered")

# --- DESIGN & CSS ---
st.markdown("""
<style>
.block-container { padding-top: 2rem; }
.stApp { color: #e6f1ff; background: linear-gradient(180deg, #0a192f, #020617); }
[data-testid="stStatusWidget"] { display: none; }
.stTable { background-color: rgba(255, 255, 255, 0.05); border-radius: 10px; }
div[data-testid="stMetricValue"] { color: #ffd700 !important; background-color: rgba(255, 255, 255, 0.1); padding: 15px; border-radius: 15px; border: 1px solid #ffd700; }
</style>
""", unsafe_allow_html=True)

# --- THEME TOGGLE ---
if "theme" not in st.session_state:
    st.session_state.theme = "dark"

def toggle_theme():
    st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"

st.button("🌗 Theme wechseln", on_click=toggle_theme)

if st.session_state.theme == "dark":
    st.markdown("""
    <style>
    .stApp { background: linear-gradient(180deg, #0a192f, #020617); color: #e6f1ff; }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
    .stApp { background: linear-gradient(180deg, #ffffff, #f0f0f0); color: #0a192f; }
    </style>
    """, unsafe_allow_html=True)

# --- TABS ---
tabs = st.tabs([
    "📿 Gamification & Dhikr",
    "🌙 Weltweite Iftar Zeiten & Quran"
])

# -------------------------------
# TAB 1: GAMIFICATION & DHIKR
# -------------------------------
with tabs[0]:
    st.header("📿 Dhikr & Ramadan Streak Tracker")

    # Dhikr Counter
    if "dhikr_count" not in st.session_state: st.session_state.dhikr_count = 0
    if "ramadan_streak" not in st.session_state: st.session_state.ramadan_streak = 0
    if "last_day" not in st.session_state: st.session_state.last_day = datetime.now().date()

    today = datetime.now().date()
    if today > st.session_state.last_day:
        st.session_state.ramadan_streak += 1
        st.session_state.last_day = today
        st.session_state.dhikr_count = 0

    col1, col2, col3 = st.columns([1,1,1])
    if col1.button("➕ Zählen"): st.session_state.dhikr_count += 1
    if col2.button("🔄 Reset Dhikr"): st.session_state.dhikr_count = 0
    if col3.button("📅 Reset Streak"): st.session_state.ramadan_streak = 0

    st.metric("Dhikr Count", st.session_state.dhikr_count)
    st.metric("Ramadan Streak", f"{st.session_state.ramadan_streak} Tage")
    st.progress(min(st.session_state.dhikr_count/100,1.0))

# -------------------------------
# TAB 2: WELTWEITE IFTAR ZEITEN + QURAN
# -------------------------------
with tabs[1]:
    st.header("🌙 Weltweite Iftar Zeiten & Quran")
    st.info("Zeigt Sunset/Iftar Zeiten für ausgewählte Städte")

    # --- IP-ORTUNG & Stadt-Eingabe ---
    @st.cache_data(ttl=3600)
    def get_ip_info():
        try:
            r = requests.get('https://ipapi.co', timeout=5)
            return r.json()
        except:
            return {"city": "Berlin"}

    ip_info = get_ip_info()
    city_input = st.text_input("📍 Standort anpassen:", value=ip_info.get("city", "Berlin"))

    try:
        geolocator = Nominatim(user_agent="ramadan_timer_final_v1")
        location = geolocator.geocode(city_input, language="de")
        
        if location:
            lat, lon = location.latitude, location.longitude
            tf = TimezoneFinder()
            tz_name = tf.timezone_at(lng=lon, lat=lat) or "UTC"
            local_tz = pytz.timezone(tz_name)
            
            now_city = datetime.now(local_tz)
            city_info = LocationInfo(city_input, "World", tz_name, lat, lon)
            s = sun(city_info.observer, date=now_city.date(), tzinfo=local_tz)
            
            # LIVE TIMER mit HTML+JS
            ramadan_start_js = local_tz.localize(datetime(2026, 2, 18, 0, 0, 0)).isoformat()
            iftar_today_js = s['sunset'].isoformat()
            now_city_js = now_city.isoformat()

            html_code = f"""
            <div style="background: rgba(255,255,255,0.1); color: #ffd700; padding: 20px; border-radius: 15px; text-align: center; font-family: sans-serif; border: 2px solid #ffd700;">
                <h3 id="lbl" style="margin:0;">Berechne für {city_input}...</h3>
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
            st.map(pd.DataFrame({'lat':[lat],'lon':[lon]}))

            # Gebetszeiten
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

    # --- QURAN PLAYER ---
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
    audio_url = f"https://cdn.islamic.network/quran/audio-surah/128/ar.alafasy/{surah_num}.mp3"
    if st.button("▶ Sure starten"):
        st.audio(audio_url, format="audio/mp3")

    # --- QURAN TEXT ---
    st.markdown("## 📖 Quran")
    @st.cache_data(ttl=86400)
    def get_surah_text(num):
        url = f"https://api.alquran.cloud/v1/surah/{num}/de.asad"
        r = requests.get(url, timeout=10)
        return r.json()["data"]

    try:
        surah = get_surah_text(surah_num)
        st.markdown(f"<div style='background: rgba(255,255,255,0.05); padding:20px; border-radius:15px; border:1px solid #ffd700; max-height:400px; overflow-y:auto;'>"
                    f"<h3 style='color:#ffd700;'>{surah['englishName']} ({surah['name']})</h3>", unsafe_allow_html=True)
        for ayah in surah["ayahs"]:
            st.markdown(f"<p><b>{ayah['numberInSurah']}.</b> {ayah['text']}</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    except:
        st.warning("Suren konnten nicht geladen werden.")
