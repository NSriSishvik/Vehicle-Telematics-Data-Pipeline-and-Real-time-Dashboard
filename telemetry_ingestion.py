import json
import sqlite3
import paho.mqtt.client as mqtt


# --------------------------------------------------
# MQTT CONFIGURATION
# --------------------------------------------------

BROKER = "localhost"
PORT = 1883

TOPIC = "vehicle/VEH001/telemetry"


# --------------------------------------------------
# SQLITE DATABASE CONFIGURATION
# --------------------------------------------------

DATABASE = "telemetry.db"


# --------------------------------------------------
# CREATE DATABASE CONNECTION
# --------------------------------------------------

connection = sqlite3.connect(DATABASE)

cursor = connection.cursor()


# --------------------------------------------------
# CREATE TELEMETRY TABLE
# --------------------------------------------------

cursor.execute("""
CREATE TABLE IF NOT EXISTS telemetry (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    vehicle_id TEXT,

    timestamp REAL,

    speed_kmh REAL,

    acceleration_mps2 REAL,

    gear INTEGER,

    engine_rpm REAL,

    wheel_rpm REAL,

    throttle_percent REAL,

    brake_percent REAL,

    engine_torque_nm REAL,

    tractive_force_n REAL,

    brake_force_n REAL,

    engine_braking_force_n REAL,

    aerodynamic_drag_n REAL,

    rolling_resistance_n REAL,

    coolant_temp_c REAL,

    fuel_level_percent REAL,

    battery_voltage_v REAL
)
""")


connection.commit()


print("SQLite database initialized successfully.")
print(f"Database file: {DATABASE}")


# --------------------------------------------------
# MQTT CONNECTION CALLBACK
# --------------------------------------------------

def on_connect(client, userdata, flags, rc):

    if rc == 0:

        print("Connected to MQTT broker")

        client.subscribe(TOPIC)

        print(f"Subscribed to topic: {TOPIC}")

    else:

        print(
            "Connection failed with code:",
            rc
        )


# --------------------------------------------------
# MQTT MESSAGE CALLBACK
# --------------------------------------------------

def on_message(client, userdata, msg):

    try:

        # MQTT messages arrive as bytes.
        # Decode bytes -> text -> Python dictionary.

        data = json.loads(
            msg.payload.decode()
        )


        # ----------------------------------------------
        # INSERT TELEMETRY INTO SQLITE DATABASE
        # ----------------------------------------------

        cursor.execute("""

        INSERT INTO telemetry (

            vehicle_id,
            timestamp,

            speed_kmh,
            acceleration_mps2,

            gear,
            engine_rpm,
            wheel_rpm,

            throttle_percent,
            brake_percent,

            engine_torque_nm,

            tractive_force_n,
            brake_force_n,
            engine_braking_force_n,

            aerodynamic_drag_n,
            rolling_resistance_n,

            coolant_temp_c,
            fuel_level_percent,
            battery_voltage_v

        )

        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

        """,

        (

            data["vehicle_id"],
            data["timestamp"],

            data["speed_kmh"],
            data["acceleration_mps2"],

            data["gear"],
            data["engine_rpm"],
            data["wheel_rpm"],

            data["throttle_percent"],
            data["brake_percent"],

            data["engine_torque_nm"],

            data["tractive_force_n"],
            data["brake_force_n"],
            data["engine_braking_force_n"],

            data["aerodynamic_drag_n"],
            data["rolling_resistance_n"],

            data["coolant_temp_c"],
            data["fuel_level_percent"],
            data["battery_voltage_v"]

        ))


        # Save the inserted record permanently.

        connection.commit()


        # ----------------------------------------------
        # TERMINAL CONFIRMATION
        # ----------------------------------------------

        print(
            f"Stored telemetry | "
            f"Vehicle: {data['vehicle_id']} | "
            f"Speed: {data['speed_kmh']:.1f} km/h | "
            f"RPM: {data['engine_rpm']:.0f}"
        )


    except json.JSONDecodeError:

        print("Invalid JSON message received.")


    except KeyError as error:

        print(
            "Missing telemetry field:",
            error
        )


    except sqlite3.Error as error:

        print(
            "SQLite database error:",
            error
        )


# --------------------------------------------------
# CREATE MQTT CLIENT
# --------------------------------------------------

client = mqtt.Client()


client.on_connect = on_connect

client.on_message = on_message


# --------------------------------------------------
# CONNECT TO MQTT BROKER
# --------------------------------------------------

client.connect(

    BROKER,
    PORT,
    60

)


# --------------------------------------------------
# START RECEIVING MESSAGES
# --------------------------------------------------

print("Telemetry ingestion pipeline running...")

client.loop_forever()