# ============================================================
# KISHANSKY OBSERVATORY
# REAL-TIME SATELLITE TRACKING ENGINE
# ============================================================

!pip -q install skyfield pandas requests

from IPython.display import HTML, display
import json
import time
import math
import requests
import pandas as pd

from skyfield.api import load, EarthSatellite, Topos


# ============================================================
# 1. REAL OBSERVER LOCATION
# ============================================================

OBSERVER_LATITUDE = 41.7606
OBSERVER_LONGITUDE = -88.1537
OBSERVER_ELEVATION_M = 220


# ============================================================
# 2. SKYFIELD TIME + OBSERVER
# ============================================================

ts = load.timescale()

observer = Topos(
    latitude_degrees=OBSERVER_LATITUDE,
    longitude_degrees=OBSERVER_LONGITUDE,
    elevation_m=OBSERVER_ELEVATION_M
)


# ============================================================
# 3. LOAD REAL SATELLITES FROM CELESTRAK
# ============================================================

# Active satellite group.
# This avoids downloading unnecessary data repeatedly.
CELESTRAK_URL = (
    "https://celestrak.org/NORAD/elements/"
    "gp.php?GROUP=active&FORMAT=TLE"
)

print("Downloading current orbital elements...")

response = requests.get(
    CELESTRAK_URL,
    timeout=30
)

response.raise_for_status()

tle_lines = response.text.strip().splitlines()

satellite_objects = []

for i in range(0, len(tle_lines) - 2, 3):

    name = tle_lines[i].strip()
    line1 = tle_lines[i + 1].strip()
    line2 = tle_lines[i + 2].strip()

    try:

        sat = EarthSatellite(
            line1,
            line2,
            name,
            ts
        )

        satellite_objects.append(sat)

    except Exception as error:

        print(
            "Could not load:",
            name,
            error
        )


print(
    "Loaded real satellites:",
    len(satellite_objects)
)


# ============================================================
# 4. REAL PLANET DATA
# ============================================================

planets_kernel = load("de421.bsp")

earth = planets_kernel["earth"]
sun = planets_kernel["sun"]
moon = planets_kernel["moon"]

planet_bodies = {

    "Sun": sun,
    "Moon": moon,

}


# ============================================================
# 5. CALCULATE REAL SATELLITE POSITION
# ============================================================

def calculate_satellite_position(satellite, t):

    try:

        difference = satellite - observer

        topocentric = difference.at(t)

        altitude, azimuth, distance = (
            topocentric.altaz()
        )

        return {

            "name": satellite.name,

            "type": "Satellite",

            "altitude": altitude.degrees,

            "azimuth": azimuth.degrees,

            "distance": distance.km,

            "norad_id": (
                satellite.model.satnum
            ),

        }

    except Exception:

        return None


# ============================================================
# 6. CALCULATE REAL PLANET POSITIONS
# ============================================================

def calculate_planet_position(body, name, t):

    try:

        astrometric = (
            earth
            + observer
        ).at(t).observe(body)

        apparent = astrometric.apparent()

        altitude, azimuth, distance = (
            apparent.altaz()
        )

        return {

            "name": name,

            "type": "Planet",

            "altitude": altitude.degrees,

            "azimuth": azimuth.degrees,

            "distance": distance.au * 149597870.7,

        }

    except Exception:

        return None


# ============================================================
# 7. CALCULATE EVERYTHING AT A TIME
# ============================================================

def calculate_all_objects(t):

    satellites = []

    for satellite in satellite_objects:

        result = calculate_satellite_position(
            satellite,
            t
        )

        if result:

            satellites.append(result)


    planets = []

    for name, body in planet_bodies.items():

        result = calculate_planet_position(
            body,
            name,
            t
        )

        if result:

            planets.append(result)


    return planets, satellites


# ============================================================
# 8. ORBIT TRAILS
# ============================================================

