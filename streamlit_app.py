# -*- coding: utf-8 -*-
"""Gujarati Vedic Kundali — Streamlit edition.

This UI layer preserves the user's existing Swiss Ephemeris/Lahiri,
whole-sign D1/D9, corrected Vimshottari Dasha and rule-based prediction
engine, while replacing the Gradio UI/map with Streamlit + Folium.

Traditional Jyotish interpretation only; not scientifically validated.
"""

import os
import io
import base64
import html
import tempfile
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import streamlit as st
import pandas as pd
import requests
import swisseph as swe
from timezonefinder import TimezoneFinder
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib import font_manager
matplotlib.use("Agg")
import folium
from streamlit_folium import st_folium
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Existing calculation/chart layer extracted from the user's app.py.
# The generated core intentionally excludes the Gradio UI and duplicated prediction engine.
# ---- Existing calculation/chart layer from the current app.py ----
HEADERS = {
    "User-Agent": "Gujarat-Vedic-Kundali/1.0"
}

SEARCH_URL = "https://nominatim.openstreetmap.org/search"

REVERSE_URL = "https://nominatim.openstreetmap.org/reverse"

tf = TimezoneFinder()

GUJARAT_LAT_MIN = 20.0

GUJARAT_LAT_MAX = 24.7

GUJARAT_LON_MIN = 68.0

GUJARAT_LON_MAX = 74.7

swe.set_sid_mode(
    swe.SIDM_LAHIRI
)

PLANET_FLAGS = (
    swe.FLG_MOSEPH
    | swe.FLG_SPEED
    | swe.FLG_SIDEREAL
)

PLANETS = {

    "Sun": swe.SUN,

    "Moon": swe.MOON,

    "Mars": swe.MARS,

    "Mercury": swe.MERCURY,

    "Jupiter": swe.JUPITER,

    "Venus": swe.VENUS,

    "Saturn": swe.SATURN,

    "Rahu": swe.MEAN_NODE

}

PLANET_GUJARATI = {

    "Sun": "સૂર્ય",

    "Moon": "ચંદ્ર",

    "Mars": "મંગળ",

    "Mercury": "બુધ",

    "Jupiter": "ગુરુ",

    "Venus": "શુક્ર",

    "Saturn": "શનિ",

    "Rahu": "રાહુ",

    "Ketu": "કેતુ"

}

PLANET_SYMBOLS = {

    "Sun": "☉",

    "Moon": "☽",

    "Mars": "♂",

    "Mercury": "☿",

    "Jupiter": "♃",

    "Venus": "♀",

    "Saturn": "♄",

    "Rahu": "☊",

    "Ketu": "☋"

}

RASHIS = [

    ("Mesha", "Aries"),

    ("Vrishabha", "Taurus"),

    ("Mithuna", "Gemini"),

    ("Karka", "Cancer"),

    ("Simha", "Leo"),

    ("Kanya", "Virgo"),

    ("Tula", "Libra"),

    ("Vrishchika", "Scorpio"),

    ("Dhanu", "Sagittarius"),

    ("Makara", "Capricorn"),

    ("Kumbha", "Aquarius"),

    ("Meena", "Pisces")

]

RASHI_GUJARATI = {

    "Mesha": "મેષ",

    "Vrishabha": "વૃષભ",

    "Mithuna": "મિથુન",

    "Karka": "કર્ક",

    "Simha": "સિંહ",

    "Kanya": "કન્યા",

    "Tula": "તુલા",

    "Vrishchika": "વૃશ્ચિક",

    "Dhanu": "ધન",

    "Makara": "મકર",

    "Kumbha": "કુંભ",

    "Meena": "મીન"

}

RASHI_ENGLISH = {

    "Mesha": "Aries",

    "Vrishabha": "Taurus",

    "Mithuna": "Gemini",

    "Karka": "Cancer",

    "Simha": "Leo",

    "Kanya": "Virgo",

    "Tula": "Libra",

    "Vrishchika": "Scorpio",

    "Dhanu": "Sagittarius",

    "Makara": "Capricorn",

    "Kumbha": "Aquarius",

    "Meena": "Pisces"

}

NAKSHATRAS = [

    "Ashwini",

    "Bharani",

    "Krittika",

    "Rohini",

    "Mrigashira",

    "Ardra",

    "Punarvasu",

    "Pushya",

    "Ashlesha",

    "Magha",

    "Purva Phalguni",

    "Uttara Phalguni",

    "Hasta",

    "Chitra",

    "Swati",

    "Vishakha",

    "Anuradha",

    "Jyeshtha",

    "Mula",

    "Purva Ashadha",

    "Uttara Ashadha",

    "Shravana",

    "Dhanishta",

    "Shatabhisha",

    "Purva Bhadrapada",

    "Uttara Bhadrapada",

    "Revati"

]

NAKSHATRA_GUJARATI = {

    "Ashwini": "અશ્વિની",

    "Bharani": "ભરણિ",

    "Krittika": "કૃત્તિકા",

    "Rohini": "રોહિણી",

    "Mrigashira": "મૃગશીર્ષ",

    "Ardra": "આર્દ્રા",

    "Punarvasu": "પુનર્વસુ",

    "Pushya": "પુષ્ય",

    "Ashlesha": "આશ્લેષા",

    "Magha": "મઘા",

    "Purva Phalguni": "પૂર્વ ફાલ્ગુની",

    "Uttara Phalguni": "ઉત્તર ફાલ્ગુની",

    "Hasta": "હસ્ત",

    "Chitra": "ચિત્રા",

    "Swati": "સ્વાતિ",

    "Vishakha": "વિશાખા",

    "Anuradha": "અનુરાધા",

    "Jyeshtha": "જ્યેષ્ઠા",

    "Mula": "મૂળ",

    "Purva Ashadha": "પૂર્વાષાઢા",

    "Uttara Ashadha": "ઉત્તરાષાઢા",

    "Shravana": "શ્રવણ",

    "Dhanishta": "ધનિષ્ઠા",

    "Shatabhisha": "શતભિષા",

    "Purva Bhadrapada": "પૂર્વાભાદ્રપદ",

    "Uttara Bhadrapada": "ઉત્તરાભાદ્રપદ",

    "Revati": "રેવતી"

}

VIMSHOTTARI_SEQUENCE = [

    "Ketu",

    "Venus",

    "Sun",

    "Moon",

    "Mars",

    "Rahu",

    "Jupiter",

    "Saturn",

    "Mercury"

]

DASHA_YEARS = {

    "Ketu": 7,

    "Venus": 20,

    "Sun": 6,

    "Moon": 10,

    "Mars": 7,

    "Rahu": 18,

    "Jupiter": 16,

    "Saturn": 19,

    "Mercury": 17

}

DASHA_GUJARATI = {

    "Ketu": "કેતુ",

    "Venus": "શુક્ર",

    "Sun": "સૂર્ય",

    "Moon": "ચંદ્ર",

    "Mars": "મંગળ",

    "Rahu": "રાહુ",

    "Jupiter": "ગુરુ",

    "Saturn": "શનિ",

    "Mercury": "બુધ"

}

def is_inside_gujarat(lat, lon):

    try:

        lat = float(lat)
        lon = float(lon)

        return (

            GUJARAT_LAT_MIN <= lat <= GUJARAT_LAT_MAX

            and

            GUJARAT_LON_MIN <= lon <= GUJARAT_LON_MAX

        )

    except:

        return False

def get_timezone(lat, lon):

    try:

        timezone = tf.timezone_at(

            lat=float(lat),

            lng=float(lon)

        )

        return timezone or "Asia/Kolkata"

    except:

        return "Asia/Kolkata"

