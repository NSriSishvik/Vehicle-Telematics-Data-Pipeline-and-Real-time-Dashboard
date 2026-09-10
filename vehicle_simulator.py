import time
import json
import math
import paho.mqtt.client as mqtt


# ============================================================
# MQTT
# ============================================================

BROKER = "localhost"
PORT = 1883
TOPIC = "vehicle/VEH001/telemetry"


# ============================================================
# REFERENCE VEHICLE
#
# Ford EcoSport 1.0 EcoBoost 125 PS, 6-speed manual
#
# Published parameters are identified below.
# Model assumptions are explicitly marked.
# ============================================================

VEHICLE = {

    "vehicle_id": "VEH001",

    # -----------------------------
    # Published vehicle data
    # -----------------------------

    "mass_kg": 1349.0,

    "wheel_radius_m": 0.3262,

    "idle_rpm": 860.0,

    "max_engine_rpm": 6500.0,

    "fuel_tank_l": 52.0,


    # -----------------------------
    # Published transmission data
    # -----------------------------

    "gear_ratios": {
        1: 4.584,
        2: 2.964,
        3: 1.912,
        4: 1.446,
        5: 1.000,
        6: 0.746
    },

    "final_drive_ratio": 3.440,


    # -----------------------------
    # MODEL ASSUMPTIONS
    # -----------------------------

    # This is drivetrain mechanical efficiency,
    # NOT engine thermal efficiency.
    "drivetrain_efficiency": 0.90,

    "drag_coefficient": 0.32,

    "frontal_area_m2": 2.25,

    "rolling_resistance_coefficient": 0.012,

    "air_density_kg_m3": 1.225,

    "max_brake_force_n": 9000.0,

    # Approximate fuel model parameter.
    # This is deliberately labelled an assumption.
    "bsfc_g_per_kwh": 280.0
}


# ============================================================
# ENGINE TORQUE MODEL
# ============================================================
#
# Ford publishes:
#
# 170 Nm @ 1500–4500 rpm
#
# We therefore preserve that directly.
#
# Outside that range, the values below are MODEL
# ASSUMPTIONS/interpolations rather than published Ford data.
# ============================================================

TORQUE_CURVE = [

    (860, 120),
    (1000, 140),

    # Published maximum torque region
    (1500, 170),
    (2000, 170),
    (2500, 170),
    (3000, 170),
    (3500, 170),
    (4000, 170),
    (4500, 170),

    # Model assumptions above published torque range
    (5000, 165),
    (5500, 157),
    (6000, 146),
    (6500, 135)
]


# ============================================================
# MQTT CLIENT
# ============================================================

client = mqtt.Client()

client.connect(
    BROKER,
    PORT,
    60
)

client.loop_start()


# ============================================================
# VEHICLE STATE
# ============================================================

speed_mps = 0.0

gear = 1

throttle = 0.0
brake = 0.0

clutch_engaged = True

fuel_level_l = VEHICLE["fuel_tank_l"]

coolant_temp_c = 20.0

simulation_time = 0.0


# ============================================================
# TORQUE INTERPOLATION
# ============================================================

def interpolate_torque(rpm):

    if rpm <= TORQUE_CURVE[0][0]:
        return TORQUE_CURVE[0][1]

    if rpm >= TORQUE_CURVE[-1][0]:
        return TORQUE_CURVE[-1][1]

    for i in range(len(TORQUE_CURVE) - 1):

        rpm1, torque1 = TORQUE_CURVE[i]
        rpm2, torque2 = TORQUE_CURVE[i + 1]

        if rpm1 <= rpm <= rpm2:

            fraction = (
                (rpm - rpm1)
                / (rpm2 - rpm1)
            )

            return (
                torque1
                + fraction * (torque2 - torque1)
            )

    return TORQUE_CURVE[-1][1]


# ============================================================
# WHEEL RPM
# ============================================================

def calculate_wheel_rpm(speed):

    circumference = (
        2
        * math.pi
        * VEHICLE["wheel_radius_m"]
    )

    wheel_rps = speed / circumference

    return wheel_rps * 60.0


# ============================================================
# ENGINE RPM
# ============================================================

def calculate_engine_rpm(
    wheel_rpm,
    current_gear
):

    if not clutch_engaged:

        return VEHICLE["idle_rpm"]

    ratio = VEHICLE["gear_ratios"][current_gear]

    rpm = (
        wheel_rpm
        * ratio
        * VEHICLE["final_drive_ratio"]
    )

    return max(
        VEHICLE["idle_rpm"],
        min(
            rpm,
            VEHICLE["max_engine_rpm"]
        )
    )


# ============================================================
# AERODYNAMIC DRAG
# ============================================================

def calculate_aerodynamic_drag(speed):

    rho = VEHICLE["air_density_kg_m3"]
    cd = VEHICLE["drag_coefficient"]
    area = VEHICLE["frontal_area_m2"]

    return (
        0.5
        * rho
        * cd
        * area
        * speed ** 2
    )


