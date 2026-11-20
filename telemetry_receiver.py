import json
import paho.mqtt.client as mqtt


BROKER = "localhost"
PORT = 1883
TOPIC = "vehicle/VEH001/telemetry"


def on_connect(client, userdata, flags, rc):

    if rc == 0:

        print("Connected to MQTT broker")

        client.subscribe(TOPIC)

        print(f"Subscribed to: {TOPIC}")

    else:

        print(
            "Connection failed with code:",
            rc
        )


def on_message(client, userdata, msg):

    try:

        # MQTT payload arrives as bytes.
        # Convert bytes → text → Python dictionary.
        data = json.loads(
            msg.payload.decode()
        )


        print("\n---------------- VEHICLE TELEMETRY ----------------")

        print(
            f"Speed:             "
            f"{data['speed_kmh']:.2f} km/h"
        )

        print(
            f"Acceleration:      "
            f"{data['acceleration_mps2']:.3f} m/s²"
        )

        print(
            f"Gear:              "
            f"{data['gear']}"
        )

        print(
            f"Engine RPM:        "
            f"{data['engine_rpm']:.0f} rpm"
        )

        print(
            f"Wheel RPM:         "
            f"{data['wheel_rpm']:.1f} rpm"
        )

        print(
            f"Throttle:          "
            f"{data['throttle_percent']:.1f}%"
        )

        print(
            f"Brake:             "
            f"{data['brake_percent']:.1f}%"
        )

        print(
            f"Engine Torque:     "
            f"{data['engine_torque_nm']:.1f} Nm"
        )

        print(
            f"Tractive Force:    "
            f"{data['tractive_force_n']:.1f} N"
        )

        print(
            f"Brake Force:       "
            f"{data['brake_force_n']:.1f} N"
        )

        print(
            f"Engine Braking:    "
            f"{data['engine_braking_force_n']:.1f} N"
        )

        print(
            f"Aero Drag:         "
            f"{data['aerodynamic_drag_n']:.1f} N"
        )

        print(
            f"Rolling Resistance:"
            f" {data['rolling_resistance_n']:.1f} N"
        )

        print(
            f"Coolant:           "
            f"{data['coolant_temp_c']:.1f} °C"
        )

        print(
            f"Fuel:              "
            f"{data['fuel_level_percent']:.2f}%"
        )

        print(
            f"Battery:           "
            f"{data['battery_voltage_v']:.2f} V"
        )


    except (json.JSONDecodeError, KeyError) as error:

        print(
            "Invalid telemetry message:",
            error
        )


client = mqtt.Client()

client.on_connect = on_connect
client.on_message = on_message

client.connect(
    BROKER,
    PORT,
    60
)

client.loop_forever()