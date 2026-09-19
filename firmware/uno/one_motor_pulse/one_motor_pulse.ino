// Single-port bench test for an L293D/74HC595 motor shield (V1 layout).
// The motor stays released until 'p' is received over USB serial.
// Each command drives the selected port forward briefly, then releases it.

#include <AFMotor_R4.h>

constexpr uint8_t kMotorPort = 4;  // Set to 1, 2, 3, or 4 before upload.
AF_DCMotor motor(kMotorPort);

constexpr uint8_t kTestSpeed = 255;  // PWM range: 0..255
constexpr unsigned long kPulseMs = 150;

void setup() {
  motor.setSpeed(0);
  motor.run(RELEASE);
  Serial.begin(9600);
  Serial.print(F("M"));
  Serial.print(kMotorPort);
  Serial.println(F(" ready. Send p for one short pulse."));
}

void loop() {
  if (Serial.available() == 0) {
    return;
  }

  const char command = Serial.read();
  if (command != 'p') {
    motor.run(RELEASE);
    return;
  }

  motor.setSpeed(kTestSpeed);
  motor.run(FORWARD);
  delay(kPulseMs);
  motor.run(RELEASE);
  motor.setSpeed(0);
  Serial.print(F("Pulse complete; M"));
  Serial.print(kMotorPort);
  Serial.println(F(" released."));
}
