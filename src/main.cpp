#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <DHT.h>

// ---------- WIFI ----------
const char* ssid = "MomsSpaghetti";
const char* password = "Bustu313";

// ---------- MQTT ----------
const char* mqtt_server = "192.168.197.229"; // din Debian IP
const int mqtt_port = 1883;
const char* mqtt_topic = "lager/teknikrum/sensorer";

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

// ---------- MOTOR ----------
void motorStart() {
  digitalWrite(MOTOR_IN1, HIGH);
  digitalWrite(MOTOR_IN2, LOW);
}

void motorStop() {
  digitalWrite(MOTOR_IN1, LOW);
  digitalWrite(MOTOR_IN2, LOW);
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
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
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

  Serial.println("System starter...");
}

// ---------- LOOP ----------
void loop() {

  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  float temp = dht.readTemperature();
  float hum = dht.readHumidity();
  int gasValue = analogRead(GAS_PIN);

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

  // ---------- JSON ----------
  String payload = "{";
  payload += "\"temperature\":" + String(temp) + ",";
  payload += "\"humidity\":" + String(hum) + ",";
  payload += "\"gas\":" + String(gasValue) + ",";
  payload += "\"motor\":" + String(motorState) + ",";
  payload += "\"alarm\":" + String(alarm);
  payload += "}";

  Serial.println(payload);

  client.publish(mqtt_topic, payload.c_str());

  delay(5000);
}
