import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import pytz
from astral.sun import sun
from astral import LocationInfo
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
from deep_translator import GoogleTranslator

# --- PAGE CONFIG ---
st.set_page_config(page_title="Ramadan Community App", page_icon="🌙", layout="centered")

# --- STYLES ---
st.markdown("""
<style>
.block-container {
    padding-top: 5rem !important;
}
</style>
""", unsafe_allow_html=True)

# --- 1. MEHRSPRACHIGKEIT ---
if "lang" not in st.session_state:
    st.session_state.lang = "de"  # Standard-Sprache

def translate(text):
    """Übersetzt Text in die aktuelle Sprache, außer es ist Arabisch."""
    try:
        if any('\u0600' <= c <= '\u06FF' for c in text):
            return text
        return GoogleTranslator(source='auto', target=st.session_state.lang).translate(text)
    except:
        return text

# Sprache auswählen und merken
langs = ["de", "en", "ru", "fr"]
selected_lang = st.selectbox(
    translate("🌐 Sprache wählen:"),
    langs,
    index=langs.index(st.session_state.lang),
    key="lang_selectbox"
)
st.session_state.lang = selected_lang

# --- Tabs ---
tabs = st.tabs([
    translate("📿 Gamification & Dhikr"),
    translate("🌙 Weltweite Iftar Zeiten")
])

# -------------------------------
# Tab 1: Gamification & Dhikr
# -------------------------------
with tabs[0]:
    st.header(translate("📿 Dhikr & Ramadan Streak Tracker"))

    # Dhikr Counter
    if "dhikr_count" not in st.session_state:
        st.session_state.dhikr_count = 0
    if "ramadan_streak" not in st.session_state:
        st.session_state.ramadan_streak = 0
    if "last_day" not in st.session_state:
        st.session_state.last_day = datetime.now().date()

    today = datetime.now().date()
    # Reset streak if a new day
    if today > st.session_state.last_day:
        st.session_state.ramadan_streak += 1
        st.session_state.last_day = today
        st.session_state.dhikr_count = 0

    col1, col2, col3 = st.columns([1,1,1])
    if col1.button(translate("➕ Zählen")):
        st.session_state.dhikr_count += 1
    if col2.button(translate("🔄 Reset Dhikr")):
        st.session_state.dhikr_count = 0
    if col3.button(translate("📅 Reset Streak")):
        st.session_state.ramadan_streak = 0

    st.metric(translate("Dhikr Count"), st.session_state.dhikr_count)
    st.metric(translate("Ramadan Streak"), f"{st.session_state.ramadan_streak} {translate('Tage')}")
    st.progress(min(st.session_state.dhikr_count/100,1.0))

# -------------------------------
# Tab 2: Weltweite Iftar Zeiten
# -------------------------------
with tabs[1]:
    st.header(translate("🌙 Weltweite Iftar Zeiten"))
    st.info(translate("Zeigt Sunset/Iftar Zeiten für ausgewählte Städte"))

    # Beispiel Städte
    cities = {
        "Mekka, Saudi-Arabien": (21.3891, 39.8579),
        "Kairo, Ägypten": (30.0444, 31.2357),
        "Istanbul, Türkei": (41.0082, 28.9784),
        "Berlin, Deutschland": (52.5200, 13.4050),
        "Karabulak, Inguschetien": (43.3130, 44.9080),
        "Antwerpen, Belgien": (51.2194, 4.4025),
        "Houten Castellum, Niederlande": (52.0181, 5.1789),
        "München, Deutschland": (48.1374, 11.5755),
        "Oulu, Finnland": (65.0121, 25.4651)
    }

    selected_city = st.selectbox(translate("Stadt auswählen:"), list(cities.keys()))
    lat, lon = cities[selected_city]

    # Zeitzone ermitteln
    tf = pytz.timezone("UTC")
    try:
        tzf = TimezoneFinder()
        tz_name = tzf.timezone_at(lat=lat, lng=lon) or "UTC"
        tf = pytz.timezone(tz_name)
    except:
        pass

    now = datetime.now(tf)
    sunset = datetime(now.year, now.month, now.day, 18, 0, 0, tzinfo=tf)
    countdown = sunset - now

    if countdown.total_seconds() > 0:
        hrs, rem = divmod(int(countdown.total_seconds()),3600)
        mins, secs = divmod(rem,60)
        st.success(translate(f"🌙 Zeit bis Iftar in {selected_city}: {hrs}h {mins}m {secs}s"))
    else:
        st.warning(translate(f"🍽️ Iftar in {selected_city} vorbei!"))
