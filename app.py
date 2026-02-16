import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
from astral.sun import sun
from astral import LocationInfo
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
from googletrans import Translator

# Initialisierung
translator = Translator()
st.set_page_config(page_title="Ramadan Timer", page_icon="🌙")

# Funktion zum Übersetzen
def auto_translate(text, city_location):
    try:
        # Erkennt das Land aus der Adresse und wählt die Sprache
        # Wir nehmen die Sprache des gefundenen Ortes
        lang_code = city_location.raw.get('address', {}).get('country_code', 'de')
        return translator.translate(text, dest=lang_code).text
    except:
        return text

st.title("🌙 Ramadan & Iftar Timer")
city_input = st.text_input("Stadt / City / المدينة:", "Aachen")

geolocator = Nominatim(user_agent="ramadan_global_app")
tf = TimezoneFinder()

try:
    location = geolocator.geocode(city_input, language="en", addressdetails=True)
    if location:
        lat, lon = location.latitude, location.longitude
        tz_name = tf.timezone_at(lng=lon, lat=lat)
        local_tz = pytz.timezone(tz_name)
        now = datetime.now(local_tz)

        # Karte anzeigen
        st.map(pd.DataFrame({'lat': [lat], 'lon': [lon]}))

        # Texte automatisch übersetzen basierend auf dem Standort
        # Beispiel: Wenn Ort in Marokko -> Arabisch, wenn in USA -> Englisch
        label_days = auto_translate("Days until Ramadan", location)
        label_iftar = auto_translate("Time until Iftar", location)

        ramadan_start = local_tz.localize(datetime(2026, 2, 18, 0, 0, 0))

        if now < ramadan_start:
            diff = ramadan_start - now
            st.metric(label_days, f"{diff.days}")
        else:
            city_info = LocationInfo(city_input, "World", tz_name, lat, lon)
            s = sun(city_info.observer, date=now.date(), tzinfo=local_tz)
            st.metric(label_iftar, s['sunset'].strftime("%H:%M"))

except:
    st.write("...")