# ============================================================
# ROLLING RESISTANCE
# ============================================================

def calculate_rolling_resistance():

    crr = VEHICLE[
        "rolling_resistance_coefficient"
    ]

    mass = VEHICLE["mass_kg"]

    gravity = 9.81

    return crr * mass * gravity


# ============================================================
# ENGINE BRAKING
# ============================================================

def calculate_engine_braking(
    engine_rpm,
    throttle,
    current_gear
):

    if not clutch_engaged:
        return 0.0

    if throttle > 2.0:
        return 0.0

    # Simplified closed-throttle engine resistance.
    #
    # This is a MODEL ASSUMPTION, not a published
    # Ford engine-friction map.

    if engine_rpm < 1200:
        braking_torque = 10.0

    elif engine_rpm < 2500:
        braking_torque = 18.0

    elif engine_rpm < 4000:
        braking_torque = 25.0

    else:
        braking_torque = 30.0

    wheel_torque = (
        braking_torque
        * VEHICLE["gear_ratios"][current_gear]
        * VEHICLE["final_drive_ratio"]
        * VEHICLE["drivetrain_efficiency"]
    )

    return (
        wheel_torque
        / VEHICLE["wheel_radius_m"]
    )


# ============================================================
# DRIVER / DRIVE CYCLE
# ============================================================

def driver_inputs(t):

    global gear

    cycle_time = t % 70.0


    # --------------------------------------------------------
    # 0–5 sec: idle / launch
    # --------------------------------------------------------

    if cycle_time < 3:

        gear = 1

        return 20.0, 0.0


    # --------------------------------------------------------
    # 3–18 sec: acceleration
    # --------------------------------------------------------

    elif cycle_time < 18:

        if speed_mps < 8.0:
            gear = 1

        elif speed_mps < 15.0:
            gear = 2

        elif speed_mps < 23.0:
            gear = 3

        elif speed_mps < 32.0:
            gear = 4

        else:
            gear = 5

        return 55.0, 0.0


    # --------------------------------------------------------
    # 18–30 sec: cruise
    # --------------------------------------------------------

    elif cycle_time < 30:

        return 20.0, 0.0


    # --------------------------------------------------------
    # 30–38 sec: throttle lift
    # --------------------------------------------------------

    elif cycle_time < 38:

        return 0.0, 0.0


    # --------------------------------------------------------
    # 38–43 sec: downshift + engine braking
    # --------------------------------------------------------

    elif cycle_time < 43:

        if speed_mps > 20:
            gear = 4

        return 0.0, 0.0


    # --------------------------------------------------------
    # 43–50 sec: conventional braking
    # --------------------------------------------------------

    elif cycle_time < 50:

        return 0.0, 30.0


    # --------------------------------------------------------
    # 50–55 sec: stopped / idle
    # --------------------------------------------------------

    elif cycle_time < 55:

        return 0.0, 0.0


    # --------------------------------------------------------
    # 55–70 sec: restart and accelerate again
    # --------------------------------------------------------

    else:

        gear = 1

        return 35.0, 0.0


# ============================================================
# SIMULATION STEP
# ============================================================

DT = 0.1