def reverse_location(lat, lon):

    try:

        response = requests.get(

            REVERSE_URL,

            params={

                "lat": float(lat),

                "lon": float(lon),

                "format": "json",

                "addressdetails": 1

            },

            headers=HEADERS,

            timeout=15

        )

        response.raise_for_status()

        data = response.json()

        address = data.get(
            "address",
            {}
        )

        parts = []

        for value in [

            address.get(
                "village",
                ""
            ),

            address.get(
                "town",
                ""
            ),

            address.get(
                "city",
                ""
            ),

            address.get(
                "state_district",
                ""
            ),

            address.get(
                "state",
                ""
            )

        ]:

            if value and value not in parts:

                parts.append(value)


        if parts:

            return ", ".join(parts)


        return (
            f"પસંદ કરેલ સ્થળ "
            f"({float(lat):.6f}, "
            f"{float(lon):.6f})"
        )


    except:

        return (
            f"પસંદ કરેલ સ્થળ "
            f"({float(lat):.6f}, "
            f"{float(lon):.6f})"
        )

def search_location(place):

    if not place or not place.strip():

        return (

            None,

            None,

            "Asia/Kolkata",

            "",

            "⚠️ કૃપા કરીને ગુજરાતનું જન્મસ્થળ દાખલ કરો."

        )


    query = place.strip()


    if "gujarat" not in query.lower():

        query += ", Gujarat, India"


    try:

        response = requests.get(

            SEARCH_URL,

            params={

                "q": query,

                "format": "json",

                "addressdetails": 1,

                "limit": 10,

                "countrycodes": "in"

            },

            headers=HEADERS,

            timeout=15

        )

        response.raise_for_status()

        results = response.json()


    except Exception as e:

        return (

            None,

            None,

            "Asia/Kolkata",

            "",

            f"❌ શોધમાં ભૂલ: {e}"

        )


    for item in results:

        try:

            lat = float(
                item["lat"]
            )

            lon = float(
                item["lon"]
            )

            display_name = item.get(
                "display_name",
                ""
            )


            if (

                is_inside_gujarat(
                    lat,
                    lon
                )

                and

                "gujarat"
                in display_name.lower()

            ):

                timezone = get_timezone(
                    lat,
                    lon
                )


                return (

                    lat,

                    lon,

                    timezone,

                    display_name,

                    f"""
### 📍 જન્મસ્થળ મળ્યું

**{display_name}**

**અક્ષાંશ:** `{lat:.6f}`

**રેખાંશ:** `{lon:.6f}`

**સમય ક્ષેત્ર:** `{timezone}`
"""

                )


        except:

            pass


    return (

        None,

        None,

        "Asia/Kolkata",

        "",

        "❌ યોગ્ય ગુજરાતનું સ્થળ મળ્યું નથી."

    )

def confirm_location(lat, lon):

    if lat is None or lon is None:

        return (

            "⚠️ કૃપા કરીને પહેલા નકશા પર જન્મસ્થળ પસંદ કરો.",

            "",

            "Asia/Kolkata"

        )


    try:

        lat = float(lat)

        lon = float(lon)

    except:

        return (

            "❌ અયોગ્ય અક્ષાંશ/રેખાંશ.",

            "",

            "Asia/Kolkata"

        )


    if not is_inside_gujarat(
        lat,
        lon
    ):

        return (

            "❌ કૃપા કરીને ગુજરાતની અંદરનું સ્થળ પસંદ કરો.",

            "",

            "Asia/Kolkata"

        )


    timezone = get_timezone(
        lat,
        lon
    )


    place = reverse_location(
        lat,
        lon
    )


    return (

        f"""
### ✅ જન્મસ્થળની પુષ્ટિ થઈ

**સ્થળ:** {place}

**અક્ષાંશ:** `{lat:.6f}`

**રેખાંશ:** `{lon:.6f}`

**સમય ક્ષેત્ર:** `{timezone}`
""",

        place,

        timezone

    )

def get_rashi(longitude):

    longitude = longitude % 360

    index = int(
        longitude // 30
    )

    rashi_name = RASHIS[index][0]

    english_name = RASHIS[index][1]

    degree = longitude % 30

    return (

        index,

        rashi_name,

        english_name,

        degree

    )

def get_nakshatra(longitude):

    longitude = longitude % 360

    nakshatra_size = (
        360 / 27
    )

    pada_size = (
        nakshatra_size / 4
    )

    index = min(

        26,

        int(
            longitude /
            nakshatra_size
        )

    )

    position = (

        longitude
        -
        index * nakshatra_size

    )

    pada = min(

        4,

        int(
            position /
            pada_size
        ) + 1

    )

    return (

        index,

        NAKSHATRAS[index],

        pada

    )

def get_nakshatra_lord(
    longitude
):

    index, _, _ = get_nakshatra(
        longitude
    )

    return VIMSHOTTARI_SEQUENCE[
        index % 9
    ]

def navamsa_sign(longitude):

    rashi_index = int(

        (longitude % 360)
        // 30

    )

    degree = longitude % 30

    part = min(

        8,

        int(
            degree /
            (30 / 9)
        )

    )


    if rashi_index in [
        0,
        3,
        6,
        9
    ]:

        start = rashi_index


    elif rashi_index in [
        1,
        4,
        7,
        10
    ]:

        start = (
            rashi_index + 8
        ) % 12


    else:

        start = (
            rashi_index + 4
        ) % 12


    return (
        start + part
    ) % 12

def format_degree(
    degree
):

    degree = degree % 30

    d = int(degree)

    minutes_float = (
        degree - d
    ) * 60

    m = int(minutes_float)

    seconds = (
        minutes_float - m
    ) * 60

    return (

        f"{d:02d}° "
        f"{m:02d}' "
        f"{seconds:05.2f}\""

    )

def make_indian_datetime(

    day,
    month,
    year,
    hour,
    minute,
    ampm

):

    day = int(day)

    month = int(month)

    year = int(year)

    hour = int(hour)

    minute = int(minute)


    if ampm == "AM":

        hour24 = (

            0

            if hour == 12

            else hour

        )

    else:

        hour24 = (

            12

            if hour == 12

            else hour + 12

        )


    return datetime(

        year,

        month,

        day,

        hour24,

        minute

    )

def get_julian_day(
    utc_datetime
):

    hour_decimal = (

        utc_datetime.hour

        +

        utc_datetime.minute / 60

        +

        utc_datetime.second / 3600

    )


    return swe.julday(

        utc_datetime.year,

        utc_datetime.month,

        utc_datetime.day,

        hour_decimal,

        swe.GREG_CAL

    )

def calculate_planets(
    jd_ut
):

    rows = []


    for planet_name, planet_id in PLANETS.items():

        values, return_code = swe.calc_ut(

            jd_ut,

            planet_id,

            PLANET_FLAGS

        )


        longitude = (
            values[0] % 360
        )

        speed = values[3]


        (

            rashi_index,

            rashi_name,

            english_name,

            degree

        ) = get_rashi(
            longitude
        )


        (

            nak_index,

            nak_name,

            pada

        ) = get_nakshatra(
            longitude
        )


        rows.append({

            "Planet":
                planet_name,

            "Longitude":
                longitude,

            "Rashi_Index":
                rashi_index,

            "Rashi":
                rashi_name,

            "Sign":
                english_name,

            "Degree_in_Rashi":
                degree,

            "Nakshatra":
                nak_name,

            "Pada":
                pada,

            "Nakshatra_Lord":
                get_nakshatra_lord(
                    longitude
                ),

            "Retrograde":
                speed < 0

        })


    # --------------------------------------------------------
    # KETU
    # --------------------------------------------------------

    rahu = next(

        r
        for r in rows
        if r["Planet"] == "Rahu"

    )


    ketu_longitude = (

        rahu["Longitude"]
        + 180

    ) % 360


    (

        rashi_index,

        rashi_name,

        english_name,

        degree

    ) = get_rashi(
        ketu_longitude
    )


    (

        nak_index,

        nak_name,

        pada

    ) = get_nakshatra(
        ketu_longitude
    )


    rows.append({

        "Planet":
            "Ketu",

        "Longitude":
            ketu_longitude,

        "Rashi_Index":
            rashi_index,

        "Rashi":
            rashi_name,

        "Sign":
            english_name,

        "Degree_in_Rashi":
            degree,

        "Nakshatra":
            nak_name,

        "Pada":
            pada,

        "Nakshatra_Lord":
            get_nakshatra_lord(
                ketu_longitude
            ),

        "Retrograde":
            True

    })


    return rows