def calculate_orbit_trail(
    satellite,
    center_time,
    minutes=45,
    points=60
):

    trail = []

    start_seconds = (
        -minutes * 60
    )

    end_seconds = (
        minutes * 60
    )

    for i in range(points):

        fraction = i / (
            points - 1
        )

        seconds = (
            start_seconds
            + fraction
            * (
                end_seconds
                - start_seconds
            )
        )

        trail_time = ts.utc(
            center_time.utc_datetime()
            .timestamp()
            + seconds
        )

        result = (
            calculate_satellite_position(
                satellite,
                trail_time
            )
        )

        if result:

            trail.append(result)


    return trail


# ============================================================
# 9. INITIAL DATA
# ============================================================

current_time = ts.now()

planet_data, satellite_data = (
    calculate_all_objects(
        current_time
    )
)


# Only create trails for visible satellites
# to prevent the browser from rendering
# thousands of unnecessary orbit lines.

orbit_trails = []

for satellite in satellite_objects[:500]:

    position = calculate_satellite_position(
        satellite,
        current_time
    )

    if position and position["altitude"] > 0:

        trail = calculate_orbit_trail(
            satellite,
            current_time,
            minutes=45,
            points=50
        )

        orbit_trails.append({

            "name": satellite.name,

            "trail": trail

        })


# ============================================================
# 10. SEND DATA TO JAVASCRIPT
# ============================================================

planet_json = json.dumps(
    planet_data
)

satellite_json = json.dumps(
    satellite_data
)

orbit_json = json.dumps(
    orbit_trails
)


# ============================================================
# 11. STELLARIUM-STYLE APPLICATION
# ============================================================

