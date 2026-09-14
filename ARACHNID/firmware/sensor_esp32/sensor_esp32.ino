/*
  FINAL DIRECT-WIFI BRAIN GATEWAY
  ARACHNID Sensor ESP32 #2 Firmware
  
  Architecture:
  SOFTWARE (Wi-Fi TCP) <--> BRAIN ESP32 <--> (UART) <--> ROVER ESP32
  
  Responsibilities:
  - Start Wi-Fi AP (ARACHNID, 192.168.4.1) and TCP server (Port 80)
  - Read 5x Ultrasonic sensors continuously
  - Sweep ToF sensor via Servo (30 to 150 degrees)
  - Transmit canonical JSON telemetry ('sensor_telemetry') to software
  - Receive ASCII movement commands (FORWARD, BACKWARD, etc.) from software
  - Forward ASCII commands over UART to Rover ESP32
  - DO NOT make autonomous navigation decisions
*/

#include <Adafruit_VL53L0X.h>
#include <ArduinoJson.h>
#include <WiFi.h>
#include <Wire.h>
#include <ESP32Servo.h>

// ================= Pin Configuration =================

// Ultrasonic Pins
#define TRIG_PIN 25
#define US_FRONT 32     // us_fc_mm
#define US_45_LEFT 27   // us_fl_mm
#define US_45_RIGHT 35  // us_fr_mm
#define US_LEFT 34      // us_l_mm
#define US_RIGHT 33     // us_r_mm

// I2C Pins (ToF)
#define TOF_SDA 21
#define TOF_SCL 22

// Servo Pin
#define SERVO_PIN 14

// UART to ESP32 #1 (Motor Controller)
#define PIN_UART2_RX 18 // Brain RX <- Rover TX (GPIO25)
#define PIN_UART2_TX 19 // Brain TX -> Rover RX (GPIO26)

// AESAR Environmental Sensor Pins (Hardware-team configuration-driven: -1 = unassigned)
#define PIN_DHT22 -1
#define PIN_SOIL_MOISTURE -1

// ================= Hardware Objects =================
Adafruit_VL53L0X lox = Adafruit_VL53L0X();
Servo tofServo;

// ================= Wi-Fi Configuration =================
const char *ssid = "ARACHNID";
const char *password = "arachnid123";
IPAddress local_ip(192, 168, 4, 1);
IPAddress gateway(192, 168, 4, 1);
IPAddress subnet(255, 255, 255, 0);
WiFiServer server(80);
WiFiClient currentClient;

// ================= State & Timing =================
unsigned long seq_num = 0;

// Ultrasonic State Machine
const int NUM_US = 5;
const int us_pins[NUM_US] = {US_FRONT, US_45_LEFT, US_45_RIGHT, US_LEFT, US_RIGHT};
int current_us_index = 0;
unsigned long us_trigger_time = 0;
bool us_waiting_echo = false;

// ISR Variables for Ultrasonic
volatile unsigned long isr_echo_start = 0;
volatile unsigned long isr_echo_duration = 0;
volatile bool isr_echo_ready = false;

// Cached Sensor Values (3000.0 means max range, -1.0 means invalid/timeout)
float cached_us[NUM_US] = {3000.0, 3000.0, 3000.0, 3000.0, 3000.0};

bool tof_ok = true;

// Servo Sweeping
int servo_angle = 90;
int servo_dir = 1;
unsigned long last_servo_time = 0;
const unsigned long SERVO_STEP_MS = 15;

// ================= ISR Function =================
void IRAM_ATTR echo_isr() {
  unsigned long now = micros();
  int pin_state = digitalRead(us_pins[current_us_index]);

  if (pin_state == HIGH) {
    isr_echo_start = now;
  } else {
    if (isr_echo_start != 0) {
      isr_echo_duration = now - isr_echo_start;
      isr_echo_ready = true;
    }
  }
}

// ================= Helper Functions =================
void process_ultrasonics() {
  unsigned long now_us = micros();

  if (!us_waiting_echo) {
    int echo_pin = us_pins[current_us_index];

    // Trigger all sensors via shared TRIG_PIN
    digitalWrite(TRIG_PIN, LOW);
    delayMicroseconds(2);
    digitalWrite(TRIG_PIN, HIGH);
    delayMicroseconds(10);
    digitalWrite(TRIG_PIN, LOW);

    isr_echo_start = 0;
    isr_echo_duration = 0;
    isr_echo_ready = false;

    attachInterrupt(digitalPinToInterrupt(echo_pin), echo_isr, CHANGE);

    us_trigger_time = now_us;
    us_waiting_echo = true;
  } else {
    int echo_pin = us_pins[current_us_index];

    if (isr_echo_ready) {
      detachInterrupt(digitalPinToInterrupt(echo_pin));

      // Calculate distance (Speed of sound = 343 m/s)
      float dist = (isr_echo_duration * 0.343) / 2.0;
      
      if (dist < 20.0 || dist > 4000.0) {
        dist = -1.0; // Mark invalid (out of bounds)
      }

      cached_us[current_us_index] = dist;

      us_waiting_echo = false;
      current_us_index = (current_us_index + 1) % NUM_US;

    } else if (now_us - us_trigger_time > 24000) { // ~24ms timeout (~4m)
      detachInterrupt(digitalPinToInterrupt(echo_pin));

      cached_us[current_us_index] = -1.0; // Mark invalid (timeout)

      us_waiting_echo = false;
      current_us_index = (current_us_index + 1) % NUM_US;
    }
  }
}

