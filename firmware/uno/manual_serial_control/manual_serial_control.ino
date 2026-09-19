// Initial manual control for the four-motor rover.
// Commands over USB serial: f=forward, b=backward, l=left, r=right, s=stop.
// Motion stops automatically unless another motion command arrives in time.

#include <AFMotor_R4.h>

AF_DCMotor frontLeft(1);
AF_DCMotor rearLeft(2);
AF_DCMotor frontRight(3);
AF_DCMotor rearRight(4);

constexpr uint8_t kDriveSpeed = 255;  // PWM range: 0..255
constexpr unsigned long kCommandTimeoutMs = 300;

bool moving = false;
unsigned long lastMotionCommandMs = 0;

void releaseAll() {
  frontLeft.run(RELEASE);
  rearLeft.run(RELEASE);
  frontRight.run(RELEASE);
  rearRight.run(RELEASE);

  frontLeft.setSpeed(0);
  rearLeft.setSpeed(0);
  frontRight.setSpeed(0);
  rearRight.setSpeed(0);

  moving = false;
}

void setAllSpeeds(uint8_t speed) {
  frontLeft.setSpeed(speed);
  rearLeft.setSpeed(speed);
  frontRight.setSpeed(speed);
  rearRight.setSpeed(speed);
}

void runLeft(uint8_t direction) {
  frontLeft.run(direction);
  rearLeft.run(direction);
}

void runRight(uint8_t direction) {
  frontRight.run(direction);
  rearRight.run(direction);
}

void startMotion(char command) {
  setAllSpeeds(kDriveSpeed);

  switch (command) {
    case 'f':
      runLeft(FORWARD);
      runRight(FORWARD);
      break;
    case 'b':
      runLeft(BACKWARD);
      runRight(BACKWARD);
      break;
    case 'l':
      runLeft(BACKWARD);
      runRight(FORWARD);
      break;
    case 'r':
      runLeft(FORWARD);
      runRight(BACKWARD);
      break;
    default:
      releaseAll();
      return;
  }

  moving = true;
  lastMotionCommandMs = millis();
}

void setup() {
  releaseAll();

  Serial.begin(9600);
  Serial.println(F("READY: f=forward b=backward l=left r=right s=stop"));
  Serial.println(F("Motion timeout: 300 ms"));
}

void loop() {
  if (Serial.available() > 0) {
    char command = Serial.read();

    if (command >= 'A' && command <= 'Z') {
      command += 'a' - 'A';
    }

    if (command == 's') {
      releaseAll();
      Serial.println(F("STOP"));
    } else if (command == 'f' || command == 'b' ||
               command == 'l' || command == 'r') {
      startMotion(command);
      Serial.print(F("MOVE "));
      Serial.println(command);
    } else if (command != '\n' && command != '\r' && command != ' ') {
      releaseAll();
      Serial.println(F("ERROR: motors released"));
    }
  }

  if (moving && millis() - lastMotionCommandMs >= kCommandTimeoutMs) {
    releaseAll();
    Serial.println(F("TIMEOUT: motors released"));
  }
}
