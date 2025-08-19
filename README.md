# AquaSync 🚰📶

**AquaSync** is an IoT-enabled liquid balancer system for two tanks using a Raspberry Pi Pico W and MQTT. It continuously monitors water levels and manages the transfer of liquid between tanks using a peristaltic pump. Data is published to an MQTT broker and visualized on a custom web dashboard, where users can view historical volume trends, pump activity, and tank states over time.

---

## 🧰 Components

| Component               | Quantity | Purpose                                                 |
|------------------------|----------|---------------------------------------------------------|
| Raspberry Pi Pico W    | 1        | Microcontroller with Wi-Fi support                      |
| HC-SR04 Ultrasonic Sensor | 2     | Measure water height in each tank                       |
| Peristaltic Pump        | 1        | Transfer liquid between tanks                           |
| L298N Motor Driver      | 1        | Drive the peristaltic pump from the Pico W              |
| Red LED                 | 3        | Indicate tank is almost full (≤ 0.5 cm from sensor)     |
| Yellow LED              | 3        | Indicate tank is above half but not near full          |
| Green LED               | 3        | Indicate tank is below half capacity                   |
| Blue LED                | 1        | Blinks when pump is active                             |
| Male-to-Male Jumper Wires | ~10   | Wiring connections                                      |
| Female-to-Male Jumper Wires | ~10 | Wiring connections                                      |

---

## 🌊 How It Works

1. **Level Measurement**  
   Each tank has an HC-SR04 ultrasonic sensor that measures the distance from the water surface to the sensor. The measured height is used to calculate the current volume.

2. **Volume Status LEDs**  
   Each tank is equipped with:
   - **Red LEDs**: Tank is near full (≤ 0.5 cm from the sensor)
   - **Yellow LEDs**: Tank is above half but not near full
   - **Green LEDs**: Tank is below half capacity  
   The LED indicators provide at-a-glance visual feedback on water levels.

3. **Pump Control**  
   A peristaltic pump, controlled by the L298N motor driver, transfers liquid from one tank to another when needed. The **blue LED** blinks while the pump is active.

4. **MQTT Communication**  
   The Pico W sends real-time data over Wi-Fi to an MQTT broker. This includes tank levels, pump state, and timestamps.

5. **Dashboard Visualization**  
   A custom web dashboard displays:
   - Current and historical tank volumes
   - Pump operation time
   - A timeline of volume levels and states using interactive charts

---

## 🖥️ Dashboard Features

- Real-time tank volume display
- Historical volume trends with graphs
- Pump activity logging
- System status (LED/state indicator)
- Hosted on a live website for monitoring

---

## 📦 Folder Structure
```bash
/AquaSync
├── /src # MicroPython code for Pico W 
├── /lib # Libraries for the MicroPython code
├── /docs # System diagrams
├── README.md
```

## 🌐 Access the Dashboard

AquaSync includes a live dashboard hosted at:

**🔗 [http://liquidbalancer.mooo.com/](http://liquidbalancer.mooo.com/)**

If you would like to use the dashboard to publish and visualize your own tank data via MQTT, please **open an issue in this repository** to request access. Include a brief description of your setup and intended use.

---
