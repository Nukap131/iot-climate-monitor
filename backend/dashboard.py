import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px
import paho.mqtt.client as mqtt

from pathlib import Path
from streamlit_autorefresh import st_autorefresh

# =========================
# Auto refresh
# =========================
st_autorefresh(interval=3000, key="refresh")

# =========================
# Database
# =========================
BASE_DIR = Path(__file__).resolve().parent.parent
DB_FILE = BASE_DIR / "database" / "sensor_data.db"

# =========================
# Streamlit setup
# =========================
st.set_page_config(page_title="IoT Climate Monitor", layout="wide")

st.title("Sensorbaseret miljøovervågningsystem")

# =========================
# MQTT control
# =========================
MQTT_BROKER = "localhost"
MQTT_TOPIC_CONTROL = "lager/teknikrum/control"

def send_command(command):
    client = mqtt.Client()
    client.connect(MQTT_BROKER, 1883, 60)
    client.publish(MQTT_TOPIC_CONTROL, command)
    client.disconnect()

# =========================
# Load data
# =========================
@st.cache_data(ttl=5)
def load_data():

    conn = sqlite3.connect(DB_FILE)

    df = pd.read_sql_query("""
        SELECT timestamp, temperature, humidity, gas, motor, alarm
        FROM sensor_data
        ORDER BY timestamp ASC
    """, conn)

    conn.close()

    df["timestamp"] = pd.to_datetime(df["timestamp"])

    # sidste 10 min
    df = df[df["timestamp"] >= pd.Timestamp.now() - pd.Timedelta(hours=2)]

    return df

df = load_data()

if df.empty:
    st.warning("Ingen live data fundet. Tjek at ESP32 og mqtt_to_sqlite.py kører.")
    st.stop()

latest = df.iloc[-1]

# =========================
# Metrics
# =========================
c1, c2, c3, c4 = st.columns(4)

c1.metric("Temperatur", f"{latest['temperature']} °C")
c2.metric("Gasniveau", int(latest["gas"]))
c3.metric("Motor", "ON" if latest["motor"] == 1 else "OFF")
c4.metric("Alarm", "ALARM" if latest["alarm"] == 1 else "Normal")

# =========================
# System control
# =========================
st.subheader("Systemstyring")

colA, colB = st.columns(2)

with colA:
    if st.button("Tænd system"):
        send_command("ON")
        st.success("System tændt")

with colB:
    if st.button("Sluk system"):
        send_command("OFF")
        st.warning("System slukket")

# =========================
# Temperatur graf
# =========================
fig_temp = px.line(
    df,
    x="timestamp",
    y="temperature",
    title="Temperatur"
)

fig_temp.update_xaxes(
    tickformat="%H:%M",
    dtick=1800000
)

fig_temp.add_hline(
    y=25,
    line_dash="dash",
    line_color="red",
    annotation_text="25°C grænse"
)

st.plotly_chart(fig_temp, use_container_width=True)

# =========================
# Gas graf
# =========================
fig_gas = px.line(
    df,
    x="timestamp",
    y="gas",
    title="Gasniveau"
)

fig_gas.update_xaxes(
    tickformat="%H:%M",
    dtick=1800000
)

fig_gas.add_hline(
    y=400,
    line_dash="dash",
    line_color="red",
    annotation_text="400 grænse"
)

st.plotly_chart(fig_gas, use_container_width=True)

# =========================
# Alarmstatus
# =========================
st.subheader("Alarmstatus")

if latest["alarm"] == 1:
    st.error("🚨 Alarm aktiv!")
else:
    st.success("✅ System OK")

# =========================
# Daglig maksimum temperatur og gas - denne måned
# =========================
st.subheader("Daglig maksimum temperatur og gas – denne måned")

conn = sqlite3.connect(DB_FILE)

monthly_df = pd.read_sql_query("""
    SELECT timestamp, temperature, gas
    FROM sensor_data
    WHERE timestamp >= date('now', 'start of month')
    ORDER BY timestamp ASC
""", conn)

conn.close()

monthly_df["timestamp"] = pd.to_datetime(monthly_df["timestamp"])
monthly_df["date"] = monthly_df["timestamp"].dt.strftime("%d-%m-%Y")

daily_summary = monthly_df.groupby("date").agg({
    "temperature": "max",
    "gas": "max"
}).reset_index()

daily_summary["date_sort"] = pd.to_datetime(
    daily_summary["date"],
    format="%d-%m-%Y"
)

daily_summary = daily_summary.sort_values("date_sort")

col_temp, col_gas = st.columns(2)

with col_temp:
    fig_daily_temp = px.bar(
        daily_summary,
        x="date",
        y="temperature",
        title="Højeste temperatur pr. dag denne måned",
        labels={"date": "Dato", "temperature": "Maks temperatur °C"}
    )
    fig_daily_temp.update_xaxes(type="category")
    st.plotly_chart(fig_daily_temp, width="stretch")

with col_gas:
    fig_daily_gas = px.bar(
        daily_summary,
        x="date",
        y="gas",
        title="Højeste gasniveau pr. dag denne måned",
        labels={"date": "Dato", "gas": "Maks gasniveau"}
    )
    fig_daily_gas.update_xaxes(type="category")
    st.plotly_chart(fig_daily_gas, width="stretch")

# =========================
# Data tabel
# =========================
st.subheader("Data tabel – sidste 50 målinger")

last_50 = df.tail(50)

st.dataframe(last_50)

# =========================
# Alarmhistorik
# =========================
st.subheader("Alarmhistorik")

alarm_history = df[df["alarm"] == 1].copy()

if alarm_history.empty:
    st.success("Ingen alarmer registreret.")
else:
    alarm_history = alarm_history.tail(50)

    st.dataframe(alarm_history)

# =========================
# Download alarmhistorik
# =========================
st.subheader("Download alarmhistorik")

if alarm_history.empty:
    st.info("Ingen alarmer at downloade.")
else:

    export_df = alarm_history.copy()

    export_df["timestamp"] = export_df["timestamp"].dt.strftime(
        "%d-%m-%Y %H:%M:%S"
    )

    csv = export_df.to_csv(
        index=False,
        sep=";",
        decimal=","
    )

    st.download_button(
        label="Download alarmhistorik (seneste 50)",
        data=csv,
        file_name="alarmhistorik.csv",
        mime="text/csv"
    )