void process_servo_and_tof() {
  unsigned long now = millis();
  if (now - last_servo_time >= SERVO_STEP_MS) {
    last_servo_time = now;

    // Update Servo Position
    servo_angle += (2 * servo_dir);
    if (servo_angle >= 150) {
      servo_angle = 150;
      servo_dir = -1;
    } else if (servo_angle <= 30) {
      servo_angle = 30;
      servo_dir = 1;
    }
    tofServo.write(servo_angle);

    // Read ToF Distance
    float dist_mm = -1.0;
    if (tof_ok) {
      VL53L0X_RangingMeasurementData_t measure;
      lox.rangingTest(&measure, false);
      
      if (measure.RangeStatus != 4) { // 4 means out of range
        dist_mm = measure.RangeMilliMeter;
        if (dist_mm < 10.0 || dist_mm > 2000.0) {
          dist_mm = -1.0;
        }
      }
    }
    
    // Output Canonical Telemetry JSON Format
    StaticJsonDocument<512> doc;
    doc["type"] = "sensor_telemetry";
    doc["timestamp_ms"] = now;
    doc["seq"] = seq_num++;
    doc["us_fc_mm"] = cached_us[0];
    doc["us_fl_mm"] = cached_us[1];
    doc["us_fr_mm"] = cached_us[2];
    doc["us_l_mm"] = cached_us[3];
    doc["us_r_mm"] = cached_us[4];
    doc["tof_angle_deg"] = servo_angle;
    doc["tof_distance_mm"] = dist_mm;

    // AESAR Environmental Sensor Object
    JsonObject env = doc.createNestedObject("environment");
    if (PIN_DHT22 != -1 || PIN_SOIL_MOISTURE != -1) {
      env["available"] = true;
      // Real reads will populate when hardware pins are physically connected
    } else {
      env["temperature_c"] = (char*)NULL;
      env["humidity_percent"] = (char*)NULL;
      env["soil_moisture_raw"] = (char*)NULL;
      env["soil_moisture_percent"] = (char*)NULL;
      env["timestamp"] = (char*)NULL;
      env["available"] = false;
    }
    
    String telemetry_str;
    serializeJson(doc, telemetry_str);
    
    // Send to Serial for debugging, and TCP client if connected
    Serial.println(telemetry_str);
    if (currentClient && currentClient.connected()) {
      currentClient.println(telemetry_str);
    }
  }
}

void emergency_stop_motors() {
  // If Wi-Fi disconnects, explicitly send STOP ASCII command to Rover ESP32
  Serial2.println("STOP");
  Serial.println("EMERGENCY STOP INVOKED - SENT STOP TO MOTORS");
}

// ================= Setup =================
void setup() {
  // Debug Serial
  Serial.begin(115200);
  while (!Serial && millis() < 2000) delay(10);
  Serial.println("\nInitializing Brain ESP32 Gateway...");

  // UART to Rover Motor Controller
  Serial2.begin(115200, SERIAL_8N1, PIN_UART2_RX, PIN_UART2_TX);

  // Init Wi-Fi SoftAP
  WiFi.softAPConfig(local_ip, gateway, subnet);
  WiFi.softAP(ssid, password);
  server.begin();
  Serial.println("Wi-Fi AP Started: ARACHNID (192.168.4.1:80)");
  
  // Configure Ultrasonic Pins
  pinMode(TRIG_PIN, OUTPUT);
  digitalWrite(TRIG_PIN, LOW);
  pinMode(US_FRONT, INPUT);
  pinMode(US_45_LEFT, INPUT);
  pinMode(US_45_RIGHT, INPUT);
  pinMode(US_LEFT, INPUT);
  pinMode(US_RIGHT, INPUT);

  // Configure ToF
  Wire.begin(TOF_SDA, TOF_SCL);
  Wire.setClock(400000);
  if (!lox.begin(0x29, false, &Wire)) {
    Serial.println("Warning: VL53L0X ToF not found!");
    tof_ok = false;
  }
  
  // Configure Servo
  tofServo.setPeriodHertz(50);
  tofServo.attach(SERVO_PIN, 500, 2400);
  tofServo.write(servo_angle);
}

// ================= Main Loop =================
void loop() {
  // Handle Wi-Fi Client Connection
  if (server.hasClient()) {
    if (!currentClient || !currentClient.connected()) {
      if (currentClient) currentClient.stop();
      currentClient = server.available();
      Serial.println("Software backend connected via TCP.");
    } else {
      WiFiClient newClient = server.available();
      newClient.stop(); // Only allow one client
    }
  }

  // Handle Client Disconnect
  if (currentClient && !currentClient.connected()) {
    currentClient.stop();
    Serial.println("Software backend disconnected.");
    emergency_stop_motors(); // Ensure rover stops if connection drops
  }

  // 1. Advance Ultrasonic State Machine
  process_ultrasonics();

  // 2. Process Servo Sweep and Transmit Telemetry
  process_servo_and_tof();

  // 3. Transparent Command Bridge (Wi-Fi TCP -> Motor Controller UART)
  if (currentClient && currentClient.connected()) {
    while (currentClient.available()) {
      char c = currentClient.read();
      Serial2.write(c); // Forward byte to Rover
      Serial.write(c);  // Echo to local debug serial
    }
  }

  // 4. Fallback Command Bridge (Local USB -> Motor Controller UART)
  while (Serial.available()) {
    char c = Serial.read();
    Serial2.write(c);
  }

  // 5. Motor Controller -> Wi-Fi/USB (Feedback/Logs)
  while (Serial2.available()) {
    char c = Serial2.read();
    Serial.write(c);
    if (currentClient && currentClient.connected()) {
      currentClient.write(c);
    }
  }
}
