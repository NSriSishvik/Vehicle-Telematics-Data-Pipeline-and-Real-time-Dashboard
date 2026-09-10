# Vehicle-Telematics-Data-Pipeline-and-Real-time-Dashboard
A Python-based vehicle telematics prototype that simulates vehicle data, transmits it using MQTT, stores the telemetry in SQLite, and visualizes the data through a real-time Streamlit dashboard.
This project demonstrates a basic end-to-end vehicle telematics data pipeline:

Vehicle Simulator → MQTT → Mosquitto Broker → Telemetry Ingestion → SQLite → Streamlit Dashboard

The system simulates vehicle operating conditions such as:

- Vehicle speed
- Acceleration
- Engine RPM
- Wheel RPM
- Gear
- Throttle position
- Brake input
- Engine torque
- Tractive force
- Engine braking force
- Aerodynamic drag
- Rolling resistance
- Coolant temperature
- Fuel level
- Battery voltage

The simulated vehicle model is based on a Ford EcoSport 1.0L EcoBoost 125 PS configuration, with vehicle and transmission parameters used to make the simulation more physically meaningful rather than generating completely random sensor values.

Tech stack used:
Python – Vehicle simulation and data processing
Paho MQTT – MQTT communication
Mosquitto – MQTT broker
SQLite – Local telemetry storage
Pandas – Telemetry data processing
Streamlit – Interactive dashboard
streamlit-autorefresh – Automatic dashboard refresh
