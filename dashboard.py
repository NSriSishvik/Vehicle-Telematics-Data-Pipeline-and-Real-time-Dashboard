import streamlit.components.v1 as components
import streamlit as st
import urllib.parse
import math
import sqlite3
import pandas as pd
from streamlit_autorefresh import st_autorefresh


def draw_analogue_gauge(value, title, unit, max_value, redline=None):
    """Draw an analogue gauge with a dynamic red needle."""

    value = max(0, min(float(value or 0), max_value))

    width, height = 320, 260
    cx, cy, radius = 160, 145, 100

    def point(r, angle):
        rad = math.radians(angle)
        return (
            cx + r * math.cos(rad),
            cy - r * math.sin(rad)
        )

    def arc_path(r, start, end):
        x1, y1 = point(r, start)
        x2, y2 = point(r, end)
        large_arc = 1 if abs(end - start) > 180 else 0

        return (
            f"M {x1:.2f} {y1:.2f} "
            f"A {r} {r} 0 {large_arc} 1 "
            f"{x2:.2f} {y2:.2f}"
        )

    start_angle = 180
    end_angle = 0
    value_angle = start_angle + (value / max_value) * (
        end_angle - start_angle
    )

    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" rx="18" fill="#17191d"/>',
        '<text x="160" y="25" text-anchor="middle" '
        'fill="#ffffff" font-size="17" font-weight="bold">'
        f'{title}</text>',
        f'<path d="{arc_path(radius, start_angle, end_angle)}" '
        'fill="none" stroke="#555b65" stroke-width="13" '
        'stroke-linecap="round"/>'
    ]

    # Red zone on the RPM gauge
    if redline is not None:
        red_angle = start_angle + (
            redline / max_value
        ) * (end_angle - start_angle)

        svg.append(
            f'<path d="{arc_path(radius, red_angle, end_angle)}" '
            'fill="none" stroke="#e53935" stroke-width="13" '
            'stroke-linecap="round"/>'
        )

    # Tick marks and labels
    
    # Tick marks and labels
    tick_step = 1000 if max_value >= 1000 else 20
    tick_count = int(max_value / tick_step)

    for i in range(tick_count + 1):
        tick_value = i * tick_step
        fraction = tick_value / max_value

        angle = start_angle + fraction * (
            end_angle - start_angle
        )

        x1, y1 = point(88, angle)
        x2, y2 = point(103, angle)
        tx, ty = point(78, angle)

        tick_color = (
            "#ff5252"
            if redline is not None and tick_value >= redline
            else "#ffffff"
        )

        label = (
            str(tick_value // 1000)
            if max_value >= 1000
            else str(tick_value)
        )

        svg.append(
            f'<line x1="{x1:.2f}" y1="{y1:.2f}" '
            f'x2="{x2:.2f}" y2="{y2:.2f}" '
            f'stroke="{tick_color}" stroke-width="2"/>'
        )

        svg.append(
            f'<text x="{tx:.2f}" y="{ty + 4:.2f}" '
            'text-anchor="middle" fill="#ffffff" font-size="11">'
            f'{label}</text>'
        )


    
    
    # Red needle
    nx, ny = point(78, value_angle)

    svg.extend([
        f'<line x1="{cx}" y1="{cy}" '
        f'x2="{nx:.2f}" y2="{ny:.2f}" '
        'stroke="#ff3030" stroke-width="4" '
        'stroke-linecap="round"/>',

        f'<circle cx="{cx}" cy="{cy}" r="8" fill="#ff3030"/>',

        f'<text x="{cx}" y="205" text-anchor="middle" '
        'fill="#ffffff" font-size="25" font-weight="bold">'
        f'{value:,.0f}</text>',

        f'<text x="{cx}" y="226" text-anchor="middle" '
        'fill="#b8c0cc" font-size="13">'
        f'{unit}</text>',

        '</svg>'
    ])

    # Convert the SVG list into an HTML string
    svg_content = "".join(svg)

    # Render the gauge
    

    st.iframe(
    svg_content,
    height=280,
    width=320
)



# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Vehicle Telematics Dashboard",
    page_icon="🚗",
    layout="wide"
)

# --------------------------------------------------
# AUTOMATIC REFRESH
# --------------------------------------------------

st_autorefresh(
    interval=1000,
    key="telemetry_refresh"
)

# --------------------------------------------------
# DATABASE CONFIGURATION
# --------------------------------------------------

DATABASE = "telemetry.db"


# --------------------------------------------------
# GET LATEST TELEMETRY
# --------------------------------------------------

