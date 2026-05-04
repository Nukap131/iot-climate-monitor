# iot-climate-monitor
IT-Teknolog 4 semester projekt, udviklet af Nuka Petrussen

## Setup

## Backend
```bash
python3 -m venv iot-venv
source iot-venv/bin/activate
pip install paho-mqtt flask pandas
```
## Start system
```bash
sudo systemctl start mosqtuitto
python backend/mqtt_to_sqlite.py
```
## ESP32
## Upload via PlatformIO:
```bash
pio run --target upload --upload-port /dev/ttyUSB0
```
## Systemarkitektur
ESP32 → MQTT → Python → SQLite → Grafana

## Mappestruktur
iot-climate-monitor/
│
├── src/                # ESP32 kode
├── backend/            # Python MQTT → SQLite
├── database/           # SQLite DB (ikke i git)
├── docs/               # Rapport / billeder
├── CAD/                # 3D modeller
├── platformio.ini
└── README.md

## Grafana
Grafana indeholder tre grafer: Temperatur, gasniveau og alarmstatus. Når Temperatur overstiger 25 grader så er alarm slået til, samt når gasniveau når 400. Man kan se i grafer røde streger, det betyder at alarmen går i gang, når man krydser streger.
