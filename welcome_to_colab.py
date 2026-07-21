# -*- coding: utf-8 -*-

import streamlit as st
import json
import random

st.set_page_config(
    page_title="KISHANSKY OBSERVATORY",
    layout="wide"
)

# ---------------------------------------------------------
# LOAD DATA
# ---------------------------------------------------------

try:
    planet_data = planet_df.to_dict(orient="records")
except:
    planet_data = []

try:
    satellite_data = satellite_df.to_dict(orient="records")
except:
    satellite_data = []

# ---------------------------------------------------------
# NORMALIZE DATA
# ---------------------------------------------------------

def normalize_object(obj, default_type):

    name = (
        obj.get("name")
        or obj.get("Name")
        or obj.get("OBJECT_NAME")
        or obj.get("object_name")
        or "Unknown Object"
    )

    altitude = (
        obj.get("altitude")
        or obj.get("Altitude")
        or obj.get("ALTITUDE")
        or 0
    )

    azimuth = (
        obj.get("azimuth")
        or obj.get("Azimuth")
        or obj.get("AZIMUTH")
        or 0
    )

    distance = (
        obj.get("distance")
        or obj.get("Distance")
        or obj.get("DISTANCE")
        or 0
    )

    try:
        altitude = float(altitude)
    except:
        altitude = 45

    try:
        azimuth = float(azimuth)
    except:
        azimuth = random.uniform(0, 360)

    try:
        distance = float(distance)
    except:
        distance = 0

    return {
        "name": str(name),
        "type": obj.get("type", default_type),
        "altitude": altitude,
        "azimuth": azimuth,
        "distance": distance
    }


planets = [
    normalize_object(obj, "Planet")
    for obj in planet_data
]

satellites = [
    normalize_object(obj, "Satellite")
    for obj in satellite_data
]

# ---------------------------------------------------------
# DEMO OBJECTS IF DATA IS EMPTY
# ---------------------------------------------------------

if len(planets) == 0:

    planets = [
        {
            "name": "Mars",
            "type": "Planet",
            "altitude": 45,
            "azimuth": 30,
            "distance": 225000000
        },
        {
            "name": "Jupiter",
            "type": "Planet",
            "altitude": 60,
            "azimuth": 130,
            "distance": 700000000
        },
        {
            "name": "Saturn",
            "type": "Planet",
            "altitude": 35,
            "azimuth": 240,
            "distance": 1300000000
        }
    ]

if len(satellites) == 0:

    satellites = [
        {
            "name": "ISS",
            "type": "Satellite",
            "altitude": 50,
            "azimuth": 90,
            "distance": 420
        },
        {
            "name": "STARLINK",
            "type": "Satellite",
            "altitude": 25,
            "azimuth": 200,
            "distance": 550
        }
    ]

planets_json = json.dumps(planets)
satellites_json = json.dumps(satellites)

# ---------------------------------------------------------
# HTML APPLICATION
# ---------------------------------------------------------

