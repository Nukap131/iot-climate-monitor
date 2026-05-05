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
source iot-venv/bin/activate
cd ~/iot-climate-monitor
python backend/mqtt_to_sqlite.py

//Start Streamlit i anden terminal//
source iot-venv/bin/activate
cd ~/iot-climate-monitor
streamlit run backend/dashboard.py --server.address 0.0.0.0 --server.port 8501
//Åbn webbrowser: http://192.168.197.229:8501
```
## ESP32
## Upload via PlatformIO:
```bash
pio run --target upload --upload-port /dev/ttyUSB0
```
## Systemarkitektur
ESP32 → MQTT → Python → SQLite → Streamlit

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

## Visualisering af data
Grafana indeholder tre grafer: Temperatur, gasniveau og alarmstatus. Når Temperatur overstiger 25 grader så er alarm slået til, samt når gasniveau når 400. Man kan se i grafer røde streger, det betyder at alarmen går i gang, når man krydser streger.
Men efter at have testet Grafanas stabiletet var jeg nødt til at droppet det, da dens nøjagtighed med live var ustabil. Efter temperatur har været over 25 og alarmen har gået i gang, så sidder de fast i over alarm linjen begge alarm og temperatur. Men jeg fandt hurtigt en anden løsning, jeg bruger i stedet Streamlit til visualisering, den fungerer fint, men den skal tilpasses til projektet, så den får bedre udseende og funktioner.