def calculate_ascendant(

    jd_ut,

    latitude,

    longitude

):

    cusps, ascmc = swe.houses_ex(

        jd_ut,

        float(latitude),

        float(longitude),

        b"W",

        swe.FLG_SIDEREAL

    )


    longitude_asc = (
        ascmc[0] % 360
    )


    (

        rashi_index,

        rashi_name,

        english_name,

        degree

    ) = get_rashi(
        longitude_asc
    )


    (

        nak_index,

        nak_name,

        pada

    ) = get_nakshatra(
        longitude_asc
    )


    return {

        "Longitude":
            longitude_asc,

        "Rashi_Index":
            rashi_index,

        "Rashi":
            rashi_name,

        "Sign":
            english_name,

        "Degree_in_Rashi":
            degree,

        "Nakshatra":
            nak_name,

        "Pada":
            pada,

        "Nakshatra_Lord":
            get_nakshatra_lord(
                longitude_asc
            )

    }

def add_years_approx(
    dt,
    years
):

    return dt + timedelta(
        days=float(years) * 365.2425
    )

def get_antardasha_years(
    mahadasha_years,
    antardasha_lord
):

    return (
        float(mahadasha_years)
        *
        float(DASHA_YEARS[antardasha_lord])
        / 120.0
    )

def find_birth_antardasha(
    mahadasha_lord,
    mahadasha_total_years,
    elapsed_fraction
):

    md_index = (
        VIMSHOTTARI_SEQUENCE.index(
            mahadasha_lord
        )
    )


    # Complete Antardasha sequence for this Mahadasha

    sequence = [

        VIMSHOTTARI_SEQUENCE[
            (md_index + j) % 9
        ]

        for j in range(9)

    ]


    # Amount of the Mahadasha already elapsed

    elapsed_md_years = (

        float(mahadasha_total_years)
        *
        float(elapsed_fraction)

    )


    accumulated_years = 0.0


    for j, ad_lord in enumerate(sequence):

        ad_years = get_antardasha_years(

            mahadasha_total_years,

            ad_lord

        )


        next_accumulated = (

            accumulated_years
            +
            ad_years

        )


        # ----------------------------------------------------
        # This is the Antardasha active at birth
        # ----------------------------------------------------

        if (
            elapsed_md_years
            <
            next_accumulated
        ):

            elapsed_inside_ad = (

                elapsed_md_years
                -
                accumulated_years

            )


            remaining_inside_ad = (

                ad_years
                -
                elapsed_inside_ad

            )


            return {

                "index":
                    j,

                "lord":
                    ad_lord,

                "total_years":
                    ad_years,

                "elapsed_years":
                    elapsed_inside_ad,

                "remaining_years":
                    remaining_inside_ad

            }


        accumulated_years = (
            next_accumulated
        )


    # --------------------------------------------------------
    # Numerical safety fallback
    # --------------------------------------------------------

    last_lord = sequence[-1]

    last_years = get_antardasha_years(

        mahadasha_total_years,

        last_lord

    )


    return {

        "index":
            8,

        "lord":
            last_lord,

        "total_years":
            last_years,

        "elapsed_years":
            last_years,

        "remaining_years":
            0.0

    }

def calculate_vimshottari(

    moon_longitude,

    birth_dt,

    mahadasha_count=9

):

    # --------------------------------------------------------
    # GET NAKSHATRA
    # --------------------------------------------------------

    (
        nak_index,
        nak_name,
        nak_pada

    ) = get_nakshatra(
        moon_longitude
    )


    # --------------------------------------------------------
    # NAKSHATRA SIZE
    # --------------------------------------------------------

    nak_size = (
        360.0 / 27.0
    )


    # --------------------------------------------------------
    # POSITION INSIDE CURRENT NAKSHATRA
    # --------------------------------------------------------
    #
    # 0.0 = beginning of Nakshatra
    # 1.0 = end of Nakshatra
    #
    # --------------------------------------------------------

    position_in_nakshatra = (
        moon_longitude % nak_size
    )


    elapsed = (

        position_in_nakshatra
        /
        nak_size

    )


    # Safety clamp

    elapsed = max(
        0.0,
        min(
            float(elapsed),
            1.0
        )
    )


    # --------------------------------------------------------
    # FIRST MAHADASHA LORD
    # --------------------------------------------------------

    first_lord = (

        VIMSHOTTARI_SEQUENCE[
            nak_index % 9
        ]

    )


    # --------------------------------------------------------
    # FIRST MAHADASHA TOTAL DURATION
    # --------------------------------------------------------

    first_total_years = (

        DASHA_YEARS[
            first_lord
        ]

    )


    # --------------------------------------------------------
    # FIRST MAHADASHA ELAPSED / REMAINING
    # --------------------------------------------------------

    first_elapsed = (

        first_total_years
        *
        elapsed

    )


    first_remaining = (

        first_total_years
        *
        (1.0 - elapsed)

    )


    # --------------------------------------------------------
    # SAFETY
    # --------------------------------------------------------

    first_remaining = max(
        0.0,
        first_remaining
    )


    # ========================================================
    # MAHADASHA TABLE
    # ========================================================

    mahadashas = []


    start = birth_dt


    first_index = (

        VIMSHOTTARI_SEQUENCE.index(
            first_lord
        )

    )


    for i in range(
        mahadasha_count
    ):

        lord = (

            VIMSHOTTARI_SEQUENCE[
                (first_index + i) % 9
            ]

        )


        # ----------------------------------------------------
        # First Mahadasha = only remaining balance
        # ----------------------------------------------------

        if i == 0:

            years = first_remaining


        else:

            years = DASHA_YEARS[
                lord
            ]


        end = add_years_approx(

            start,

            years

        )


        mahadashas.append({

            "Lord":
                lord,

            "Start":
                start,

            "End":
                end,

            "Years":
                years

        })


        start = end


    # ========================================================
    # ANTARDASHA TABLE
    # ========================================================

    ad_rows = []


    for md_index_number, md in enumerate(
        mahadashas
    ):

        md_lord = md[
            "Lord"
        ]

        md_start = md[
            "Start"
        ]

        md_years = md[
            "Years"
        ]


        md_sequence_index = (

            VIMSHOTTARI_SEQUENCE.index(
                md_lord
            )

        )


        # ====================================================
        # FIRST MAHADASHA — SPECIAL HANDLING
        # ====================================================

        if md_index_number == 0:

            # ------------------------------------------------
            # Determine the Antardasha active AT BIRTH
            # ------------------------------------------------

            active_ad = find_birth_antardasha(

                mahadasha_lord=
                    md_lord,

                mahadasha_total_years=
                    first_total_years,

                elapsed_fraction=
                    elapsed

            )


            active_index = active_ad[
                "index"
            ]


            active_lord = active_ad[
                "lord"
            ]


            # ------------------------------------------------
            # The active Antardasha starts at BIRTH
            # with only its remaining duration.
            # ------------------------------------------------

            ad_start = md_start


            active_remaining_years = (
                active_ad[
                    "remaining_years"
                ]
            )


            ad_end = add_years_approx(

                ad_start,

                active_remaining_years

            )


            ad_rows.append({

                "Mahadasha":
                    md_lord,

                "Antardasha":
                    active_lord,

                "Start":
                    ad_start.strftime(
                        "%d-%m-%Y"
                    ),

                "End":
                    ad_end.strftime(
                        "%d-%m-%Y"
                    )

            })


            ad_start = ad_end


            # ------------------------------------------------
            # Continue with subsequent Antardashas
            # ------------------------------------------------

            for j in range(
                active_index + 1,
                9
            ):

                ad_lord = (

                    VIMSHOTTARI_SEQUENCE[
                        (
                            md_sequence_index
                            +
                            j
                        ) % 9
                    ]

                )


                ad_years = (

                    get_antardasha_years(

                        first_total_years,

                        ad_lord

                    )

                )


                ad_end = add_years_approx(

                    ad_start,

                    ad_years

                )


                ad_rows.append({

                    "Mahadasha":
                        md_lord,

                    "Antardasha":
                        ad_lord,

                    "Start":
                        ad_start.strftime(
                            "%d-%m-%Y"
                        ),

                    "End":
                        ad_end.strftime(
                            "%d-%m-%Y"
                        )

                })


                ad_start = ad_end


        # ====================================================
        # ALL SUBSEQUENT MAHADASHA
        # ====================================================

        else:

            ad_start = md_start


            for j in range(9):

                ad_lord = (

                    VIMSHOTTARI_SEQUENCE[
                        (
                            md_sequence_index
                            +
                            j
                        ) % 9
                    ]

                )


                ad_years = (

                    get_antardasha_years(

                        md_years,

                        ad_lord

                    )

                )


                ad_end = add_years_approx(

                    ad_start,

                    ad_years

                )


                ad_rows.append({

                    "Mahadasha":
                        md_lord,

                    "Antardasha":
                        ad_lord,

                    "Start":
                        ad_start.strftime(
                            "%d-%m-%Y"
                        ),

                    "End":
                        ad_end.strftime(
                            "%d-%m-%Y"
                        )

                })


                ad_start = ad_end


    # ========================================================
    # DATAFRAME
    # ========================================================

    ad_df = pd.DataFrame(
        ad_rows
    )


    # ========================================================
    # COMPLETION MESSAGE
    # ========================================================

    print(
        "✅ Vimshottari Dasha loaded."
    )

    print(
        "✅ First Mahadasha Antardasha position corrected."
    )

    print(
        "   First Mahadasha :",
        first_lord
    )

    print(
        "   Nakshatra       :",
        nak_name
    )

    print(
        "   Pada             :",
        nak_pada
    )

    print(
        "   Elapsed fraction :",
        round(
            elapsed,
            6
        )
    )

    print(
        "   MD elapsed years:",
        round(
            first_elapsed,
            6
        )
    )

    print(
        "   MD balance years:",
        round(
            first_remaining,
            6
        )
    )


    # ========================================================
    # RETURN EXACTLY THE SAME VALUES AS ORIGINAL CELL
    # ========================================================

    return (

        ad_df,

        nak_name,

        nak_pada,

        first_lord

    )

