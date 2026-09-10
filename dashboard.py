import streamlit as st
import sqlite3
import pandas as pd
from streamlit_autorefresh import st_autorefresh

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

    