while True:

    # --------------------------------------------------------
    # DRIVER INPUT
    # --------------------------------------------------------

    throttle, brake = driver_inputs(
        simulation_time
    )


    # --------------------------------------------------------
    # ROTATIONAL SPEED
    # --------------------------------------------------------

    wheel_rpm = calculate_wheel_rpm(
        speed_mps
    )

    engine_rpm = calculate_engine_rpm(
        wheel_rpm,
        gear
    )


    # --------------------------------------------------------
    # ENGINE TORQUE
    # --------------------------------------------------------

    engine_torque = interpolate_torque(
        engine_rpm
    )

    requested_engine_torque = (
        engine_torque
        * throttle
        / 100.0
    )


    # --------------------------------------------------------
    # TRANSMISSION
    # --------------------------------------------------------

    wheel_torque = (
        requested_engine_torque
        * VEHICLE["gear_ratios"][gear]
        * VEHICLE["final_drive_ratio"]
        * VEHICLE["drivetrain_efficiency"]
    )


    # --------------------------------------------------------
    # TRACTIVE FORCE
    # --------------------------------------------------------

    tractive_force = (
        wheel_torque
        / VEHICLE["wheel_radius_m"]
    )


    # --------------------------------------------------------
    # BRAKING FORCE
    # --------------------------------------------------------

    brake_force = (
        brake
        / 100.0
        * VEHICLE["max_brake_force_n"]
    )


    # --------------------------------------------------------
    # ROAD LOAD
    # --------------------------------------------------------

    aerodynamic_drag = (
        calculate_aerodynamic_drag(
            speed_mps
        )
    )

    rolling_resistance = (
        calculate_rolling_resistance()
    )


    # --------------------------------------------------------
    # ENGINE BRAKING
    # --------------------------------------------------------

    engine_braking_force = (
        calculate_engine_braking(
            engine_rpm,
            throttle,
            gear
        )
    )


    # --------------------------------------------------------
    # NET FORCE
    # --------------------------------------------------------

    net_force = (

        tractive_force

        - brake_force

        - aerodynamic_drag

        - rolling_resistance

        - engine_braking_force
    )


    # --------------------------------------------------------
    # VEHICLE ACCELERATION
    # --------------------------------------------------------

    acceleration = (
        net_force
        / VEHICLE["mass_kg"]
    )


    # --------------------------------------------------------
    # UPDATE SPEED
    # --------------------------------------------------------

    speed_mps += acceleration * DT

    speed_mps = max(
        0.0,
        speed_mps
    )


    # ========================================================
    # FUEL CONSUMPTION
    # ========================================================
    #
    # Fuel model based on engine power and assumed BSFC.
    #
    # This is an engineering approximation, not a Ford
    # measured fuel-flow map.
    # ========================================================

    engine_power_kw = (
        engine_torque
        * engine_rpm
        / 9550.0
    )

    useful_engine_power_kw = (
        engine_power_kw
        * throttle
        / 100.0
    )

    fuel_mass_flow_g_per_s = (
        useful_engine_power_kw
        * VEHICLE["bsfc_g_per_kwh"]
        / 3600.0
    )

    fuel_density_kg_per_l = 0.745

    fuel_l_per_s = (
        fuel_mass_flow_g_per_s
        / 1000.0
        / fuel_density_kg_per_l
    )

    fuel_level_l -= (
        fuel_l_per_s * DT
    )

    fuel_level_l = max(
        0.0,
        fuel_level_l
    )


    # ========================================================
    # COOLANT TEMPERATURE
    # ========================================================
    #
    # Simple thermal state rather than RPM directly becoming
    # temperature.
    # ========================================================

    heat_input = (
        useful_engine_power_kw
        * 0.002
    )

    cooling = (
        (coolant_temp_c - 20.0)
        * 0.0005
    )

    coolant_temp_c += (
        heat_input
        - cooling
    )

    coolant_temp_c = max(
        20.0,
        min(
            coolant_temp_c,
            105.0
        )
    )


    # ========================================================
    # BATTERY / ALTERNATOR
    # ========================================================

    if engine_rpm > 1000:

        target_voltage = 14.1

    else:

        target_voltage = 12.5


    battery_voltage = (
        target_voltage
    )


    # ========================================================
    # TELEMETRY
    # ========================================================

    data = {

        "vehicle_id":
            VEHICLE["vehicle_id"],

        "timestamp":
            time.time(),

        "simulation_time":
            round(simulation_time, 1),

        "speed_kmh":
            round(
                speed_mps * 3.6,
                2
            ),

        "acceleration_mps2":
            round(
                acceleration,
                3
            ),

        "wheel_rpm":
            round(
                wheel_rpm,
                1
            ),

        "engine_rpm":
            round(
                engine_rpm,
                0
            ),

        "gear":
            gear,

        "throttle_percent":
            round(
                throttle,
                1
            ),

        "brake_percent":
            round(
                brake,
                1
            ),

        "clutch_engaged":
            clutch_engaged,

        "engine_torque_nm":
            round(
                engine_torque,
                1
            ),

        "tractive_force_n":
            round(
                tractive_force,
                1
            ),

        "brake_force_n":
            round(
                brake_force,
                1
            ),

        "engine_braking_force_n":
            round(
                engine_braking_force,
                1
            ),

        "aerodynamic_drag_n":
            round(
                aerodynamic_drag,
                1
            ),

        "rolling_resistance_n":
            round(
                rolling_resistance,
                1
            ),

        "coolant_temp_c":
            round(
                coolant_temp_c,
                1
            ),

        "fuel_level_percent":
            round(
                fuel_level_l
                / VEHICLE["fuel_tank_l"]
                * 100.0,
                2
            ),

        "fuel_level_l":
            round(
                fuel_level_l,
                3
            ),

        "battery_voltage_v":
            round(
                battery_voltage,
                2
            )
    }


    # ========================================================
    # MQTT
    # ========================================================

    message = json.dumps(data)

    client.publish(
        TOPIC,
        message
    )


    # ========================================================
    # LOCAL CONSOLE
    # ========================================================

    print(
        f"t={simulation_time:6.1f}s | "
        f"Speed={data['speed_kmh']:6.2f} km/h | "
        f"Gear={gear} | "
        f"RPM={engine_rpm:5.0f} | "
        f"Throttle={throttle:5.1f}% | "
        f"Brake={brake:5.1f}% | "
        f"Fuel={data['fuel_level_percent']:6.2f}%"
    )


    simulation_time += DT

    time.sleep(DT)