# ============================================================
# FONT CONFIGURATION — Gujarati + English safe rendering
# ============================================================
# Keep DejaVu Sans as the global/default font. Gujarati text is
# rendered explicitly with Noto Sans Gujarati so Matplotlib never
# falls back to a font without Gujarati glyphs.

matplotlib.rcParams["font.family"] = "DejaVu Sans"
matplotlib.rcParams["font.sans-serif"] = ["DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False

all_fonts = font_manager.findSystemFonts()

def _find_font_by_name(*needles, prefer_regular=False, prefer_bold=False):
    candidates = []
    for path in all_fonts:
        name = os.path.basename(path).lower()
        if all(n.lower() in name for n in needles):
            candidates.append(path)
    if prefer_bold:
        for path in candidates:
            if "bold" in os.path.basename(path).lower():
                return path
    if prefer_regular:
        for path in candidates:
            n = os.path.basename(path).lower()
            if "regular" in n and "bold" not in n:
                return path
    return candidates[0] if candidates else None

# Robust search for Noto Sans Gujarati.
# FIRST look inside the GitHub/Streamlit project so the app does not
# depend on a system-installed Gujarati font.
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_FONT_DIR = os.path.join(PROJECT_DIR, "fonts")

project_regular = os.path.join(PROJECT_FONT_DIR, "NotoSansGujarati-Regular.ttf")
project_bold = os.path.join(PROJECT_FONT_DIR, "NotoSansGujarati-Bold.ttf")

if os.path.exists(project_regular):
    GUJARATI_FONT = project_regular
else:
    GUJARATI_FONT = _find_font_by_name(
        "notosansgujarati", prefer_regular=True
    )

if os.path.exists(project_bold):
    GUJARATI_BOLD_FONT = project_bold
else:
    GUJARATI_BOLD_FONT = _find_font_by_name(
        "notosansgujarati", prefer_bold=True
    )

# Explicit common fallback paths used by Streamlit/Linux images.
if GUJARATI_FONT is None:
    for candidate in (
        "/usr/share/fonts/truetype/noto/NotoSansGujarati-Regular.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansGujarati-Regular.ttf",
    ):
        if os.path.exists(candidate):
            GUJARATI_FONT = candidate
            break

if GUJARATI_BOLD_FONT is None:
    for candidate in (
        "/usr/share/fonts/truetype/noto/NotoSansGujarati-Bold.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansGujarati-Bold.ttf",
    ):
        if os.path.exists(candidate):
            GUJARATI_BOLD_FONT = candidate
            break

if GUJARATI_FONT is None:
    raise RuntimeError(
        "Noto Sans Gujarati regular font was not found. "
        "Install/copy NotoSansGujarati-Regular.ttf before starting the app."
    )

# If a separate bold file is unavailable, use the regular font rather
# than constructing a FontProperties object with fname=None.
if GUJARATI_BOLD_FONT is None:
    GUJARATI_BOLD_FONT = GUJARATI_FONT

# Register fonts with Matplotlib.
font_manager.fontManager.addfont(GUJARATI_FONT)
if GUJARATI_BOLD_FONT != GUJARATI_FONT:
    font_manager.fontManager.addfont(GUJARATI_BOLD_FONT)

ENGLISH_FONT = font_manager.findfont(
    font_manager.FontProperties(family="DejaVu Sans")
)

# IMPORTANT: explicit file-based FontProperties.
GUJ_FONT = font_manager.FontProperties(fname=GUJARATI_FONT)
GUJ_FONT_BOLD = font_manager.FontProperties(fname=GUJARATI_BOLD_FONT)
ENG_FONT = font_manager.FontProperties(fname=ENGLISH_FONT)
ENG_FONT_BOLD = font_manager.FontProperties(fname=ENGLISH_FONT)

print("==============================================")
print("FONT CONFIGURATION")
print("==============================================")
print("Global font     : DejaVu Sans")
print("Gujarati font   :", GUJARATI_FONT)
print("Gujarati bold   :", GUJARATI_BOLD_FONT)
print("English font    :", ENGLISH_FONT)
print("Gujarati font OK:", os.path.exists(GUJARATI_FONT))
print("==============================================")

def north_indian_centers():

    return {

        1: (0.50, 0.75),

        2: (0.25, 0.875),

        3: (0.125, 0.625),

        4: (0.25, 0.375),

        5: (0.125, 0.125),

        6: (0.25, 0.125),

        7: (0.50, 0.25),

        8: (0.75, 0.125),

        9: (0.875, 0.125),

        10: (0.75, 0.375),

        11: (0.875, 0.625),

        12: (0.75, 0.875)

    }

def draw_north_indian(

    ax,
    rows,
    asc,
    title,
    navamsa=False

):

    # --------------------------------------------------------
    # AXIS
    # --------------------------------------------------------

    ax.set_xlim(
        0,
        1
    )

    ax.set_ylim(
        0,
        1
    )

    ax.set_aspect(
        "equal"
    )

    ax.axis(
        "off"
    )


    # --------------------------------------------------------
    # OUTER SQUARE
    # --------------------------------------------------------

    ax.add_patch(

        patches.Rectangle(

            (0, 0),

            1,

            1,

            fill=False,

            linewidth=2

        )

    )


    # --------------------------------------------------------
    # MAIN DIAGONALS
    # --------------------------------------------------------

    ax.plot(

        [0, 1],

        [0, 1],

        linewidth=1.5

    )


    ax.plot(

        [0, 1],

        [1, 0],

        linewidth=1.5

    )


    # --------------------------------------------------------
    # INNER DIAGONALS
    # --------------------------------------------------------

    ax.plot(

        [0.5, 0],

        [0, 0.5],

        linewidth=1.2

    )


    ax.plot(

        [0.5, 0],

        [1, 0.5],

        linewidth=1.2

    )


    ax.plot(

        [0.5, 1],

        [0, 0.5],

        linewidth=1.2

    )


    ax.plot(

        [0.5, 1],

        [1, 0.5],

        linewidth=1.2

    )


    centers = north_indian_centers()


    # ========================================================
    # DETERMINE STARTING SIGN
    # ========================================================

    if navamsa:

        lagna_sign = navamsa_sign(
            asc["Longitude"]
        )

    else:

        lagna_sign = asc[
            "Rashi_Index"
        ]


    # ========================================================
    # DISPLAY 12 HOUSES
    # ========================================================

    for house in range(
        1,
        13
    ):

        sign_index = (

            lagna_sign
            + house
            - 1

        ) % 12


        x, y = centers[
            house
        ]


        rashi_internal = RASHIS[
            sign_index
        ][0]


        rashi_gujarati = (
            RASHI_GUJARATI[
                rashi_internal
            ]
        )


        # ----------------------------------------------------
        # HOUSE NUMBER
        # ----------------------------------------------------

        ax.text(

            x,

            y + 0.12,

            f"ભાવ {house}",

            ha="center",

            va="center",

            fontsize=8,

            fontproperties=GUJ_FONT_BOLD

        )


        # ----------------------------------------------------
        # RASHI NAME
        # ----------------------------------------------------

        ax.text(

            x,

            y + 0.035,

            rashi_gujarati,

            ha="center",

            va="center",

            fontsize=10,

            fontproperties=GUJ_FONT_BOLD

        )


    # ========================================================
    # GROUP PLANETS BY HOUSE
    # ========================================================

    grouped = {

        h: []

        for h in range(
            1,
            13
        )

    }


    for row in rows:

        if navamsa:

            house = (

                (
                    row[
                        "Navamsa_Index"
                    ]

                    -

                    lagna_sign

                ) % 12

            ) + 1

        else:

            house = row[
                "House"
            ]


        planet_gujarati = (
            PLANET_GUJARATI[
                row["Planet"]
            ]
        )


        # ----------------------------------------------------
        # RETROGRADE
        # ----------------------------------------------------

        if row.get(
            "Retrograde",
            False
        ):

            planet_gujarati += " (વક્રી)"


        grouped[
            house
        ].append(
            planet_gujarati
        )


    # ========================================================
    # DISPLAY PLANETS
    # ========================================================

    for house, planets in grouped.items():

        if not planets:

            continue


        x, y = centers[
            house
        ]


        planet_text = "\n".join(
            planets
        )


        ax.text(

            x,

            y - 0.105,

            planet_text,

            ha="center",

            va="center",

            fontsize=8.5,

            linespacing=0.95,

            fontproperties=GUJ_FONT_BOLD

        )


    # ========================================================
    # CHART TITLE
    # ========================================================

    ax.set_title(

        title,

        fontsize=14,

        fontweight="bold",

        pad=12,

        fontproperties=GUJ_FONT_BOLD

    )

def create_kundali_png(

    rows,
    asc,
    name,
    birth_text

):

    path = os.path.join(

        tempfile.gettempdir(),

        "gujarati_vedic_kundali.png"

    )


    # --------------------------------------------------------
    # CREATE FIGURE
    # --------------------------------------------------------

    fig, axes = plt.subplots(

        1,

        2,

        figsize=(15, 8)

    )


    # ========================================================
    # D1 — જન્મ રાશિ
    # ========================================================

    draw_north_indian(

        axes[0],

        rows,

        asc,

        "જન્મ રાશિ કુંડળી",

        navamsa=False

    )


    # ========================================================
    # D9 — નવાંશ
    # ========================================================

    draw_north_indian(

        axes[1],

        rows,

        asc,

        "નવાંશ કુંડળી",

        navamsa=True

    )


    # ========================================================
    # TOP GUJARATI TITLE
    # ========================================================

    fig.text(

        0.50,

        0.965,

        "વૈદિક જન્મ કુંડળી",

        ha="center",

        va="center",

        fontsize=18,

        fontproperties=GUJ_FONT_BOLD

    )


    # ========================================================
    # NAME
    # ========================================================
    #
    # IMPORTANT:
    # Name is deliberately rendered using English font.
    #
    # If the entered name is Gujarati, we will later make
    # the name font selectable separately.
    #


    if name:

        fig.text(

            0.50,

            0.935,

            str(name),

            ha="center",

            va="center",

            fontsize=13,

            fontproperties=ENG_FONT_BOLD

        )


    # ========================================================
    # DATE / TIME
    # ========================================================

    if birth_text:

        fig.text(

            0.50,

            0.905,

            str(birth_text),

            ha="center",

            va="center",

            fontsize=10,

            fontproperties=ENG_FONT

        )


    # ========================================================
    # LAYOUT
    # ========================================================

    plt.tight_layout(

        rect=[

            0,

            0,

            1,

            0.88

        ]

    )


    # ========================================================
    # SAVE IMAGE
    # ========================================================

    fig.savefig(

        path,

        dpi=200,

        bbox_inches="tight",

        facecolor="white"

    )


    plt.close(
        fig
    )


    return path

def make_planet_table(rows):

    data = []


    for r in rows:

        data.append({

            "ગ્રહ":
                PLANET_GUJARATI[
                    r["Planet"]
                ],

            "રેખાંશ":
                round(
                    r["Longitude"],
                    6
                ),

            "રાશિ":
                RASHI_GUJARATI[
                    r["Rashi"]
                ],

            "અંશ":
                format_degree(
                    r["Degree_in_Rashi"]
                ),

            "નક્ષત્ર":
                NAKSHATRA_GUJARATI[
                    r["Nakshatra"]
                ],

            "પાદ":
                r["Pada"],

            "નક્ષત્ર સ્વામી":
                PLANET_GUJARATI.get(

                    r[
                        "Nakshatra_Lord"
                    ],

                    r[
                        "Nakshatra_Lord"
                    ]

                ),

            "ભાવ":
                r["House"],

            "નવાંશ":
                RASHI_GUJARATI[
                    RASHIS[
                        r[
                            "Navamsa_Index"
                        ]
                    ][0]
                ],

            "ગતિ":
                (
                    "વક્રી"
                    if r["Retrograde"]
                    else "માર્ગી"
                )

        })


    return pd.DataFrame(
        data
    )
# ---- End calculation/chart layer ----

# Existing rule-based engine supplied by the user.
from prediction_engine import (
    generate_rule_based_predictions,
    _make_prediction_dataframe,
    _prediction_report,
)

# ------------------------------------------------------------------
# STREAMLIT PAGE CONFIG
# ------------------------------------------------------------------
st.set_page_config(
    page_title="ગુજરાતી વૈદિક જન્મ કુંડળી",
    page_icon="🪔",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .main-title {font-size: 2.0rem; font-weight: 800; text-align:center; margin-bottom:0.2rem;}
    .sub-title {text-align:center; color:#666; margin-bottom:1rem;}
    .section-box {padding:0.7rem 1rem; border-radius:0.7rem; background:#faf7ff; border:1px solid #e5d8f2; margin:0.5rem 0 1rem 0;}
    div[data-testid="stMetricValue"] {font-size:1.25rem;}
    </style>
    """,
    unsafe_allow_html=True,
)

# ------------------------------------------------------------------
# FOLIUM / LOCATION HELPERS
# ------------------------------------------------------------------
def make_gujarat_map(lat=None, lon=None):
    center = [22.2587, 71.1924]
    m = folium.Map(location=center, zoom_start=7, control_scale=True)
    folium.TileLayer(
        tiles="OpenStreetMap",
        name="OpenStreetMap",
        control=True,
    ).add_to(m)
    folium.Rectangle(
        bounds=[[GUJARAT_LAT_MIN, GUJARAT_LON_MIN], [GUJARAT_LAT_MAX, GUJARAT_LON_MAX]],
        color="#7b1fa2",
        weight=2,
        fill=False,
        dash_array="6 5",
        tooltip="ગુજરાત — પસંદગી વિસ્તાર",
    ).add_to(m)
    if lat is not None and lon is not None:
        folium.Marker(
            [lat, lon],
            tooltip="પસંદ કરેલ જન્મસ્થળ",
            popup=f"જન્મસ્થળ<br>અક્ષાંશ: {lat:.6f}<br>રેખાંશ: {lon:.6f}",
        ).add_to(m)
    return m


def search_and_store_place(place):
    lat, lon, tz, display, status = search_location(place)
    if lat is None or lon is None:
        return False, status
    st.session_state["latitude"] = float(lat)
    st.session_state["longitude"] = float(lon)
    st.session_state["timezone"] = tz or "Asia/Kolkata"
    st.session_state["confirmed_place"] = display
    return True, status


def confirm_and_store(lat, lon):
    status, place, tz = confirm_location(lat, lon)
    if place:
        st.session_state["latitude"] = float(lat)
        st.session_state["longitude"] = float(lon)
        st.session_state["timezone"] = tz
        st.session_state["confirmed_place"] = place
    return status

# ------------------------------------------------------------------
# KUNDALI CALCULATION WRAPPER
# ------------------------------------------------------------------
def calculate_kundali(name, day, month, year, hour, minute, ampm, place, lat, lon, timezone):
    local_naive = make_indian_datetime(day, month, year, hour, minute, ampm)
    timezone_name = timezone or "Asia/Kolkata"
    local_dt = local_naive.replace(tzinfo=ZoneInfo(timezone_name))
    utc_dt = local_dt.astimezone(ZoneInfo("UTC"))
    jd_ut = get_julian_day(utc_dt)

    rows = calculate_planets(jd_ut)
    asc = calculate_ascendant(jd_ut, float(lat), float(lon))

    for row in rows:
        rashi_index = get_rashi(row["Longitude"])[0]
        row["Rashi_Index"] = rashi_index
        row["Navamsa_Index"] = navamsa_sign(row["Longitude"])
        row["House"] = ((rashi_index - asc["Rashi_Index"]) % 12) + 1

    moon = next(r for r in rows if r["Planet"] == "Moon")
    dasha_df, moon_nak, moon_pada, first_lord = calculate_vimshottari(
        moon["Longitude"], local_dt
    )

    predictions = generate_rule_based_predictions(
        rows, asc, dasha_df, birth_dt=local_dt
    )
    prediction_df = _make_prediction_dataframe(predictions)
    prediction_report = _prediction_report(predictions, name=name or "")

    if not place:
        place = reverse_location(lat, lon)

    birth_text = f"{local_dt.strftime('%d-%m-%Y %I:%M %p')} | {place}"
    chart_path = create_kundali_png(rows, asc, name, birth_text)
    planet_df = make_planet_table(rows)

    dasha_gujarati = dasha_df.copy()
    dasha_gujarati["મહાદશા"] = dasha_gujarati["Mahadasha"].map(DASHA_GUJARATI)
    dasha_gujarati["અંતર્દશા"] = dasha_gujarati["Antardasha"].map(DASHA_GUJARATI)
    dasha_gujarati = dasha_gujarati[["મહાદશા", "અંતર્દશા", "Start", "End"]]
    dasha_gujarati.columns = ["મહાદશા", "અંતર્દશા", "શરૂઆત", "અંત"]

    janma_rashi = RASHI_GUJARATI[moon["Rashi"]]
    moon_nakshatra = NAKSHATRA_GUJARATI[moon["Nakshatra"]]

    report = f"""
# 🪔 વૈદિક જન્મ કુંડળી

## 👤 વ્યક્તિની માહિતી
**નામ:** {name or 'ઉલ્લેખિત નથી'}  
**જન્મસ્થળ:** {place}  
**અક્ષાંશ:** `{float(lat):.6f}`  
**રેખાંશ:** `{float(lon):.6f}`  
**સમય ક્ષેત્ર:** `{timezone_name}`  
**જન્મ તારીખ:** `{local_dt.strftime('%d-%m-%Y')}`  
**જન્મ સમય:** `{local_dt.strftime('%I:%M %p')}`

---

## 🕉️ જન્મ રાશિ
**{janma_rashi}** — {moon['Rashi']}

## ⭐ જન્મ નક્ષત્ર
**નક્ષત્ર:** {moon_nakshatra}  
**પાદ:** {moon['Pada']}  
**નક્ષત્ર સ્વામી:** {PLANET_GUJARATI.get(moon['Nakshatra_Lord'], moon['Nakshatra_Lord'])}

## 🌅 લગ્ન
**લગ્ન રાશિ:** {RASHI_GUJARATI[asc['Rashi']]}  
**અંશ:** {format_degree(asc['Degree_in_Rashi'])}  
**નક્ષત્ર:** {NAKSHATRA_GUJARATI[asc['Nakshatra']]}  
**પાદ:** {asc['Pada']}  
**નક્ષત્ર સ્વામી:** {PLANET_GUJARATI.get(asc['Nakshatra_Lord'], asc['Nakshatra_Lord'])}

## 🕉️ વિંશોત્તરી દશા
**પ્રારંભિક મહાદશા:** {DASHA_GUJARATI.get(first_lord, first_lord)}

## ⚙️ ગણતરી પદ્ધતિ
- સાઇડિરિયલ રાશિચક્ર
- લાહિરી અયનામ્ષ
- Swiss Ephemeris
- Mean Rahu
- Ketu = Rahu + 180°
- Whole Sign Houses
- D1 જન્મ રાશિ કુંડળી
- D9 નવાંશ કુંડળી
- ઉત્તર ભારતીય કુંડળી બંધારણ

"""
    report += prediction_report

    return {
        "name": name,
        "place": place,
        "timezone": timezone_name,
        "local_dt": local_dt,
        "lat": float(lat),
        "lon": float(lon),
        "rows": rows,
        "asc": asc,
        "dasha_df": dasha_df,
        "dasha_gujarati": dasha_gujarati,
        "planet_df": planet_df,
        "prediction_df": prediction_df,
        "predictions": predictions,
        "prediction_report": prediction_report,
        "report": report,
        "chart_path": chart_path,
        "first_lord": first_lord,
        "moon_nak": moon_nak,
        "moon_pada": moon_pada,
    }

# ------------------------------------------------------------------
# PDF REPORT
# ------------------------------------------------------------------
def _find_gujarati_font():
    for p in font_manager.findSystemFonts():
        b = os.path.basename(p).lower()
        if "notosansgujarati" in b and "regular" in b:
            return p
    for p in font_manager.findSystemFonts():
        if "notosansgujarati" in os.path.basename(p).lower():
            return p
    return None


def build_pdf(result):
    out = os.path.join(tempfile.gettempdir(), "gujarati_vedic_kundali_report.pdf")
    guj_font = _find_gujarati_font()
    if guj_font:
        try:
            pdfmetrics.registerFont(TTFont("NotoGujarati", guj_font))
            base_font = "NotoGujarati"
        except Exception:
            base_font = "Helvetica"
    else:
        base_font = "Helvetica"

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "GujaratiTitle", parent=styles["Title"], fontName=base_font,
        fontSize=18, leading=23, alignment=TA_CENTER, spaceAfter=10
    )
    h1 = ParagraphStyle(
        "GujaratiH1", parent=styles["Heading1"], fontName=base_font,
        fontSize=13, leading=17, spaceBefore=9, spaceAfter=5
    )
    body = ParagraphStyle(
        "GujaratiBody", parent=styles["BodyText"], fontName=base_font,
        fontSize=9.2, leading=13, spaceAfter=4
    )

    doc = SimpleDocTemplate(
        out, pagesize=A4, rightMargin=14*mm, leftMargin=14*mm,
        topMargin=12*mm, bottomMargin=12*mm
    )
    story = []
    story.append(Paragraph("વૈદિક જન્મ કુંડળી", title_style))
    if result.get("chart_path") and os.path.exists(result["chart_path"]):
        story.append(Image(result["chart_path"], width=180*mm, height=96*mm))
        story.append(Spacer(1, 4*mm))

    info = [
        ["નામ", str(result["name"] or "ઉલ્લેખિત નથી")],
        ["જન્મસ્થળ", str(result["place"])],
        ["અક્ષાંશ", f"{result['lat']:.6f}"],
        ["રેખાંશ", f"{result['lon']:.6f}"],
        ["સમય ક્ષેત્ર", result["timezone"]],
        ["જન્મ તારીખ/સમય", result["local_dt"].strftime("%d-%m-%Y %I:%M %p")],
    ]
    t = Table(info, colWidths=[38*mm, 140*mm])
    t.setStyle(TableStyle([
        ("FONTNAME", (0,0), (-1,-1), base_font),
        ("FONTSIZE", (0,0), (-1,-1), 8.5),
        ("GRID", (0,0), (-1,-1), 0.35, colors.grey),
        ("BACKGROUND", (0,0), (0,-1), colors.whitesmoke),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING", (0,0), (-1,-1), 5),
        ("RIGHTPADDING", (0,0), (-1,-1), 5),
    ]))
    story.append(t)

    story.append(Paragraph("ગ્રહોની સ્થિતિ", h1))
    pdf_rows = [["ગ્રહ", "રાશિ", "અંશ", "નક્ષત્ર", "પાદ", "ભાવ"]]
    for _, r in result["planet_df"].iterrows():
        pdf_rows.append([
            str(r["ગ્રહ"]), str(r["રાશિ"]), str(r["અંશ"]),
            str(r["નક્ષત્ર"]), str(r["પાદ"]), str(r["ભાવ"])
        ])
    pt = Table(pdf_rows, repeatRows=1, colWidths=[27*mm, 27*mm, 28*mm, 42*mm, 16*mm, 16*mm])
    pt.setStyle(TableStyle([
        ("FONTNAME", (0,0), (-1,-1), base_font),
        ("FONTSIZE", (0,0), (-1,-1), 7.5),
        ("GRID", (0,0), (-1,-1), 0.3, colors.grey),
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#eee6f7")),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ]))
    story.append(pt)

    story.append(Paragraph("વિંશોત્તરી દશા", h1))
    drows = [["મહાદશા", "અંતર્દશા", "શરૂઆત", "અંત"]]
    for _, r in result["dasha_gujarati"].iterrows():
        drows.append([str(r.iloc[0]), str(r.iloc[1]), str(r.iloc[2]), str(r.iloc[3])])
    dt = Table(drows, repeatRows=1, colWidths=[40*mm, 40*mm, 40*mm, 40*mm])
    dt.setStyle(TableStyle([
        ("FONTNAME", (0,0), (-1,-1), base_font),
        ("FONTSIZE", (0,0), (-1,-1), 7.5),
        ("GRID", (0,0), (-1,-1), 0.3, colors.grey),
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#eee6f7")),
    ]))
    story.append(dt)

    story.append(PageBreak())
    story.append(Paragraph("નિયમ આધારિત જ્યોતિષ આગાહી", title_style))
    for para in result["prediction_report"].split("\n\n"):
        p = para.strip()
        if not p or p.startswith("---"):
            continue
        # Basic markdown-to-plain conversion for PDF.
        p = p.replace("# ", "").replace("## ", "").replace("### ", "")
        p = p.replace("**", "")
        p = p.replace("> ", "")
        if p.startswith("-"):
            p = "• " + p[1:].strip()
        story.append(Paragraph(html.escape(p).replace("\n", "<br/>"), body))

    doc.build(story)
    return out

# ------------------------------------------------------------------
# SESSION STATE
# ------------------------------------------------------------------
for key, default in {
    "latitude": None,
    "longitude": None,
    "timezone": "Asia/Kolkata",
    "confirmed_place": "",
    "result": None,
    "last_map_click": None,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ------------------------------------------------------------------
# UI
# ------------------------------------------------------------------
st.markdown('<div class="main-title">🪔 ગુજરાતી વૈદિક જન્મ કુંડળી</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">જન્મસ્થળ પસંદ કરો → જન્મ વિગતો દાખલ કરો → D1, D9, દશા અને નિયમ આધારિત વિશ્લેષણ મેળવો</div>',
    unsafe_allow_html=True,
)

with st.expander("⚠️ મહત્વપૂર્ણ નોંધ", expanded=False):
    st.write(
        "આ એપ્લિકેશન પરંપરાગત વૈદિક જ્યોતિષના નિયમોનું ગણિતીય/નિયમ આધારિત અર્થઘટન આપે છે. "
        "આ પદ્ધતિ વૈજ્ઞાનિક રીતે માન્ય ભવિષ્યવાણી પદ્ધતિ નથી અને આરોગ્ય, કાનૂની, નાણાકીય અથવા અન્ય ઉચ્ચ-જોખમ નિર્ણય માટે તેનો આધાર ન લેવો."
    )

st.subheader("૧. વ્યક્તિની માહિતી")
name = st.text_input("નામ", placeholder="તમારું નામ દાખલ કરો")

st.subheader("૨. જન્મસ્થળ")
search_col1, search_col2 = st.columns([4,1])
with search_col1:
    search_text = st.text_input("ગુજરાતનું જન્મસ્થળ શોધો", placeholder="Junagadh, Rajkot, Ahmedabad", key="search_text")
with search_col2:
    search_clicked = st.button("🔎 શોધો", use_container_width=True)

if search_clicked:
    ok, status = search_and_store_place(search_text)
    if ok:
        st.success(status)
    else:
        st.error(status)

map_col, info_col = st.columns([2.2,1])
with map_col:
    st.markdown("**🗺️ ગુજરાતના નકશા પર ક્લિક કરો**")
    m = make_gujarat_map(st.session_state["latitude"], st.session_state["longitude"])
    map_result = st_folium(m, width=None, height=520, returned_objects=["last_clicked"])
    clicked = map_result.get("last_clicked") if map_result else None
    if clicked:
        lat = round(float(clicked["lat"]), 6)
        lon = round(float(clicked["lng"]), 6)
        click_key = f"{lat:.6f},{lon:.6f}"
        if st.session_state.get("last_map_click") != click_key:
            st.session_state["last_map_click"] = click_key
            if is_inside_gujarat(lat, lon):
                st.session_state["latitude"] = lat
                st.session_state["longitude"] = lon
                st.session_state["timezone"] = get_timezone(lat, lon)
                st.session_state["confirmed_place"] = reverse_location(lat, lon)
                st.rerun()
            else:
                st.warning("કૃપા કરીને ગુજરાતની અંદરનું સ્થળ પસંદ કરો.")

with info_col:
    st.markdown("### પસંદ કરેલ સ્થળ")
    st.write(f"**સ્થળ:** {st.session_state['confirmed_place'] or 'હજુ પસંદ કરેલ નથી'}")
    st.write(f"**અક્ષાંશ:** {st.session_state['latitude'] if st.session_state['latitude'] is not None else '—'}")
    st.write(f"**રેખાંશ:** {st.session_state['longitude'] if st.session_state['longitude'] is not None else '—'}")
    st.write(f"**સમય ક્ષેત્ર:** {st.session_state['timezone']}")
    if st.button("✅ જન્મસ્થળની પુષ્ટિ કરો", use_container_width=True):
        if st.session_state["latitude"] is None or st.session_state["longitude"] is None:
            st.warning("પહેલા નકશા પર સ્થળ પસંદ કરો અથવા શોધ કરો.")
        else:
            status = confirm_and_store(st.session_state["latitude"], st.session_state["longitude"])
            st.success(status)

st.subheader("૩. જન્મ તારીખ અને સમય")
dc1, dc2, dc3 = st.columns(3)
with dc1:
    day = st.selectbox("દિવસ", list(range(1,32)), index=0)
with dc2:
    months = [("જાન્યુઆરી",1),("ફેબ્રુઆરી",2),("માર્ચ",3),("એપ્રિલ",4),("મે",5),("જૂન",6),("જુલાઈ",7),("ઑગસ્ટ",8),("સપ્ટેમ્બર",9),("ઑક્ટોબર",10),("નવેમ્બર",11),("ડિસેમ્બર",12)]
    month_label = st.selectbox("મહિનો", [x[0] for x in months], index=0)
    month = dict(months)[month_label]
with dc3:
    year = st.selectbox("વર્ષ", list(range(1900,2031)), index=100)

tc1, tc2, tc3 = st.columns(3)
with tc1:
    hour = st.selectbox("કલાક", list(range(1,13)), index=11)
with tc2:
    minute = st.selectbox("મિનિટ", [f"{i:02d}" for i in range(60)], index=0)
with tc3:
    ampm = st.selectbox("AM / PM", ["AM","PM"], index=0)

if st.button("🪐 સંપૂર્ણ જન્મ કુંડળી બનાવો", type="primary", use_container_width=True):
    if st.session_state["latitude"] is None or st.session_state["longitude"] is None:
        st.error("કૃપા કરીને પહેલાં જન્મસ્થળ પસંદ કરો.")
    else:
        try:
            with st.spinner("કુંડળી, દશા અને નિયમ આધારિત વિશ્લેષણ તૈયાર થઈ રહ્યું છે..."):
                result = calculate_kundali(
                    name, day, month, year, hour, int(minute), ampm,
                    st.session_state["confirmed_place"],
                    st.session_state["latitude"],
                    st.session_state["longitude"],
                    st.session_state["timezone"],
                )
            st.session_state["result"] = result
            st.success("✅ સંપૂર્ણ કુંડળી તૈયાર છે.")
        except Exception as e:
            st.exception(e)

result = st.session_state.get("result")
if result:
    st.divider()
    st.subheader("📋 જન્મ સારાંશ")
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("જન્મ રાશિ", result["planet_df"].loc[result["planet_df"]["ગ્રહ"] == "ચંદ્ર", "રાશિ"].iloc[0])
    c2.metric("લગ્ન", RASHI_GUJARATI[result["asc"]["Rashi"]])
    c3.metric("નક્ષત્ર", result["moon_nak"])
    c4.metric("પ્રારંભિક મહાદશા", DASHA_GUJARATI.get(result["first_lord"], result["first_lord"]))

    st.subheader("🪔 D1 જન્મ રાશિ અને D9 નવાંશ")
    st.image(result["chart_path"], use_container_width=True)

    st.subheader("🪐 ગ્રહોની સ્થિતિ")
    st.dataframe(result["planet_df"], use_container_width=True, hide_index=True)

    st.subheader("🕉️ વિંશોત્તરી દશા")
    st.dataframe(result["dasha_gujarati"], use_container_width=True, hide_index=True)

    st.subheader("🔮 નિયમ આધારિત જ્યોતિષ આગાહી સારાંશ")
    st.dataframe(result["prediction_df"], use_container_width=True, hide_index=True)

    pred = result["predictions"]
    pc1, pc2 = st.columns(2)
    with pc1:
        st.metric("સમગ્ર કુંડળી સ્કોર", f"{pred['overall_score']:.1f}/100")
    with pc2:
        m = pred["manglik"]
        st.metric("મંગળ દોષ", "હા" if m["present"] else "ના")

    st.markdown(result["prediction_report"])

    st.subheader("📅 11 વર્ષનો નિયમ આધારિત ટ્રેન્ડ")
    annual_rows = []
    for y in pred["annual"]:
        s = y["scores"]
        annual_rows.append({
            "વર્ષ": y["year"],
            "કારકિર્દી": s["career"],
            "ધન": s["wealth"],
            "શિક્ષણ": s["education"],
            "સંબંધો": s["relationships"],
        })
    annual_df = pd.DataFrame(annual_rows).set_index("વર્ષ")
    st.line_chart(annual_df, use_container_width=True)
    st.dataframe(annual_df, use_container_width=True)

    st.subheader("🪐 ગ્રહ શક્તિ સારાંશ")
    strength_df = pd.DataFrame(pred.get("planet_strengths", []))
    if not strength_df.empty:
        strength_df = strength_df.rename(columns={
            "Planet":"ગ્રહ", "Strength":"બળ", "Dignity":"સ્થિતિ",
            "House":"ભાવ", "Functional":"કાર્યાત્મક સ્વભાવ", "Combust":"દહન", "Notes":"નોંધ"
        })
        strength_df["ગ્રહ"] = strength_df["ગ્રહ"].map(PLANET_GUJARATI).fillna(strength_df["ગ્રહ"])
        strength_df["સ્થિતિ"] = strength_df["સ્થિતિ"].replace({"exalted":"ઉચ્ચ", "debilitated":"નીચ", "own sign":"સ્વરાશિ", "neutral":"સામાન્ય", "node":"છાયા ગ્રહ"})
        strength_df["કાર્યાત્મક સ્વભાવ"] = strength_df["કાર્યાત્મક સ્વભાવ"].replace({"Supportive":"સહાયક", "Challenging":"પડકારજનક", "Mixed":"મિશ્ર"})
        strength_df["દહન"] = strength_df["દહન"].replace({"Yes":"હા", "No":"ના"})
        st.dataframe(strength_df, use_container_width=True, hide_index=True)

    st.subheader("🧿 યોગ અને મહત્વપૂર્ણ સ્થિતિઓ")
    yogas = pred.get("yogas", [])
    if yogas:
        yoga_df = pd.DataFrame(yogas)
        yoga_df = yoga_df.rename(columns={"name":"યોગ", "strength":"બળ", "reason":"અર્થઘટન"})
        yoga_df["યોગ"] = yoga_df["યોગ"].replace({
            "Raja Yoga connection":"રાજયોગ સંકેત",
            "Dharma-Karmadhipati Yoga":"ધર્મ-કર્માધિપતિ યોગ",
            "Dhana Yoga connection":"ધન યોગ સંકેત",
            "Gaja Kesari Yoga":"ગજકેસરી યોગ",
            "Budha-Aditya Yoga":"બુધાદિત્ય યોગ",
            "Vipareeta Raja Yoga indication":"વિપરીત રાજયોગ સંકેત",
            "Neecha placement":"નીચ ગ્રહસ્થિતિ"
        })
        yoga_df["બળ"] = yoga_df["બળ"].replace({"Strong":"મજબૂત", "Moderate":"મધ્યમ", "Context-dependent":"પરિસ્થિતિ આધારિત", "Requires cancellation analysis":"રદયોગ વિશ્લેષણ જરૂરી"})
        st.dataframe(yoga_df, use_container_width=True, hide_index=True)
    else:
        st.info("વર્તમાન નિયમ સમૂહ મુજબ કોઈ મુખ્ય યોગ મળ્યો નથી.")

    st.subheader("📥 Downloads")
    pdf_path = None
    try:
        pdf_path = build_pdf(result)
    except Exception as e:
        st.warning(f"PDF તૈયાર કરવામાં સમસ્યા: {e}")

    d1 = result["prediction_report"].encode("utf-8")
    st.download_button(
        "📄 Download Prediction Report (Markdown)",
        data=d1,
        file_name="vedic_prediction_report.md",
        mime="text/markdown",
        use_container_width=True,
    )

    st.download_button(
        "📊 Download Planetary Positions (CSV)",
        data=result["planet_df"].to_csv(index=False).encode("utf-8-sig"),
        file_name="planetary_positions.csv",
        mime="text/csv",
        use_container_width=True,
    )

    st.download_button(
        "🕉️ Download Vimshottari Dasha (CSV)",
        data=result["dasha_gujarati"].to_csv(index=False).encode("utf-8-sig"),
        file_name="vimshottari_dasha.csv",
        mime="text/csv",
        use_container_width=True,
    )

    st.download_button(
        "🔮 Download Prediction Summary (CSV)",
        data=result["prediction_df"].to_csv(index=False).encode("utf-8-sig"),
        file_name="prediction_summary.csv",
        mime="text/csv",
        use_container_width=True,
    )

    if pdf_path and os.path.exists(pdf_path):
        with open(pdf_path, "rb") as f:
            st.download_button(
                "📕 Download Complete Gujarati PDF",
                data=f.read(),
                file_name="gujarati_vedic_kundali_report.pdf",
                mime="application/pdf",
                use_container_width=True,
            )

    with open(result["chart_path"], "rb") as f:
        st.download_button(
            "🖼️ Download D1 + D9 Kundali PNG",
            data=f.read(),
            file_name="gujarati_vedic_kundali.png",
            mime="image/png",
            use_container_width=True,
        )
