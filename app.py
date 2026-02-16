
import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import pytz
from astral.sun import sun
from astral import LocationInfo
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder

# ------------------------------
# 1️⃣ Spracheinstellungen
# ------------------------------
if "lang" not in st.session_state:
    # Automatische Erkennung beim ersten Laden
    try:
        r = requests.get("https://ipapi.co/json/", timeout=5).json()
        detected_lang = r.get("languages", "de").split(",")[0][:2]
        st.session_state.lang = detected_lang if detected_lang in ["de","en","ar"] else "de"
    except:
        st.session_state.lang = "de"

# Dropdown für manuelle Auswahl
st.session_state.lang = st.selectbox(
    "Sprache / Language / اللغة:",
    options=["de", "en", "ar"],
    index=["de", "en", "ar"].index(st.session_state.lang)
)

lang = st.session_state.lang

import streamlit as st
from googletrans import Translator  # pip install googletrans==4.0.0-rc1
import datetime

# ------------------------------
# 1️⃣ Spracheinstellungen
# ------------------------------
if "lang" not in st.session_state:
    # Standard: automatische Erkennung via IP oder Browser
    st.session_state.lang = "de"  # Standard, kann man noch automatisch setzen

lang = st.session_state.lang

# Dropdown für Sprache (kann jederzeit geändert werden)
st.session_state.lang = st.selectbox(
    "Sprache auswählen / Select Language / اختر اللغة",
    options=["de","en","fr","es","tr","ar","id","ur"],
    index=["de","en","fr","es","tr","ar","id","ur"].index(st.session_state.lang)
)
lang = st.session_state.lang

# ------------------------------
# 2️⃣ Texte
# ------------------------------
ui_texts = {
    "title": "🌙 Ramadan & Iftar App",
    "dhikr_header": "📿 Dhikr & Ramadan Streak Tracker",
    "dhikr_btn": "➕ Zählen",
    "reset_dhikr": "🔄 Reset Dhikr",
    "reset_streak": "📅 Reset Streak",
    "dhikr_count": "Dhikr Count",
    "ramadan_streak": "Ramadan Streak",
    "world_ifatr": "🌙 Weltweite Iftar Zeiten",
    "select_city": "Stadt auswählen:",
    "time_until_ifatr": "Zeit bis Iftar in",
    "iftar_passed": "🍽️ Iftar vorbei!",
    "quran_player": "🎧 Quran Player",
    "quran_text": "📖 Quran",
    "theme_btn": "🌗 Theme wechseln"
}

# ------------------------------
# 3️⃣ Übersetzung (außer Arabisch)
# ------------------------------
translator = Translator()
translated_texts = {}
for key, value in ui_texts.items():
    # Wenn die Zielsprache Arabisch ist, nur UI übersetzen, nicht die Inhalte
    if lang == "ar":
        translated_texts[key] = value
    else:
        # Übersetze alles außer Arabische Schriftzeichen
        translated_texts[key] = translator.translate(value, dest=lang).text

t = translated_texts

# ------------------------------
# 4️⃣ Beispiel Anzeige
# ------------------------------
st.title(t["title"])
st.header(t["dhikr_header"])

if "dhikr_count" not in st.session_state:
    st.session_state.dhikr_count = 0
if "ramadan_streak" not in st.session_state:
    st.session_state.ramadan_streak = 0
if "last_day" not in st.session_state:
    st.session_state.last_day = datetime.datetime.now().date()

today = datetime.datetime.now().date()
if today > st.session_state.last_day:
    st.session_state.ramadan_streak += 1
    st.session_state.last_day = today
    st.session_state.dhikr_count = 0

col1, col2, col3 = st.columns(3)
if col1.button(t["dhikr_btn"]):
    st.session_state.dhikr_count += 1
if col2.button(t["reset_dhikr"]):
    st.session_state.dhikr_count = 0
if col3.button(t["reset_streak"]):
    st.session_state.ramadan_streak = 0

st.metric(t["dhikr_count"], st.session_state.dhikr_count)
st.metric(t["ramadan_streak"], f"{st.session_state.ramadan_streak} Tage")


# ------------------------------
# 3️⃣ Design & Theme
# ------------------------------
st.set_page_config(page_title=t["title"], page_icon="🌙", layout="centered")
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

# Theme Toggle
if "theme" not in st.session_state:
    st.session_state.theme = "dark"
def toggle_theme():
    st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"
st.button(t["theme_btn"], on_click=toggle_theme)
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

# ------------------------------
# 4️⃣ Tabs
# ------------------------------
tabs = st.tabs([t["dhikr_header"], t["world_ifatr"]])

# -------------------------------
# Tab 1: Dhikr & Streak
# -------------------------------
with tabs[0]:
    st.header(t["dhikr_header"])

    if "dhikr_count" not in st.session_state:
        st.session_state.dhikr_count = 0
    if "ramadan_streak" not in st.session_state:
        st.session_state.ramadan_streak = 0
    if "last_day" not in st.session_state:
        st.session_state.last_day = datetime.now().date()

    today = datetime.now().date()
    if today > st.session_state.last_day:
        st.session_state.ramadan_streak += 1
        st.session_state.last_day = today
        st.session_state.dhikr_count = 0

    col1, col2, col3 = st.columns(3)
    if col1.button(t["dhikr_btn"]):
        st.session_state.dhikr_count += 1
    if col2.button(t["reset_dhikr"]):
        st.session_state.dhikr_count = 0
    if col3.button(t["reset_streak"]):
        st.session_state.ramadan_streak = 0

    st.metric(t["dhikr_count"], st.session_state.dhikr_count)
    st.metric(t["ramadan_streak"], f"{st.session_state.ramadan_streak} Tage")
    st.progress(min(st.session_state.dhikr_count/100,1.0))

# -------------------------------
# Tab 2: Weltweite Iftar Zeiten
# -------------------------------
with tabs[1]:
    st.header(t["world_ifatr"])
    st.info("Zeigt Sunset/Iftar Zeiten für ausgewählte Städte")

    cities = {
        "Mekka, Saudi-Arabien": (21.3891, 39.8579),
        "Kairo, Ägypten": (30.0444, 31.2357),
        "Istanbul, Türkei": (41.0082, 28.9784),
        "Berlin, Deutschland": (52.5200, 13.4050)
    }

    selected_city = st.selectbox(t["select_city"], list(cities.keys()))
    lat, lon = cities[selected_city]

    tzf = TimezoneFinder()
    tz_name = tzf.timezone_at(lat=lat, lng=lon) or "UTC"
    tf = pytz.timezone(tz_name)

    now = datetime.now(tf)
    sunset = datetime(now.year, now.month, now.day, 18, 0, 0, tzinfo=tf)
    countdown = sunset - now
    if countdown.total_seconds() > 0:
        hrs, rem = divmod(int(countdown.total_seconds()),3600)
        mins, secs = divmod(rem,60)
        st.success(f"{t['time_until_ifatr']} {selected_city}: {hrs}h {mins}m {secs}s")
    else:
        st.warning(f"{t['iftar_passed']} {selected_city}")

# -------------------------------
# Quran Player & Text bleiben unverändert (arabisch)
# -------------------------------
st.markdown(f"## {t['quran_player']}")
st.markdown(f"## {t['quran_text']}")

