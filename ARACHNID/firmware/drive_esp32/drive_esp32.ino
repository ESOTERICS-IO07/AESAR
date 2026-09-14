#include <Arduino.h>

// ============================================================
// ARACHNID ROVER ESP32 #1
// ============================================================
// Motor controller for two BTS7960 drivers.
// Commands come from Brain ESP32 #2 over UART.
//
// UART:
//   Rover RX = GPIO 26
//   Rover TX = GPIO 25
//   Baud     = 115200
//
// Commands:
//   FORWARD
//   BACKWARD
//   LEFT
//   RIGHT
//   STOP
//
// Safety:
//   1000 ms hardware command watchdog
//
// Speed:
//   Drive = 30%
//   Turn  = 25%
// ============================================================


// ============================================================
// LEFT BTS7960
// ============================================================

const int PIN_L_RPWM = 4;
const int PIN_L_LPWM = 17;
const int PIN_L_REN  = 23;
const int PIN_L_LEN  = 5;


// ============================================================
// RIGHT BTS7960
// ============================================================

const int PIN_R_RPWM = 22;
const int PIN_R_LPWM = 21;
const int PIN_R_REN  = 18;
const int PIN_R_LEN  = 19;


// ============================================================
// BRAIN ESP32 #2 UART
// ============================================================

const int PIN_UART_RX = 26;
const int PIN_UART_TX = 25;

HardwareSerial BrainSerial(2);


// ============================================================
// SAFETY
// ============================================================

unsigned long last_cmd_time = 0;

const unsigned long WATCHDOG_TIMEOUT_MS = 1000;


// ============================================================
// SPEED LIMITS
// ============================================================

const float DRIVE_SPEED = 0.30;
const float TURN_SPEED  = 0.60;


// ============================================================
// CURRENT MOTOR TARGETS
// ============================================================

float target_left_speed  = 0.0;
float target_right_speed = 0.0;


// ============================================================
// BTS7960 MOTOR CONTROL
// ============================================================

void set_bts7960_speed(
  int rpwm_pin,
  int lpwm_pin,
  int ren_pin,
  int len_pin,
  float speed_norm
) {

  speed_norm = constrain(speed_norm, -1.0, 1.0);

  // -------------------------
  // STOP
  // -------------------------

  if (abs(speed_norm) < 0.01) {

    analogWrite(rpwm_pin, 0);
    analogWrite(lpwm_pin, 0);

    digitalWrite(ren_pin, LOW);
    digitalWrite(len_pin, LOW);

    return;
  }


  // -------------------------
  // ENABLE DRIVER
  // -------------------------

  digitalWrite(ren_pin, HIGH);
  digitalWrite(len_pin, HIGH);


  // -------------------------
  // PWM
  // -------------------------

  int pwm_val = (int)(
    constrain(abs(speed_norm), 0.0, 1.0) * 255.0
  );


  // -------------------------
  // POSITIVE DIRECTION
  // -------------------------

  if (speed_norm > 0) {

    analogWrite(rpwm_pin, pwm_val);
    analogWrite(lpwm_pin, 0);

  }

  // -------------------------
  // NEGATIVE DIRECTION
  // -------------------------

  else {

    analogWrite(rpwm_pin, 0);
    analogWrite(lpwm_pin, pwm_val);
  }
}


// ============================================================
// PROCESS COMMAND FROM BRAIN
// ============================================================

void process_command(String cmd) {

  cmd.trim();

  if (cmd.length() == 0) {
    return;
  }


  // Debug output to USB Serial Monitor

  Serial.print("Received: ");
  Serial.println(cmd);


  // ==========================================================
  // FORWARD
  //
  // Physical polarity:
  // Left  = positive
  // Right = negative
  // ==========================================================

  if (cmd == "FORWARD") {

    target_left_speed  = DRIVE_SPEED;
    target_right_speed = -DRIVE_SPEED;

    last_cmd_time = millis();
  }


  // ==========================================================
  // BACKWARD
  // ==========================================================

  else if (cmd == "BACKWARD") {

    target_left_speed  = -DRIVE_SPEED;
    target_right_speed = DRIVE_SPEED;

    last_cmd_time = millis();
  }


  // ==========================================================
  // LEFT
  // ==========================================================

  else if (cmd == "LEFT") {

    target_left_speed  = -TURN_SPEED;
    target_right_speed = -TURN_SPEED;

    last_cmd_time = millis();
  }


  // ==========================================================
  // RIGHT
  // ==========================================================

  else if (cmd == "RIGHT") {

    target_left_speed  = TURN_SPEED;
    target_right_speed = TURN_SPEED;

    last_cmd_time = millis();
  }


  // ==========================================================
  // STOP
  // ==========================================================

  else if (cmd == "STOP") {

    target_left_speed  = 0.0;
    target_right_speed = 0.0;

    last_cmd_time = millis();
  }


  // ==========================================================
  // UNKNOWN COMMAND
  // ==========================================================

  else {

    target_left_speed  = 0.0;
    target_right_speed = 0.0;

    Serial.println("INVALID COMMAND -> STOP");
  }
}