app = f"""

<!DOCTYPE html>

<html>

<head>

<meta charset="UTF-8">

<style>

html, body {{

    margin: 0;

    padding: 0;

    overflow: hidden;

    background: black;

}}

#app {{

    position: relative;

    width: 100vw;

    height: 850px;

    overflow: hidden;

    background:

    radial-gradient(

        circle at center,

        #172554 0%,

        #020617 45%,

        #000000 100%

    );

}}

#sky {{

    position: absolute;

    left: 0;

    top: 0;

    width: 100%;

    height: 100%;

    cursor: grab;

}}

#sky:active {{

    cursor: grabbing;

}}

#title {{

    position: absolute;

    top: 20px;

    left: 25px;

    color: white;

    font-family: Arial;

    font-size: 25px;

    font-weight: bold;

    z-index: 10;

    text-shadow:

        0 0 10px #38bdf8,

        0 0 20px #38bdf8;

}}

#info {{

    position: absolute;

    right: 25px;

    top: 75px;

    width: 280px;

    padding: 20px;

    color: white;

    background: rgba(0,0,0,.88);

    border: 1px solid #64748b;

    border-radius: 15px;

    font-family: Arial;

    display: none;

    z-index: 20;

    box-shadow: 0 0 30px rgba(255,255,255,.25);

}}

#info h2 {{

    margin-top: 0;

    color: #7dd3fc;

}}

#controls {{

    position: absolute;

    bottom: 25px;

    left: 50%;

    transform: translateX(-50%);

    z-index: 20;

}}

button {{

    padding: 11px 20px;

    margin: 5px;

    border-radius: 8px;

    border: 1px solid #64748b;

    background: #1e293b;

    color: white;

    font-size: 14px;

    cursor: pointer;

}}

button:hover {{

    background: #334155;

}}

</style>

</head>

<body>

<div id="app">

<canvas id="sky"></canvas>

<div id="title">

🌌 KISHANSKY OBSERVATORY

</div>

<div id="info">

<h2 id="name">

Selected Object

</h2>

<p>

Type:

<span id="type"></span>

</p>

<p>

Altitude:

<span id="altitude"></span>

</p>

<p>

Azimuth:

<span id="azimuth"></span>

</p>

<p>

Distance:

<span id="distance"></span>

</p>

</div>

<div id="controls">

<button onclick="zoomIn()">

Zoom In

</button>

<button onclick="zoomOut()">

Zoom Out

</button>

<button onclick="resetView()">

Reset View

</button>

</div>

</div>

<script>


// ---------------------------------------------------------
// CANVAS
// ---------------------------------------------------------

const canvas =

document.getElementById("sky");

const ctx =

canvas.getContext("2d");

let width =

window.innerWidth;

let height =

850;

canvas.width =

width;

canvas.height =

height;


// ---------------------------------------------------------
// APPLICATION STATE
// ---------------------------------------------------------

let zoom = 1;

let offsetX = 0;

let offsetY = 0;

let selected = null;


// ---------------------------------------------------------
// DATA
// ---------------------------------------------------------

const planets =

{planets_json};

const satellites =

{satellites_json};

const objects = [

    ...planets,

    ...satellites

];


// ---------------------------------------------------------
// STARS
// ---------------------------------------------------------

let stars = [];

for (

    let i = 0;

    i < 5000;

    i++

) {{

    stars.push({{

        x: Math.random(),

        y: Math.random(),

        size:

            Math.random() * 2.5 + .3,

        brightness:

            Math.random() * .8 + .2

    }});

}}


// ---------------------------------------------------------
// COORDINATE CONVERSION
// ---------------------------------------------------------

function convert(

    altitude,

    azimuth

) {{

    const cx =

        width / 2 +

        offsetX;

    const cy =

        height / 2 +

        offsetY;

    const radius =

        Math.min(

            width,

            height

        )

        * .38

        * zoom;

    const r =

        radius *

        (90 - altitude)

        / 90;

    const angle =

        (azimuth - 90)

        *

        Math.PI

        / 180;

    return {{

        x:

            cx +

            r *

            Math.cos(angle),

        y:

            cy +

            r *

            Math.sin(angle)

    }};

}}


// ---------------------------------------------------------
// DRAW STARS
// ---------------------------------------------------------

function drawStars(){{

    for (

        let star of stars

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

            star.brightness +

            ")";

        ctx.fill();

    }}

}}


// ---------------------------------------------------------
// DRAW SKY GRID
// ---------------------------------------------------------

function drawSky(){{

    const cx =

        width / 2 +

        offsetX;

    const cy =

        height / 2 +

        offsetY;

    const radius =

        Math.min(

            width,

            height

        )

        * .38

        * zoom;


    ctx.strokeStyle =

        "rgba(100,150,220,.35)";

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

            radius *

            (90 - altitude)

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


    ctx.fillStyle =

        "white";

    ctx.font =

        "bold 18px Arial";


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


// ---------------------------------------------------------
// DRAW OBJECTS
// ---------------------------------------------------------

function drawObjects(){{

    for (

        let object of objects

    ) {{

        let altitude =

            Number(object.altitude);

        let azimuth =

            Number(object.azimuth);


        if (

            isNaN(altitude)

            ||

            isNaN(azimuth)

        )

            continue;


        if (

            altitude <= 0

        )

            continue;


        const p =

            convert(

                altitude,

                azimuth

            );


        const isSelected =

            selected &&

            selected.name ===

            object.name;


        let size =

            object.type ===

            "Planet"

            ? 11

            : 5;


        if (

            isSelected

        )

            size = 15;


        ctx.beginPath();

        ctx.arc(

            p.x,

            p.y,

            size,

            0,

            Math.PI * 2

        );


        ctx.fillStyle =

            object.type ===

            "Planet"

            ? "#ffffff"

            : "#60a5fa";


        ctx.shadowBlur =

            isSelected

            ? 35

            : 15;


        ctx.shadowColor =

            object.type ===

            "Planet"

            ? "white"

            : "#60a5fa";


        ctx.fill();


        ctx.shadowBlur = 0;


        if (

            object.type ===

            "Planet"

            ||

            isSelected

        ) {{

            ctx.fillStyle =

                "white";

            ctx.font =

                "13px Arial";

            ctx.fillText(

                object.name,

                p.x + 15,

                p.y

            );

        }}

    }}

}}


// ---------------------------------------------------------
// RENDER LOOP
// ---------------------------------------------------------

function render(){{

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

    drawObjects();


    requestAnimationFrame(

        render

    );

}}


// ---------------------------------------------------------
// CLICK OBJECT
// ---------------------------------------------------------

canvas.addEventListener(

    "click",

    function(event){{

        let closest =

            null;

        let closestDistance =

            35;


        for (

            let object of objects

        ) {{

            const altitude =

                Number(

                    object.altitude

                );

            const azimuth =

                Number(

                    object.azimuth

                );


            if (

                altitude <= 0

            )

                continue;


            const p =

                convert(

                    altitude,

                    azimuth

                );


            const distance =

                Math.sqrt(

                    (

                        event.clientX -

                        p.x

                    ) ** 2

                    +

                    (

                        event.clientY -

                        p.y

                    ) ** 2

                );


            if (

                distance <

                closestDistance

            ) {{

                closest =

                    object;

                closestDistance =

                    distance;

            }}

        }}


        if (

            closest

        ) {{

            selected =

                closest;


            document.getElementById(

                "info"

            ).style.display =

                "block";


            document.getElementById(

                "name"

            ).innerText =

                closest.name;


            document.getElementById(

                "type"

            ).innerText =

                closest.type;


            document.getElementById(

                "altitude"

            ).innerText =

                Number(

                    closest.altitude

                ).toFixed(3)

                + "°";


            document.getElementById(

                "azimuth"

            ).innerText =

                Number(

                    closest.azimuth

                ).toFixed(3)

                + "°";


            document.getElementById(

                "distance"

            ).innerText =

                Number(

                    closest.distance

                ).toFixed(2)

                + " km";

        }}

    }}

);


// ---------------------------------------------------------
// ZOOM
// ---------------------------------------------------------

function zoomIn(){{

    zoom *= 1.3;

}}

function zoomOut(){{

    zoom /= 1.3;

}}

function resetView(){{

    zoom = 1;

    offsetX = 0;

    offsetY = 0;

}}


// ---------------------------------------------------------
// PAN
// ---------------------------------------------------------

let dragging = false;

let lastX = 0;

let lastY = 0;


canvas.addEventListener(

    "mousedown",

    function(event){{

        dragging = true;

        lastX =

            event.clientX;

        lastY =

            event.clientY;

    }}

);


canvas.addEventListener(

    "mouseup",

    function(){{

        dragging = false;

    }}

);


canvas.addEventListener(

    "mousemove",

    function(event){{

        if (

            !dragging

        )

            return;


        offsetX +=

            event.clientX -

            lastX;

        offsetY +=

            event.clientY -

            lastY;


        lastX =

            event.clientX;

        lastY =

            event.clientY;

    }}

);


// ---------------------------------------------------------
// RESIZE
// ---------------------------------------------------------

window.addEventListener(

    "resize",

    function(){{

        width =

            window.innerWidth;

        canvas.width =

            width;

        canvas.height =

            height;

    }}

);


// START

render();

</script>

</body>

</html>

"""

# ---------------------------------------------------------
# RENDER WITH STREAMLIT
# ---------------------------------------------------------

st.html(app)
