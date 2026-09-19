// Four-motor bench test for an L293D/74HC595 motor shield (V1 layout).
// All motors stay released until 'p' is received over USB serial.
// Each command drives M1-M4 forward briefly, then releases all outputs.

#include <AFMotor_R4.h>

AF_DCMotor motor1(1);
AF_DCMotor motor2(2);
AF_DCMotor motor3(3);
AF_DCMotor motor4(4);

constexpr uint8_t kTestSpeed = 255;  // PWM range: 0..255
constexpr unsigned long kPulseMs = 150;

void releaseAll() {
  motor1.run(RELEASE);
  motor2.run(RELEASE);
  motor3.run(RELEASE);
  motor4.run(RELEASE);

  motor1.setSpeed(0);
  motor2.setSpeed(0);
  motor3.setSpeed(0);
  motor4.setSpeed(0);
}

void setup() {
  releaseAll();

  Serial.begin(9600);
  Serial.println(F("M1-M4 ready. Send p for one short forward pulse."));
}

void loop() {
  if (Serial.available() == 0) {
    return;
  }

  const char command = Serial.read();
  if (command != 'p') {
    releaseAll();
    return;
  }

  motor1.setSpeed(kTestSpeed);
  motor2.setSpeed(kTestSpeed);
  motor3.setSpeed(kTestSpeed);
  motor4.setSpeed(kTestSpeed);

  motor1.run(FORWARD);
  motor2.run(FORWARD);
  motor3.run(FORWARD);
  motor4.run(FORWARD);

  delay(kPulseMs);
  releaseAll();

  Serial.println(F("Pulse complete; M1-M4 released."));
}
