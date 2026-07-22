# Hardware Wiring & Interface Guide

This document details the hardware setup, pin connections, component selection, and electrical specifications for the **Smart Environment Monitor**.

---

## 1. Pin Mapping Table

| ESP32 GPIO Pin | Connected Component | Component Pin | Function / Notes |
| :--- | :--- | :--- | :--- |
| **3.3V / VIN** | DHT22 Sensor | Pin 1 (VCC) | 3.3V - 5.0V Power Supply Rail |
| **GPIO 15** | DHT22 Sensor | Pin 2 (DATA) | Single-bus Digital Telemetry Input |
| **NC** | DHT22 Sensor | Pin 3 (NC) | Not Connected |
| **GND** | DHT22 Sensor | Pin 4 (GND) | System Ground Connection |
| **GPIO 2** | Blue Status LED | Anode (+) | Onboard / External Connection Indicator |
| **GND** | 220Ω Resistor → LED | Cathode (-) | Current Limiting Resistor to GND |

---

## 2. Signal Integrity & Passive Components

1. **Pull-Up Resistor ($R_1 = 10\text{ k}\Omega$)**:
   - A $10\text{ k}\Omega$ pull-up resistor must be connected between `DHT22 Pin 2 (DATA)` and `VCC (3.3V)` to keep the single-bus data line pulled HIGH during idle states.
2. **Decoupling Capacitor ($C_1 = 0.1\,\mu\text{F}$)**:
   - A $0.1\,\mu\text{F}$ ceramic capacitor placed across `VCC` and `GND` right near the DHT22 sensor pins filters high-frequency noise caused by Wi-Fi RF power spikes on the 3.3V power rail.

---

## 3. Schematic Diagram (ASCII)

```text
       +------------------------------------+
       |              ESP32                 |
       |                                    |
       |  3.3V  GPIO15     GPIO2      GND   |
       +---|-------|---------|---------|----+
           |       |         |         |
           |   +---+---+     |         |
           |   |       |     |         |
          [R1 10k]    |     [LED]      |
           |   |       |     |         |
           |   |       |    [R2 220R]  |
           |   |       |     |         |
       +---|---|-------|-----|---------|----+
       |  Pin1 Pin2   Pin3  Anode    Cathode|
       | (VCC) (DATA) (NC)   |         |    |
       |     DHT22 Sensor    +---------+    |
       |     (Pin 4 = GND) -----------------+
       +------------------------------------+
```

---

## 4. Power Consumption Profile

| Mode | Active Modules | Current Draw @ 3.3V | Power (mW) |
| :--- | :--- | :--- | :--- |
| **Wi-Fi TX Burst** | ESP32 CPU (240MHz) + Wi-Fi Radio TX | ~160 - 240 mA | ~528 - 792 mW |
| **Idle / Sampling** | ESP32 CPU (80MHz) + DHT22 Read | ~80 mA | ~264 mW |
| **Modem Sleep** | ESP32 CPU Active, Wi-Fi Sleep | ~20 - 30 mA | ~66 - 99 mW |
| **Deep Sleep (Optional)**| RTC Controller + ULP | ~10 - 15 $\mu$A | ~33 - 50 $\mu$W |
