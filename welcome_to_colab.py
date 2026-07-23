# ============================================================
# KISHANSKY — REAL-TIME ASTRONOMY OBSERVATORY
# COLAB ONE-CELL VERSION
# ============================================================

# ------------------------------------------------------------
# 1. INSTALL DEPENDENCIES
# ------------------------------------------------------------

import sys
import subprocess

packages = [
    "streamlit",
    "skyfield",
    "sgp4",
    "numpy",
    "pandas",
    "requests",
    "plotly"
]

for package in packages:

    subprocess.check_call(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "-q",
            package
        ]
    )


# ------------------------------------------------------------
# 2. WRITE APPLICATION
# ------------------------------------------------------------

app_code = r'''
import streamlit as st
import numpy as np
import pandas as pd
import requests
import math
import time
from datetime import datetime, timezone, timedelta

from skyfield.api import load, EarthSatellite, wgs84
from skyfield.data import hipparcos


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="KishanSky",
    page_icon="🌌",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# CUSTOM INTERFACE
# ============================================================

st.markdown(
"""
<style>

html, body, [class*="css"] {
    font-family: Arial, sans-serif;
}

.stApp {
    background:
        radial-gradient(
            circle at top,
            #101d3a 0%,
            #050914 45%,
            #020308 100%
        );
    color: white;
}

section[data-testid="stSidebar"] {
    background:
        linear-gradient(
            180deg,
            #070c19,
            #02040a
        );
    border-right: 1px solid #1c3857;
}

h1 {
    color: #76ddff;
    letter-spacing: 3px;
}

h2, h3 {
    color: #a8eaff;
}

div[data-testid="stMetric"] {
    background: rgba(20, 40, 70, 0.35);
    border: 1px solid #25476b;
    border-radius: 12px;
    padding: 10px;
}

</style>
""",
    unsafe_allow_html=True
)


# ============================================================
# TITLE
# ============================================================

st.title("🌌 KISHANSKY")

st.caption(
    "REAL-TIME ASTRONOMY OBSERVATORY • CREATED BY KISHAN"
)


# ============================================================
# SESSION STATE
# ============================================================

if "simulation_time" not in st.session_state:

    st.session_state.simulation_time = datetime.now(
        timezone.utc
    )

if "satellites" not in st.session_state:

    st.session_state.satellites = None

if "stars" not in st.session_state:

    st.session_state.stars = None


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("⚙️ OBSERVATORY CONTROL")


# ------------------------------------------------------------
# LOCATION
# ------------------------------------------------------------

st.sidebar.subheader("📍 Observer Location")

latitude = st.sidebar.number_input(
    "Latitude",
    value=41.7508,
    min_value=-90.0,
    max_value=90.0
)

longitude = st.sidebar.number_input(
    "Longitude",
    value=-88.1535,
    min_value=-180.0,
    max_value=180.0
)

elevation = st.sidebar.number_input(
    "Elevation (meters)",
    value=210.0,
    min_value=-500.0,
    max_value=10000.0
)


# ------------------------------------------------------------
# TIME CONTROL
# ------------------------------------------------------------

st.sidebar.subheader("⏱ Time Control")

time_speed = st.sidebar.select_slider(
    "Time Speed",
    options=[
        0,
        1,
        10,
        60,
        600,
        3600,
        86400
    ],
    value=1,
    format_func=lambda x: (
        "PAUSED"
        if x == 0
        else f"{x}×"
    )
)


# ------------------------------------------------------------
# FOV
# ------------------------------------------------------------

st.sidebar.subheader("🔭 Sky View")

fov = st.sidebar.slider(
    "Field of View",
    20,
    180,
    100
)


# ============================================================
# LOAD ASTRONOMICAL DATA
# ============================================================

@st.cache_resource
def load_ephemeris():

    ts = load.timescale()

    eph = load(
        "de421.bsp"
    )

    return ts, eph


@st.cache_data
def load_stars():

    try:

        with load.open(
            "hip_main.dat"
        ) as f:

            stars = hipparcos.load_dataframe(
                f
            )

    except Exception:

        stars = load(
            "hip_main.dat"
        )

    stars = stars[
        stars["magnitude"] <= 6.5
    ]

    stars = stars[
        [
            "ra_degrees",
            "dec_degrees",
            "magnitude"
        ]
    ]

    return stars


# ============================================================
# LOAD EPHEMERIS
# ============================================================

try:

    ts, eph = load_ephemeris()

except Exception as error:

    st.error(
        f"Could not load planetary ephemeris: {error}"
    )

    st.stop()


# ============================================================
# LOAD STARS
# ============================================================

try:

    stars = load_stars()

except Exception as error:

    st.warning(
        f"Star catalog unavailable: {error}"
    )

    stars = pd.DataFrame()


# ============================================================
# CURRENT SIMULATION TIME
# ============================================================

if time_speed > 0:

    st.session_state.simulation_time += timedelta(
        seconds=time_speed
    )


current_time = st.session_state.simulation_time

t = ts.from_datetime(
    current_time
)


# ============================================================
# OBSERVER
# ============================================================

observer = wgs84.latlon(
    latitude,
    longitude,
    elevation_m=elevation
)

earth = eph["earth"]

observer_position = (
    earth
    + observer
)


# ============================================================
# PLANETS
# ============================================================

bodies = {

    "Sun": eph["sun"],
    "Moon": eph["moon"],
    "Mercury": eph["mercury"],
    "Venus": eph["venus"],
    "Mars": eph["mars"],
    "Jupiter": eph["jupiter barycenter"],
    "Saturn": eph["saturn barycenter"],
    "Uranus": eph["uranus barycenter"],
    "Neptune": eph["neptune barycenter"]
}


planet_positions = []


for name, body in bodies.items():

    try:

        astrometric = observer_position.at(
            t
        ).observe(
            body
        )

        apparent = astrometric.apparent()

        altitude, azimuth, distance = (
            apparent.altaz()
        )

        planet_positions.append(

            {
                "Object": name,
                "Type": "Planetary Body",
                "Azimuth": round(
                    azimuth.degrees,
                    3
                ),
                "Altitude": round(
                    altitude.degrees,
                    3
                ),
                "Distance (km)": round(
                    distance.km,
                    0
                )
            }

        )

    except Exception:

        pass


planet_df = pd.DataFrame(
    planet_positions
)


# ============================================================
# REAL SATELLITE DATA
# ============================================================

@st.cache_data(
    ttl=3600
)
def download_satellites():

    url = (
        "https://celestrak.org/NORAD/elements/gp.php"
        "?GROUP=active"
        "&FORMAT=tle"
    )

    response = requests.get(
        url,
        timeout=30
    )

    response.raise_for_status()

    lines = response.text.splitlines()

    satellites = []

    i = 0

    while i + 2 < len(lines):

        name = lines[i].strip()

        line1 = lines[i + 1].strip()

        line2 = lines[i + 2].strip()

        if (
            line1.startswith("1 ")
            and line2.startswith("2 ")
        ):

            satellites.append(

                {
                    "name": name,
                    "line1": line1,
                    "line2": line2
                }

            )

        i += 3

    return satellites


try:

    satellite_data = download_satellites()

except Exception as error:

    satellite_data = []

    st.warning(
        f"Satellite data temporarily unavailable: {error}"
    )


# ============================================================
# SATELLITE PROPAGATION
# ============================================================

satellite_positions = []


for sat_data in satellite_data[:1000]:

    try:

        satellite = EarthSatellite(
            sat_data["line1"],
            sat_data["line2"],
            sat_data["name"],
            ts
        )

        geocentric = satellite.at(
            t
        )

        subpoint = wgs84.subpoint(
            geocentric
        )

        difference = (
            satellite
            - observer
        )

        topocentric = difference.at(
            t
        )

        altitude, azimuth, distance = (
            topocentric.altaz()
        )

        satellite_positions.append(

            {
                "Object": sat_data["name"],
                "Type": "Satellite",
                "Azimuth": round(
                    azimuth.degrees,
                    3
                ),
                "Altitude": round(
                    altitude.degrees,
                    3
                ),
                "Distance (km)": round(
                    distance.km,
                    3
                ),
                "Latitude": round(
                    subpoint.latitude.degrees,
                    4
                ),
                "Longitude": round(
                    subpoint.longitude.degrees,
                    4
                )
            }

        )

    except Exception:

        continue


satellite_df = pd.DataFrame(
    satellite_positions
)


# ============================================================
# SEARCH
# ============================================================

st.sidebar.subheader("🔎 Search")

search = st.sidebar.text_input(
    "Search for an object"
)


# ============================================================
# MAIN METRICS
# ============================================================

col1, col2, col3, col4 = st.columns(4)


with col1:

    st.metric(
        "Catalog Stars",
        f"{len(stars):,}"
    )


with col2:

    st.metric(
        "Active Satellites",
        f"{len(satellite_df):,}"
    )


with col3:

    st.metric(
        "Planets / Bodies",
        len(planet_df)
    )


with col4:

    st.metric(
        "UTC Time",
        current_time.strftime(
            "%H:%M:%S"
        )
    )


# ============================================================
# SEARCH RESULTS
# ============================================================

if search:

    search_lower = search.lower()

    planet_matches = planet_df[
        planet_df["Object"]
        .str.lower()
        .str.contains(
            search_lower
        )
    ]

    satellite_matches = satellite_df[
        satellite_df["Object"]
        .str.lower()
        .str.contains(
            search_lower,
            na=False
        )
    ]

    if len(planet_matches) > 0:

        st.subheader(
            "🪐 Planetary Search Result"
        )

        st.dataframe(
            planet_matches,
            use_container_width=True
        )

    elif len(satellite_matches) > 0:

        st.subheader(
            "🛰 Satellite Search Result"
        )

        st.dataframe(
            satellite_matches.head(50),
            use_container_width=True
        )

    else:

        st.info(
            "No matching object found."
        )


# ============================================================
# PLANETS
# ============================================================

st.subheader(
    "🪐 Real-Time Planetary Positions"
)

st.dataframe(
    planet_df,
    use_container_width=True,
    hide_index=True
)


# ============================================================
# SATELLITES
# ============================================================

st.subheader(
    "🛰 Real-Time Satellite Tracking"
)

if len(satellite_df) > 0:

    visible_satellites = satellite_df[
        satellite_df["Altitude"] > 0
    ]

    st.write(
        f"Visible above horizon: "
        f"{len(visible_satellites):,}"
    )

    st.dataframe(
        visible_satellites.head(100),
        use_container_width=True,
        hide_index=True
    )

else:

    st.warning(
        "No satellite data currently available."
    )


# ============================================================
# SKY MAP
# ============================================================

st.subheader(
    "🌌 Live Sky Map"
)

try:

    import plotly.graph_objects as go

    fig = go.Figure()

    # --------------------------------------------------------
    # STARS
    # --------------------------------------------------------

    if len(stars) > 0:

        star_sample = stars.head(
            5000
        )

        fig.add_trace(

            go.Scattergl(

                x=star_sample[
                    "ra_degrees"
                ],

                y=star_sample[
                    "dec_degrees"
                ],

                mode="markers",

                marker=dict(

                    size=np.maximum(

                        1,

                        7
                        - star_sample[
                            "magnitude"
                        ].values

                    ),

                    opacity=0.8

                ),

                name="Stars"

            )

        )


    # --------------------------------------------------------
    # PLANETS
    # --------------------------------------------------------

    if len(planet_df) > 0:

        fig.add_trace(

            go.Scatter(

                x=planet_df[
                    "Azimuth"
                ],

                y=planet_df[
                    "Altitude"
                ],

                mode="markers+text",

                text=planet_df[
                    "Object"
                ],

                textposition="top center",

                marker=dict(
                    size=12
                ),

                name="Planets"

            )

        )


    # --------------------------------------------------------
    # SATELLITES
    # --------------------------------------------------------

    visible = satellite_df[
        satellite_df[
            "Altitude"
        ] > 0
    ].head(
        300
    )

    if len(visible) > 0:

        fig.add_trace(

            go.Scattergl(

                x=visible[
                    "Azimuth"
                ],

                y=visible[
                    "Altitude"
                ],

                mode="markers",

                marker=dict(
                    size=5
                ),

                name="Satellites"

            )

        )


    fig.update_layout(

        height=650,

        paper_bgcolor="#020308",

        plot_bgcolor="#020308",

        font=dict(
            color="white"
        ),

        xaxis=dict(
            title="Azimuth / Right Ascension",
            gridcolor="#1d334e"
        ),

        yaxis=dict(
            title="Altitude / Declination",
            gridcolor="#1d334e"
        ),

        legend=dict(
            bgcolor="#050914"
        )

    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

except Exception as error:

    st.error(
        f"Sky visualization error: {error}"
    )


# ============================================================
# DATA TABLE
# ============================================================

with st.expander(
    "📊 Complete Planetary Data"
):

    st.dataframe(
        planet_df,
        use_container_width=True
    )


with st.expander(
    "📡 Satellite Data"
):

    st.dataframe(
        satellite_df.head(1000),
        use_container_width=True
    )


# ============================================================
# AUTO REFRESH
# ============================================================

time.sleep(
    1
)

st.rerun()
'''


# ------------------------------------------------------------
# 3. SAVE APP
# ------------------------------------------------------------

with open(
    "KishanSky.py",
    "w",
    encoding="utf-8"
) as file:

    file.write(
        app_code
    )


# ------------------------------------------------------------
# 4. START STREAMLIT
# ------------------------------------------------------------

import os
import subprocess
import time

# Stop previous Streamlit servers
os.system(
    "pkill -f 'streamlit run' || true"
)

time.sleep(
    2
)

process = subprocess.Popen(

    [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        "KishanSky.py",
        "--server.port",
        "8501",
        "--server.address",
        "0.0.0.0",
        "--server.headless",
        "true",
        "--browser.gatherUsageStats",
        "false"
    ],

    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT
)

print(
    "KishanSky is starting..."
)

time.sleep(
    8
)

print(
    "Open the Streamlit preview or Colab port 8501."
)
