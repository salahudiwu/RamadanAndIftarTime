import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import pytz
from astral.sun import sun
from astral import LocationInfo
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder

# --------------------------------------------------
# DESIGN (Mobile Glass Style)
# --------------------------------------------------
st.set_page_config(page_title="Ramadan Pro", page_icon="🌙")

st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg,#0a192f,#112240);
    color: white;
}
.block-container {
    padding-top: 2rem;
}
.glass {
    background: rgba(255,255,255,0.08);
    padding:20px;
    border-radius:20px;
    backdrop-filter: blur(10px);
    border:1px solid rgba(255,255,255,0.2);
    margin-bottom:20px;
}
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# LANGUAGE SWITCH
# --------------------------------------------------
lang = st.selectbox("Language / Sprache", ["Deutsch", "English"])

def t(de, en):
    return de if lang == "Deutsch" else en

st.title("🌙 Ramadan Pro")

# --------------------------------------------------
# QURAN PLAYER + AUTO NEXT
# --------------------------------------------------
st.markdown('<div class="glass">', unsafe_allow_html=True)
st.subheader(t("🎧 Koran hören", "🎧 Listen to Quran"))

reciters = {
    "Mishary Alafasy": "mishaari_raashid_al_3afaasee",
    "Maher Al-Muaiqly": "maher_almuaiqly",
    "Abdul Basit": "abdulbasit_mujawwad"
}

selected_reciter = st.selectbox(t("Rezitator", "Reciter"), list(reciters.keys()))
surah = st.number_input(t("Sure (1-114)", "Surah (1-114)"), 1, 114, 1)

formatted = f"{int(surah):03d}"
audio_url = f"https://server8.mp3quran.net/{reciters[selected_reciter]}/{formatted}.mp3"

# Auto-Next JS
st.components.v1.html(f"""
<audio id="player" controls autoplay style="width:100%">
  <source src="{audio_url}" type="audio/mpeg">
</audio>

<script>
var player = document.getElementById("player");
player.onended = function() {{
    var next = {surah} + 1;
    if(next <= 114){{
        window.parent.postMessage({{type: "streamlit:setComponentValue", value: next}}, "*");
    }}
}};
</script>
""", height=80)

st.markdown('</div>', unsafe_allow_html=True)

# --------------------------------------------------
# LOCATION + PRAYER TIMES
# --------------------------------------------------
st.markdown('<div class="glass">', unsafe_allow_html=True)
st.subheader(t("📍 Standort & Gebetszeiten", "📍 Location & Prayer Times"))

city = st.text_input(t("Stadt", "City"), "Aachen")

try:
    geolocator = Nominatim(user_agent="ramadan_pro")
    location = geolocator.geocode(city)

    if location:
        lat, lon = location.latitude, location.longitude
        tf = TimezoneFinder()
        tz = tf.timezone_at(lng=lon, lat=lat) or "UTC"
        local_tz = pytz.timezone(tz)
        now = datetime.now(local_tz)

        city_info = LocationInfo(city, "World", tz, lat, lon)
        s = sun(city_info.observer, date=now.date(), tzinfo=local_tz)

        asr = s['noon'] + (s['sunset'] - s['noon']) * 0.5

        df = pd.DataFrame([
            ["Fajr", s['dawn'].strftime("%H:%M")],
            ["Dhuhr", s['noon'].strftime("%H:%M")],
            ["Asr", asr.strftime("%H:%M")],
            ["Maghrib (Iftar)", s['sunset'].strftime("%H:%M")],
            ["Isha", s['dusk'].strftime("%H:%M")]
        ], columns=["Prayer", "Time"])

        st.table(df)

        # IFTAR COUNTDOWN + SOUND
        maghrib = s['sunset'].strftime("%b %d, %Y %H:%M:%S")

        st.markdown("### 🥘 " + t("Countdown bis Iftar", "Countdown to Iftar"))

        st.components.v1.html(f"""
        <h2 id="iftar">...</h2>

        <audio id="adhan">
        <source src="https://server8.mp3quran.net/adhan/adhan.mp3" type="audio/mpeg">
        </audio>

        <script>
        var target = new Date("{maghrib}").getTime();
        var adhanPlayed = false;

        function update() {{
            var now = new Date().getTime();
            var diff = target - now;

            if(diff > 0){{
                var h = Math.floor((diff % (1000*60*60*24))/(1000*60*60));
                var m = Math.floor((diff % (1000*60*60))/(1000*60));
                var s = Math.floor((diff % (1000*60))/1000);
                document.getElementById("iftar").innerHTML = h+"h "+m+"m "+s+"s";
            }} else {{
                document.getElementById("iftar").innerHTML = "🌙 Iftar!";
                if(!adhanPlayed){{
                    document.getElementById("adhan").play();
                    adhanPlayed = true;
                }}
            }}
        }}
        setInterval(update,1000);
        update();
        </script>
        """, height=120)

except:
    st.error("City not found")

st.markdown('</div>', unsafe_allow_html=True)

# --------------------------------------------------
# RAMADAN COUNTDOWN AUTO YEAR
# --------------------------------------------------
st.markdown('<div class="glass">', unsafe_allow_html=True)
st.subheader("🕌 " + t("Countdown bis Ramadan", "Countdown to Ramadan"))

ramadan = datetime(2026, 2, 18)
ramadan_str = ramadan.strftime("%b %d, %Y %H:%M:%S")

st.components.v1.html(f"""
<h2 id="ramadan">...</h2>
<script>
var target2 = new Date("{ramadan_str}").getTime();

function updateR(){{
 var now = new Date().getTime();
 var diff = target2 - now;
 if(diff>0){{
   var d=Math.floor(diff/(1000*60*60*24));
   document.getElementById("ramadan").innerHTML=d+" days";
 }}else{{
   document.getElementById("ramadan").innerHTML="🌙 Ramadan Mubarak!";
 }}
}}
setInterval(updateR,1000);
updateR();
</script>
""", height=100)

st.markdown('</div>', unsafe_allow_html=True) 