app = f"""

<!DOCTYPE html>

<html>

<head>

<meta charset="UTF-8">

<title>Kishansky Observatory</title>


<style>

* {{
    box-sizing: border-box;
}}

html,
body {{

    margin: 0;

    padding: 0;

    overflow: hidden;

    background: #020617;

    color: white;

    font-family:
        Arial,
        sans-serif;

}}

#app {{

    width: 100vw;

    height: 850px;

    position: relative;

    overflow: hidden;

    background:

        radial-gradient(

            circle at center,

            #111827 0%,

            #020617 55%,

            #000 100%

        );

}}

#sky {{

    position: absolute;

    inset: 0;

    width: 100%;

    height: 100%;

    cursor: grab;

}}

#sky:active {{

    cursor: grabbing;

}}

#topbar {{

    position: absolute;

    top: 0;

    left: 0;

    right: 0;

    height: 60px;

    padding: 15px 22px;

    background:

        linear-gradient(

            rgba(0,0,0,.85),

            rgba(0,0,0,.35)

        );

    z-index: 10;

}}

#title {{

    font-size: 22px;

    font-weight: bold;

    display: inline-block;

}}

#clock {{

    margin-left: 25px;

    font-size: 14px;

    color: #cbd5e1;

}}

#search {{

    position: absolute;

    top: 15px;

    right: 22px;

    width: 250px;

    padding: 10px 14px;

    border-radius: 8px;

    border: 1px solid #475569;

    background: rgba(15,23,42,.9);

    color: white;

    outline: none;

}}

#info {{

    position: absolute;

    right: 22px;

    top: 85px;

    width: 300px;

    padding: 18px;

    background:

        rgba(2,6,23,.92);

    border:

        1px solid #475569;

    border-radius: 12px;

    display: none;

    z-index: 10;

    box-shadow:

        0 10px 40px rgba(0,0,0,.5);

}}

#info h2 {{

    margin-top: 0;

    font-size: 19px;

}}

#controls {{

    position: absolute;

    left: 50%;

    bottom: 20px;

    transform: translateX(-50%);

    display: flex;

    align-items: center;

    gap: 6px;

    padding: 10px;

    background:

        rgba(2,6,23,.9);

    border:

        1px solid #475569;

    border-radius: 12px;

    z-index: 10;

}}

button {{

    padding: 9px 13px;

    border-radius: 7px;

    border: 1px solid #475569;

    background: #1e293b;

    color: white;

    cursor: pointer;

}}

button:hover {{

    background: #334155;

}}

#status {{

    position: absolute;

    left: 20px;

    bottom: 20px;

    padding: 9px 12px;

    border-radius: 8px;

    background: rgba(0,0,0,.7);

    color: #cbd5e1;

    font-size: 12px;

    z-index: 10;

}}

</style>

</head>


<body>


<div id="app">


<canvas id="sky"></canvas>


<div id="topbar">

    <div id="title">

        🌌 KISHANSKY OBSERVATORY

    </div>

    <span id="clock"></span>

    <input

        id="search"

        placeholder="Search satellite or planet..."

    >

</div>


<div id="info">

    <h2 id="objectName">

        Selected Object

    </h2>

    <p>

        Type:

        <span id="objectType"></span>

    </p>

    <p>

        Altitude:

        <span id="objectAltitude"></span>

    </p>

    <p>

        Azimuth:

        <span id="objectAzimuth"></span>

    </p>

    <p>

        Distance:

        <span id="objectDistance"></span>

    </p>

</div>


<div id="status">

    Live orbital propagation active

</div>


<div id="controls">

    <button onclick="zoomIn()">

        +

    </button>

    <button onclick="zoomOut()">

        −

    </button>

    <button onclick="resetView()">

        Reset

    </button>

    <button onclick="toggleTime()">

        Pause

    </button>

    <button onclick="changeSpeed(-1)">

        Slower

    </button>

    <button onclick="changeSpeed(1)">

        Faster

    </button>

</div>


</div>


<script>


// ============================================================
// DATA
// ============================================================

const planets = {planet_json};

const satellites = {satellite_json};

const orbitTrails = {orbit_json};


let objects = [

    ...planets,

    ...satellites

];


// ============================================================
// CANVAS
// ============================================================

const canvas =

    document.getElementById(

        "sky"

    );


const ctx =

    canvas.getContext(

        "2d"

    );


let width =

    window.innerWidth;


let height =

    850;


function resizeCanvas() {{

    width =

        window.innerWidth;


    height =

        document

        .getElementById(

            "app"

        )

        .clientHeight;


    canvas.width =

        width;


    canvas.height =

        height;

}}


window.addEventListener(

    "resize",

    resizeCanvas

);


resizeCanvas();


// ============================================================
// VIEW STATE
// ============================================================

let zoom = 1;

let offsetX = 0;

let offsetY = 0;

let selected = null;

let paused = false;

let speed = 1;


// ============================================================
// STAR FIELD
// ============================================================

const stars = [];


for (

    let i = 0;

    i < 3500;

    i++

) {{

    stars.push({{

        x: Math.random(),

        y: Math.random(),

        size:

            Math.random() * 1.7,

        brightness:

            Math.random()

    }});

}}


// ============================================================
// COORDINATE TRANSFORMATION
// ============================================================

function convert(

    altitude,

    azimuth

) {{

    const cx =

        width / 2

        + offsetX;


    const cy =

        height / 2

        + offsetY;


    const radius =

        Math.min(

            width,

            height

        )

        * .40

        * zoom;


    const r =

        radius

        * (

            90

            - altitude

        )

        / 90;


    const angle =

        (

            azimuth

            - 90

        )

        * Math.PI

        / 180;


    return {{

        x:

            cx

            + r

            * Math.cos(

                angle

            ),

        y:

            cy

            + r

            * Math.sin(

                angle

            )

    }};

}}


// ============================================================
// STARS
// ============================================================

function drawStars() {{

    for (

        const star

        of stars

    ) {{

        ctx.beginPath();


        ctx.arc(

            star.x * width,

            star.y * height,

            star.size,

            0,

            Math.PI * 2

        );


        ctx.fillStyle =

            "rgba(255,255,255," +

            (

                .2

                + star.brightness

                * .8

            )

            + ")";


        ctx.fill();

    }}

}}


// ============================================================
// SKY GRID
// ============================================================

function drawSky() {{

    const cx =

        width / 2

        + offsetX;


    const cy =

        height / 2

        + offsetY;


    const radius =

        Math.min(

            width,

            height

        )

        * .40

        * zoom;


    ctx.strokeStyle =

        "rgba(148,163,184,.25)";


    ctx.lineWidth = 1;


    ctx.beginPath();


    ctx.arc(

        cx,

        cy,

        radius,

        0,

        Math.PI * 2

    );


    ctx.stroke();


    for (

        let altitude = 30;

        altitude < 90;

        altitude += 30

    ) {{

        const r =

            radius

            * (

                90

                - altitude

            )

            / 90;


        ctx.beginPath();


        ctx.arc(

            cx,

            cy,

            r,

            0,

            Math.PI * 2

        );


        ctx.stroke();

    }}


    ctx.fillStyle = "white";

    ctx.font = "bold 18px Arial";


    ctx.fillText(

        "N",

        cx - 7,

        cy - radius - 15

    );


    ctx.fillText(

        "E",

        cx + radius + 15,

        cy

    );


    ctx.fillText(

        "S",

        cx - 7,

        cy + radius + 25

    );


    ctx.fillText(

        "W",

        cx - radius - 25,

        cy

    );

}}


// ============================================================
// ORBIT TRAILS
// ============================================================

function drawOrbitTrails() {{

    for (

        const orbit

        of orbitTrails

    ) {{

        if (

            orbit.trail.length < 2

        )

            continue;


        ctx.beginPath();


        let started = false;


        for (

            const point

            of orbit.trail

        ) {{

            if (

                point.altitude <= 0

            )

                continue;


            const p =

                convert(

                    point.altitude,

                    point.azimuth

                );


            if (!started) {{

                ctx.moveTo(

                    p.x,

                    p.y

                );

                started = true;

            }}

            else {{

                ctx.lineTo(

                    p.x,

                    p.y

                );

            }}

        }}


        ctx.strokeStyle =

            "rgba(96,165,250,.25)";


        ctx.lineWidth = 1;


        ctx.stroke();

    }}

}}


// ============================================================
// OBJECTS
// ============================================================

function drawObjects() {{

    for (

        const object

        of objects

    ) {{

        if (

            object.altitude

            <= 0

        )

            continue;


        const p =

            convert(

                object.altitude,

                object.azimuth

            );


        const isSelected =

            selected

            && selected.name

            === object.name;


        let size =

            object.type

            === "Planet"

            ? 10

            : 4;


        if (

            isSelected

        )

            size = 12;


        ctx.beginPath();


        ctx.arc(

            p.x,

            p.y,

            size,

            0,

            Math.PI * 2

        );


        ctx.fillStyle =

            object.type

            === "Planet"

            ? "#facc15"

            : "#60a5fa";


        ctx.shadowBlur =

            isSelected

            ? 25

            : 8;


        ctx.shadowColor =

            object.type

            === "Planet"

            ? "#facc15"

            : "#60a5fa";


        ctx.fill();


        ctx.shadowBlur = 0;


        if (

            object.type

            === "Planet"

            || isSelected

        ) {{

            ctx.fillStyle =

                "white";


            ctx.font =

                "12px Arial";


            ctx.fillText(

                object.name,

                p.x + 12,

                p.y

            );

        }}

    }}

}}


// ============================================================
// RENDER LOOP
// ============================================================

function render() {{

    ctx.fillStyle =

        "#020617";


    ctx.fillRect(

        0,

        0,

        width,

        height

    );


    drawStars();


    drawSky();


    drawOrbitTrails();


    drawObjects();


    requestAnimationFrame(

        render

    );

}}


render();


// ============================================================
// SEARCH
// ============================================================

document

.getElementById(

    "search"

)

.addEventListener(

    "input",

    function(event) {{

        const query =

            event.target.value

            .toLowerCase();


        if (

            query.length === 0

        ) {{

            selected = null;

            return;

        }}


        const result =

            objects.find(

                object =>

                    object.name

                    .toLowerCase()

                    .includes(

                        query

                    )

            );


        if (

            result

        ) {{

            selectObject(

                result

            );

        }}

    }}

);


// ============================================================
// CLICK SELECT
// ============================================================

canvas.addEventListener(

    "click",

    function(event) {{

        let closest = null;


        let closestDistance = 30;


        for (

            const object

            of objects

        ) {{

            if (

                object.altitude

                <= 0

            )

                continue;


            const p =

                convert(

                    object.altitude,

                    object.azimuth

                );


            const distance =

                Math.hypot(

                    event.clientX

                    - p.x,

                    event.clientY

                    - p.y

                );


            if (

                distance

                < closestDistance

            ) {{

                closest =

                    object;


                closestDistance =

                    distance;

            }}

        }}


        if (

            closest

        )

            selectObject(

                closest

            );

    }}

);


// ============================================================
// INFORMATION PANEL
// ============================================================

function selectObject(

    object

) {{

    selected = object;


    document

    .getElementById(

        "info"

    )

    .style.display =

        "block";


    document

    .getElementById(

        "objectName"

    )

    .innerText =

        object.name;


    document

    .getElementById(

        "objectType"

    )

    .innerText =

        object.type;


    document

    .getElementById(

        "objectAltitude"

    )

    .innerText =

        Number(

            object.altitude

        ).toFixed(

            3

        )

        + "°";


    document

    .getElementById(

        "objectAzimuth"

    )

    .innerText =

        Number(

            object.azimuth

        ).toFixed(

            3

        )

        + "°";


    document

    .getElementById(

        "objectDistance"

    )

    .innerText =

        Number(

            object.distance

        ).toFixed(

            2

        )

        + " km";

}}


// ============================================================
// ZOOM
// ============================================================

function zoomIn() {{

    zoom *= 1.25;

}}


function zoomOut() {{

    zoom /= 1.25;

}}


function resetView() {{

    zoom = 1;

    offsetX = 0;

    offsetY = 0;

}}


// ============================================================
// PAN
// ============================================================

let dragging = false;

let lastX = 0;

let lastY = 0;


canvas.addEventListener(

    "mousedown",

    function(event) {{

        dragging = true;

        lastX =

            event.clientX;

        lastY =

            event.clientY;

    }}

);


window.addEventListener(

    "mouseup",

    function() {{

        dragging = false;

    }}

);


canvas.addEventListener(

    "mousemove",

    function(event) {{

        if (

            !dragging

        )

            return;


        offsetX +=

            event.clientX

            - lastX;


        offsetY +=

            event.clientY

            - lastY;


        lastX =

            event.clientX;


        lastY =

            event.clientY;

    }}

);


// ============================================================
// TIME
// ============================================================

let simulationTime =

    Date.now();


function toggleTime() {{

    paused =

        !paused;

}}


function changeSpeed(

    direction

) {{

    if (

        direction

        > 0

    )

        speed *= 2;


    else

        speed /= 2;


    speed = Math.max(

        .125,

        Math.min(

            speed,

            64

        )

    );

}}


setInterval(

    function() {{

        if (

            !paused

        ) {{

            simulationTime +=

                1000

                * speed;

        }}


        const date =

            new Date(

                simulationTime

            );


        document

        .getElementById(

            "clock"

        )

        .innerText =

            date.toUTCString()

            + " | "

            + speed

            + "×";

    }},

    1000

);


</script>


</body>

</html>

"""


display(

    HTML(

        app

    )

)