// ============================================================
// SETUP
// ============================================================

void setup() {

  // USB Serial for debugging

  Serial.begin(115200);


  // Brain ESP32 UART

  BrainSerial.begin(
    115200,
    SERIAL_8N1,
    PIN_UART_RX,
    PIN_UART_TX
  );


  // ==========================================================
  // LEFT BTS7960 PINS
  // ==========================================================

  pinMode(PIN_L_RPWM, OUTPUT);
  pinMode(PIN_L_LPWM, OUTPUT);
  pinMode(PIN_L_REN, OUTPUT);
  pinMode(PIN_L_LEN, OUTPUT);


  // ==========================================================
  // RIGHT BTS7960 PINS
  // ==========================================================

  pinMode(PIN_R_RPWM, OUTPUT);
  pinMode(PIN_R_LPWM, OUTPUT);
  pinMode(PIN_R_REN, OUTPUT);
  pinMode(PIN_R_LEN, OUTPUT);


  // ==========================================================
  // START WITH DRIVERS DISABLED
  // ==========================================================

  digitalWrite(PIN_L_REN, LOW);
  digitalWrite(PIN_L_LEN, LOW);

  digitalWrite(PIN_R_REN, LOW);
  digitalWrite(PIN_R_LEN, LOW);


  analogWrite(PIN_L_RPWM, 0);
  analogWrite(PIN_L_LPWM, 0);

  analogWrite(PIN_R_RPWM, 0);
  analogWrite(PIN_R_LPWM, 0);


  // ==========================================================
  // INITIAL WATCHDOG STATE
  // ==========================================================

  last_cmd_time = millis();


  // ==========================================================
  // STARTUP MESSAGE
  // ==========================================================

  Serial.println();
  Serial.println("=================================");
  Serial.println("ARACHNID Rover ESP32 #1 READY");
  Serial.println("=================================");
  Serial.println("Brain UART RX = GPIO 26");
  Serial.println("Brain UART TX = GPIO 25");
  Serial.println("UART Baud     = 115200");
  Serial.println("Drive Speed   = 30%");
  Serial.println("Turn Speed    = 25%");
  Serial.println("Watchdog      = 1000 ms");
  Serial.println("=================================");
}


// ============================================================
// MAIN LOOP
// ============================================================

void loop() {

  unsigned long now = millis();


  // ==========================================================
  // RECEIVE COMMANDS FROM BRAIN ESP32 #2
  // ==========================================================

  while (BrainSerial.available() > 0) {

    String line = BrainSerial.readStringUntil('\n');

    line.trim();

    process_command(line);
  }


  // ==========================================================
  // 1000 ms SAFETY WATCHDOG
  //
  // If Brain stops sending commands, STOP motors.
  // ==========================================================

  if (now - last_cmd_time > WATCHDOG_TIMEOUT_MS) {

    target_left_speed  = 0.0;
    target_right_speed = 0.0;
  }


  // ==========================================================
  // APPLY LEFT MOTOR
  // ==========================================================

  set_bts7960_speed(
    PIN_L_RPWM,
    PIN_L_LPWM,
    PIN_L_REN,
    PIN_L_LEN,
    target_left_speed
  );


  // ==========================================================
  // APPLY RIGHT MOTOR
  // ==========================================================

  set_bts7960_speed(
    PIN_R_RPWM,
    PIN_R_LPWM,
    PIN_R_REN,
    PIN_R_LEN,
    target_right_speed
  );
}