def get_latest_telemetry():

    connection = sqlite3.connect(DATABASE)

    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM telemetry
        ORDER BY id DESC
        LIMIT 1
    """)

    row = cursor.fetchone()

    column_names = [
        description[0]
        for description in cursor.description
    ]

    connection.close()

    if row is None:
        return None

    return dict(zip(column_names, row))

# --------------------------------------------------
# GET TELEMETRY HISTORY
# --------------------------------------------------

def get_telemetry_history(limit=100):

    connection = sqlite3.connect(DATABASE)

    query = f"""
        SELECT *
        FROM telemetry
        ORDER BY id DESC
        LIMIT {limit}
    """

    dataframe = pd.read_sql_query(
        query,
        connection
    )

    connection.close()

    dataframe = dataframe.iloc[::-1]

    dataframe["timestamp"] = pd.to_datetime(dataframe["timestamp"], unit="s")

    return dataframe

# --------------------------------------------------
# DETERMINE VEHICLE OPERATING STATE
# --------------------------------------------------

def get_vehicle_state(data):

    speed = data["speed_kmh"]
    acceleration = data["acceleration_mps2"]
    brake = data["brake_percent"]
    engine_braking = data["engine_braking_force_n"]

    if speed < 1.0:

        return "IDLE"

    elif brake > 0:

        return "BRAKING"

    elif engine_braking > 100:

        return "ENGINE BRAKING"

    elif acceleration > 0.3:

        return "ACCELERATING"

    elif acceleration < -0.3:

        return "DECELERATING"

    else:

        return "CRUISING"

# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------

st.title("🚗 Vehicle Telematics Dashboard")

st.caption("Real-time vehicle telemetry monitoring")


latest_data = get_latest_telemetry()


if latest_data is None:

    st.warning(
        "No telemetry data found. "
        "Please start the vehicle simulator and telemetry ingestion service."
    )

else:

    st.success(
        f"Connected to telemetry database | "
        f"Vehicle: {latest_data['vehicle_id']}"
    )

    vehicle_state = get_vehicle_state(latest_data)

    st.info(
    f"Vehicle State: {vehicle_state}"
    )

    # ----------------------------------------------
    # ANALOGUE GAUGES
    # ----------------------------------------------

    rpm = latest_data["engine_rpm"]
    speed = latest_data["speed_kmh"]

    gauge_col1, gauge_col2 = st.columns(2)

    with gauge_col1:
        draw_analogue_gauge(
            value=rpm,
            title="TACHOMETER",
            unit="x1000 RPM",
            max_value=8000,
            redline=6500
        )

    with gauge_col2:
        draw_analogue_gauge(
            value=speed,
            title="SPEEDOMETER",
            unit="km/h",
            max_value=220
        )

    # ----------------------------------------------
    # KPI ROW 1
    # ----------------------------------------------

    col1, col2, col3, col4 = st.columns(4)


    with col1:

        st.metric(
            "Speed",
            f"{latest_data['speed_kmh']:.1f} km/h"
        )


    with col2:

        st.metric(
            "Engine RPM",
            f"{latest_data['engine_rpm']:.0f} rpm"
        )


    with col3:

        st.metric(
            "Gear",
            latest_data["gear"]
        )


    with col4:

        st.metric(
            "Engine Torque",
            f"{latest_data['engine_torque_nm']:.1f} Nm"
        )


    # ----------------------------------------------
    # KPI ROW 2
    # ----------------------------------------------

    col5, col6, col7, col8 = st.columns(4)


    with col5:

        st.metric(
            "Throttle",
            f"{latest_data['throttle_percent']:.1f}%"
        )


    with col6:

        st.metric(
            "Brake",
            f"{latest_data['brake_percent']:.1f}%"
        )


    with col7:

        st.metric(
            "Fuel Level",
            f"{latest_data['fuel_level_percent']:.1f}%"
        )


    with col8:

        st.metric(
            "Coolant Temperature",
            f"{latest_data['coolant_temp_c']:.1f} °C"
        )


    # ----------------------------------------------
    # EXPANDABLE RAW DATA
    # ----------------------------------------------

    with st.expander("View Latest Raw Telemetry"):

        st.json(latest_data)

# --------------------------------------------------
# TELEMETRY HISTORY
# --------------------------------------------------

st.divider()

st.header("Telemetry History")


history_data = get_telemetry_history(100)


# ----------------------------------------------
# SPEED HISTORY
# ----------------------------------------------

st.subheader("Vehicle Speed")

st.line_chart(
    history_data,
    x="timestamp",
    y="speed_kmh"
)


# ----------------------------------------------
# ENGINE RPM HISTORY
# ----------------------------------------------

st.subheader("Engine RPM")

st.line_chart(
    history_data,
    x="timestamp",
    y="engine_rpm"
)


# ----------------------------------------------
# DRIVER INPUTS
# ----------------------------------------------

st.subheader("Driver Inputs")

st.line_chart(
    history_data,
    x="timestamp",
    y=[
        "throttle_percent",
        "brake_percent"
    ]
)


# ----------------------------------------------
# FUEL LEVEL HISTORY
# ----------------------------------------------

st.subheader("Fuel Level")

st.line_chart(
    history_data,
    x="timestamp",
    y="fuel_level_percent"
)


# ----------------------------------------------
# COOLANT TEMPERATURE HISTORY
# ----------------------------------------------

st.subheader("Coolant Temperature")

st.line_chart(
    history_data,
    x="timestamp",
    y="coolant_temp_c"
)

    