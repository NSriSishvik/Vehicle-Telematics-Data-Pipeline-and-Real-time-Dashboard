# Vehicle-Telematics-Data-Pipeline-and-Real-time-Dashboard with Tachometer
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

<img width="1438" height="845" alt="Screenshot_2026-11-20-16-02-04-35_6012fa4d4ddec268fc5c7112cbb265e7" src="https://github.com/user-attachments/assets/079cbeee-dc9c-47aa-971b-c58034830e39" />




