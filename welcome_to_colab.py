import streamlit as st
import pandas as pd
import numpy as np
import requests
import math
from datetime import datetime, timezone

from skyfield.api import load, EarthSatellite, wgs84


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="KishanSky",
    page_icon="🌌",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# STYLE
# ============================================================

st.markdown("""
<style>

.stApp {
    background:
        radial-gradient(
            ellipse at top,
            #17284a 0%,
            #070b17 45%,
            #020308 100%
        );
}

[data-testid="stSidebar"] {
    background-color: #050914;
}

h1 {
    color: #79e6ff;
    letter-spacing: 4px;
}

h2, h3 {
    color: #b5edff;
}

[data-testid="stMetric"] {
    background: rgba(20, 45, 75, 0.35);
    border: 1px solid #24496c;
    border-radius: 12px;
    padding: 12px;
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# HEADER
# ============================================================

st.title("🌌 KISHANSKY")

st.caption(
    "REAL-TIME ASTRONOMY OBSERVATORY • CREATED BY KISHAN"
)


# ============================================================
# LOAD SKYFIELD DATA
# ============================================================

@st.cache_resource
def load_astronomy():

    ts = load.timescale()

    eph = load("de421.bsp")

    return ts, eph


try:

    ts, eph = load_astronomy()

except Exception as error:

    st.error(
        f"Unable to load astronomy engine: {error}"
    )

    st.stop()


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.header("🔭 OBSERVATORY")

st.sidebar.subheader("📍 Observer Location")

latitude = st.sidebar.number_input(
    "Latitude",
    min_value=-90.0,
    max_value=90.0,
    value=41.7508,
    step=0.0001
)

longitude = st.sidebar.number_input(
    "Longitude",
    min_value=-180.0,
    max_value=180.0,
    value=-88.1535,
    step=0.0001
)

elevation = st.sidebar.number_input(
    "Elevation (m)",
    min_value=-500.0,
    max_value=10000.0,
    value=210.0
)


st.sidebar.subheader("⏱ TIME")

simulation_time = st.sidebar.datetime_input(
    "Observation Time",
    value=datetime.now()
)


st.sidebar.subheader("🔎 SEARCH")

search = st.sidebar.text_input(
    "Search planets or satellites"
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

observer_position = earth + observer


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


t = ts.from_datetime(
    simulation_time.replace(
        tzinfo=timezone.utc
    )
)


planet_rows = []


for name, body in bodies.items():

    try:

        astrometric = (
            observer_position
            .at(t)
            .observe(body)
        )

        apparent = astrometric.apparent()

        altitude, azimuth, distance = (
            apparent.altaz()
        )

        planet_rows.append({

            "Object": name,

            "Type": "Solar System",

            "Azimuth (°)": round(
                azimuth.degrees,
                2
            ),

            "Altitude (°)": round(
                altitude.degrees,
                2
            ),

            "Distance (km)": round(
                distance.km
            )

        })

    except Exception:

        continue


planet_df = pd.DataFrame(
    planet_rows
)


# ============================================================
# REAL SATELLITE DATA
# ============================================================

@st.cache_data(ttl=3600)
def get_satellite_tles():

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

    for i in range(
        0,
        len(lines) - 2,
        3
    ):

        name = lines[i].strip()

        line1 = lines[i + 1].strip()

        line2 = lines[i + 2].strip()

        if (
            line1.startswith("1 ")
            and line2.startswith("2 ")
        ):

            satellites.append({

                "name": name,

                "line1": line1,

                "line2": line2

            })

    return satellites


try:

    tle_data = get_satellite_tles()

except Exception as error:

    st.warning(
        f"Satellite data unavailable: {error}"
    )

    tle_data = []


# ============================================================
# PROPAGATE SATELLITES
# ============================================================

satellite_rows = []


for data in tle_data:

    try:

        satellite = EarthSatellite(

            data["line1"],

            data["line2"],

            data["name"],

            ts

        )

        difference = satellite - observer

        topocentric = difference.at(t)

        altitude, azimuth, distance = (
            topocentric.altaz()
        )

        geocentric = satellite.at(t)

        subpoint = wgs84.subpoint(
            geocentric
        )

        satellite_rows.append({

            "Object": data["name"],

            "Type": "Satellite",

            "Azimuth (°)": round(
                azimuth.degrees,
                2
            ),

            "Altitude (°)": round(
                altitude.degrees,
                2
            ),

            "Distance (km)": round(
                distance.km,
                2
            ),

            "Latitude": round(
                subpoint.latitude.degrees,
                4
            ),

            "Longitude": round(
                subpoint.longitude.degrees,
                4
            )

        })

    except Exception:

        continue


satellite_df = pd.DataFrame(
    satellite_rows
)


# ============================================================
# METRICS
# ============================================================

a, b, c, d = st.columns(4)


with a:

    st.metric(
        "🌟 Active Stars System",
        "HIPPARCOS"
    )


with b:

    st.metric(
        "🛰 Satellites",
        f"{len(satellite_df):,}"
    )


with c:

    st.metric(
        "🪐 Solar System Objects",
        len(planet_df)
    )


with d:

    st.metric(
        "🕒 UTC",
        simulation_time.strftime(
            "%H:%M:%S"
        )
    )


# ============================================================
# SEARCH
# ============================================================

if search:

    search_lower = search.lower()

    planet_results = planet_df[
        planet_df["Object"]
        .str.lower()
        .str.contains(
            search_lower
        )
    ]

    satellite_results = satellite_df[
        satellite_df["Object"]
        .str.lower()
        .str.contains(
            search_lower,
            na=False
        )
    ]

    if len(planet_results) > 0:

        st.subheader(
            "🔍 Planet Search Result"
        )

        st.dataframe(
            planet_results,
            use_container_width=True,
            hide_index=True
        )

    elif len(satellite_results) > 0:

        st.subheader(
            "🔍 Satellite Search Result"
        )

        st.dataframe(
            satellite_results.head(100),
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info(
            "No matching object found."
        )


# ============================================================
# PLANETARY DATA
# ============================================================

st.subheader(
    "🪐 Real-Time Solar System"
)

st.dataframe(
    planet_df,
    use_container_width=True,
    hide_index=True
)


# ============================================================
# SATELLITE DATA
# ============================================================

st.subheader(
    "🛰 Real-Time Satellite Tracking"
)

visible_satellites = satellite_df[
    satellite_df["Altitude (°)"] > 0
]

st.write(
    f"Satellites above your horizon: "
    f"{len(visible_satellites):,}"
)

st.dataframe(
    visible_satellites.head(100),
    use_container_width=True,
    hide_index=True
)


# ============================================================
# VISUAL SKY MAP
# ============================================================

st.subheader(
    "🌌 Interactive Sky Map"
)

import plotly.graph_objects as go


fig = go.Figure()


# ------------------------------------------------------------
# PLANETS
# ------------------------------------------------------------

if len(planet_df) > 0:

    fig.add_trace(

        go.Scatter(

            x=planet_df[
                "Azimuth (°)"
            ],

            y=planet_df[
                "Altitude (°)"
            ],

            mode="markers+text",

            text=planet_df[
                "Object"
            ],

            textposition="top center",

            marker=dict(
                size=15
            ),

            name="Planets"

        )

    )


# ------------------------------------------------------------
# SATELLITES
# ------------------------------------------------------------

if len(visible_satellites) > 0:

    satellite_sample = (
        visible_satellites
        .head(500)
    )

    fig.add_trace(

        go.Scattergl(

            x=satellite_sample[
                "Azimuth (°)"
            ],

            y=satellite_sample[
                "Altitude (°)"
            ],

            mode="markers",

            marker=dict(
                size=5
            ),

            name="Satellites"

        )

    )


fig.update_layout(

    height=700,

    paper_bgcolor="#020308",

    plot_bgcolor="#020308",

    font=dict(
        color="white"
    ),

    xaxis=dict(

        title="Azimuth (degrees)",

        range=[0, 360],

        gridcolor="#18304b"

    ),

    yaxis=dict(

        title="Altitude (degrees)",

        range=[0, 90],

        gridcolor="#18304b"

    ),

    legend=dict(

        bgcolor="#050914"

    )

)


st.plotly_chart(
    fig,
    use_container_width=True
)


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "KishanSky • Real satellite orbital propagation using current TLE data • "
    "Planetary calculations using Skyfield ephemerides • Built by Kishan"
)
