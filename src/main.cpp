#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <DHT.h>

// ---------- WIFI ----------
const char* ssid = "MomsSpaghetti";
const char* password = "Bustu313";

// ---------- MQTT ----------
const char* mqtt_server = "192.168.197.229";
const int mqtt_port = 1883;
const char* mqtt_topic = "lager/teknikrum/sensorer";
const char* mqtt_control_topic = "lager/teknikrum/control";

// ---------- SENSOR ----------
#define DHTPIN 4
#define DHTTYPE DHT11
#define GAS_PIN 34

// ---------- MOTOR ----------
#define MOTOR_IN1 26
#define MOTOR_IN2 27

DHT dht(DHTPIN, DHTTYPE);
WiFiClient espClient;
PubSubClient client(espClient);

// ---------- LIMITS ----------
const float TEMP_LIMIT = 25.0;
const int GAS_LIMIT = 400;

// ---------- SYSTEM STATE ----------
bool systemEnabled = true;

// ---------- MOTOR ----------
void motorStart() {
  digitalWrite(MOTOR_IN1, HIGH);
  digitalWrite(MOTOR_IN2, LOW);
}

void motorStop() {
  digitalWrite(MOTOR_IN1, LOW);
  digitalWrite(MOTOR_IN2, LOW);
}

// ---------- MQTT CALLBACK ----------
void callback(char* topic, byte* payload, unsigned int length) {
  String message;

  for (int i = 0; i < length; i++) {
    message += (char)payload[i];
  }

  Serial.print("MQTT command received: ");
  Serial.println(message);

  if (message == "OFF") {
    systemEnabled = false;
    motorStop();
    Serial.println("System disabled");
  }

  if (message == "ON") {
    systemEnabled = true;
    Serial.println("System enabled");
  }
}

// ---------- WIFI ----------
void setup_wifi() {
  delay(10);
  Serial.println("Connecting to WiFi...");

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nWiFi connected");
  Serial.println(WiFi.localIP());
}

// ---------- MQTT ----------
void reconnect() {
  while (!client.connected()) {
    Serial.print("Connecting to MQTT...");
    if (client.connect("ESP32Client")) {
      Serial.println("connected");
      client.subscribe(mqtt_control_topic);
      Serial.println("Subscribed to control topic");
    } else {
      Serial.print("failed, rc=");
      Serial.println(client.state());
      delay(2000);
    }
  }
}

// ---------- SETUP ----------
void setup() {
  Serial.begin(115200);

  dht.begin();

  pinMode(MOTOR_IN1, OUTPUT);
  pinMode(MOTOR_IN2, OUTPUT);
  motorStop();

  setup_wifi();

  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);

  Serial.println("System starter...");
}

// ---------- LOOP ----------
void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  if (!systemEnabled) {
    motorStop();

    String payload = "{";
    payload += "\"temperature\":0,";
    payload += "\"humidity\":0,";
    payload += "\"gas\":0,";
    payload += "\"motor\":0,";
    payload += "\"alarm\":0,";
    payload += "\"system\":\"OFF\"";
    payload += "}";

    Serial.println(payload);
    client.publish(mqtt_topic, payload.c_str());

    delay(5000);
    return;
  }

  float temp = dht.readTemperature();
  float hum = dht.readHumidity();
  int gasValue = analogRead(GAS_PIN);

  if (isnan(temp) || isnan(hum)) {
    Serial.println("DHT sensor error");
    delay(2000);
    return;
  }

  bool highTemp = temp > TEMP_LIMIT;
  bool gasDetected = gasValue > GAS_LIMIT;

  int motorState = 0;
  int alarm = 0;

  if (highTemp || gasDetected) {
    motorStart();
    motorState = 1;
    alarm = 1;
  } else {
    motorStop();
  }

  String payload = "{";
  payload += "\"temperature\":" + String(temp, 1) + ",";
  payload += "\"humidity\":" + String(hum, 1) + ",";
  payload += "\"gas\":" + String(gasValue) + ",";
  payload += "\"motor\":" + String(motorState) + ",";
  payload += "\"alarm\":" + String(alarm) + ",";
  payload += "\"system\":\"ON\"";
  payload += "}";

  Serial.println(payload);
  client.publish(mqtt_topic, payload.c_str());

  delay(5000);
}
