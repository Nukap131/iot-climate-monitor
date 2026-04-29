import json
import sqlite3
from pathlib import Path
from datetime import datetime
import paho.mqtt.client as mqtt

BASE_DIR = Path(__file__).resolve().parent.parent
DB_FILE = BASE_DIR / "database" / "sensor_data.db"

MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "lager/teknikrum/sensorer"

def init_db():
    DB_FILE.parent.mkdir(exist_ok=True)

    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS sensor_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            temperature REAL,
            humidity REAL,
            gas INTEGER,
            motor INTEGER,
            alarm INTEGER
        )
    """)

    conn.commit()
    conn.close()
    print(f"Database klar: {DB_FILE}")

def save_data(data):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO sensor_data
        (timestamp, temperature, humidity, gas, motor, alarm)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().isoformat(timespec="seconds"),
        data.get("temperature"),
        data.get("humidity"),
        data.get("gas"),
        data.get("motor"),
        data.get("alarm")
    ))

    conn.commit()
    conn.close()
    print("Data gemt i SQLite")

def on_connect(client, userdata, flags, reason_code, properties=None):
    print(f"Forbundet til MQTT broker. Code: {reason_code}")
    client.subscribe(MQTT_TOPIC)
    print(f"Abonnerer på topic: {MQTT_TOPIC}")

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        print("Modtaget:", payload)
        save_data(payload)
    except Exception as e:
        print("Fejl:", e)

print("Starter MQTT → SQLite backend...")
init_db()

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message

client.connect(MQTT_BROKER, MQTT_PORT, 60)

print("Venter på MQTT-beskeder...")
client.loop_forever()
