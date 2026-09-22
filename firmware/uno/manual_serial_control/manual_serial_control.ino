// Keyboard-ready serial control for the four-motor RobotCar.
//
// The Mac or Raspberry Pi reads the keyboard and sends one-character commands
// over USB serial. While moving, it must repeat the active command faster than
// kCommandTimeoutMs. If communication stops, the UNO releases every motor.

#include <AFMotor_R4.h>

AF_DCMotor frontLeft(1);
AF_DCMotor rearLeft(2);
AF_DCMotor frontRight(3);
AF_DCMotor rearRight(4);

constexpr uint8_t kDefaultSpeed = 255;  // PWM range: 0..255
constexpr uint8_t kMinimumSpeed = 80;
constexpr uint8_t kSpeedStep = 15;
constexpr unsigned long kCommandTimeoutMs = 300;

enum Motion : uint8_t {
  STOPPED,
  FORWARD_MOTION,
  BACKWARD_MOTION,
  PIVOT_LEFT,
  PIVOT_RIGHT,
  FORWARD_LEFT,
  FORWARD_RIGHT,
  BACKWARD_LEFT,
  BACKWARD_RIGHT
};

uint8_t driveSpeed = kDefaultSpeed;
Motion currentMotion = STOPPED;
unsigned long lastMotionCommandMs = 0;

void setLeftSpeed(uint8_t speed) {
  frontLeft.setSpeed(speed);
  rearLeft.setSpeed(speed);
}

void setRightSpeed(uint8_t speed) {
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

void releaseAll() {
  frontLeft.run(RELEASE);
  rearLeft.run(RELEASE);
  frontRight.run(RELEASE);
  rearRight.run(RELEASE);

  setLeftSpeed(0);
  setRightSpeed(0);
  currentMotion = STOPPED;
}

const __FlashStringHelper *motionName(Motion motion) {
  switch (motion) {
    case FORWARD_MOTION:  return F("forward");
    case BACKWARD_MOTION: return F("backward");
    case PIVOT_LEFT:      return F("pivot-left");
    case PIVOT_RIGHT:     return F("pivot-right");
    case FORWARD_LEFT:    return F("forward-left");
    case FORWARD_RIGHT:   return F("forward-right");
    case BACKWARD_LEFT:   return F("backward-left");
    case BACKWARD_RIGHT:  return F("backward-right");
    default:              return F("stopped");
  }
}

void applyMotion(Motion motion) {
  // Curves run the inside wheels at half the selected speed.
  const uint8_t slowSpeed = driveSpeed / 2;
  uint8_t leftSpeed = driveSpeed;
  uint8_t rightSpeed = driveSpeed;
  uint8_t leftDirection = FORWARD;
  uint8_t rightDirection = FORWARD;

  switch (motion) {
    case FORWARD_MOTION:
      break;

    case BACKWARD_MOTION:
      leftDirection = BACKWARD;
      rightDirection = BACKWARD;
      break;

    case PIVOT_LEFT:
      leftDirection = BACKWARD;
      rightDirection = FORWARD;
      break;

    case PIVOT_RIGHT:
      leftDirection = FORWARD;
      rightDirection = BACKWARD;
      break;

    case FORWARD_LEFT:
      leftSpeed = slowSpeed;
      break;

    case FORWARD_RIGHT:
      rightSpeed = slowSpeed;
      break;

    case BACKWARD_LEFT:
      leftSpeed = slowSpeed;
      leftDirection = BACKWARD;
      rightDirection = BACKWARD;
      break;

    case BACKWARD_RIGHT:
      rightSpeed = slowSpeed;
      leftDirection = BACKWARD;
      rightDirection = BACKWARD;
      break;

    default:
      releaseAll();
      return;
  }

  setLeftSpeed(leftSpeed);
  setRightSpeed(rightSpeed);
  runLeft(leftDirection);
  runRight(rightDirection);
  currentMotion = motion;
  lastMotionCommandMs = millis();
}

void commandMotion(Motion requestedMotion) {
  const bool changed = requestedMotion != currentMotion;
  applyMotion(requestedMotion);

  // Repeated commands act as a quiet heartbeat, avoiding serial congestion.
  if (changed) {
    Serial.print(F("MOVE: "));
    Serial.print(motionName(currentMotion));
    Serial.print(F(" speed="));
    Serial.println(driveSpeed);
  }
}

void stopMotors(const __FlashStringHelper *reason) {
  releaseAll();
  Serial.println(reason);
}

void setDriveSpeed(uint8_t newSpeed) {
  driveSpeed = constrain(newSpeed, kMinimumSpeed, 255);

  // Apply a speed change immediately without changing direction.
  if (currentMotion != STOPPED) {
    applyMotion(currentMotion);
  }

  Serial.print(F("SPEED: "));
  Serial.println(driveSpeed);
}

void changeDriveSpeed(int16_t amount) {
  int16_t newSpeed = static_cast<int16_t>(driveSpeed) + amount;
  newSpeed = constrain(newSpeed, kMinimumSpeed, 255);
  setDriveSpeed(static_cast<uint8_t>(newSpeed));
}

void setSpeedLevel(char command) {
  // Keys 1..9 map evenly from kMinimumSpeed to full power. Key 0 stops.
  if (command == '0') {
    stopMotors(F("STOP"));
    return;
  }

  const uint8_t level = command - '1';
  const uint8_t speed = kMinimumSpeed +
      (static_cast<uint16_t>(255 - kMinimumSpeed) * level) / 8;
  setDriveSpeed(speed);
}

void printStatus() {
  Serial.print(F("STATUS: motion="));
  Serial.print(motionName(currentMotion));
  Serial.print(F(" speed="));
  Serial.println(driveSpeed);
}

void printHelp() {
  Serial.println(F("CONTROLS"));
  Serial.println(F("  w/f forward    s/b backward"));
  Serial.println(F("  a/l pivot left d/r pivot right"));
  Serial.println(F("  q/e forward curve left/right"));
  Serial.println(F("  z/c backward curve left/right"));
  Serial.println(F("  x or space stop"));
  Serial.println(F("  +/- speed      1..9 speed level"));
  Serial.println(F("  0 stop         ? status         h help"));
  Serial.println(F("Repeat motion commands within 300 ms while driving."));
}

void handleCommand(char command) {
  if (command >= 'A' && command <= 'Z') {
    command += 'a' - 'A';
  }

  switch (command) {
    case 'w':
    case 'f': commandMotion(FORWARD_MOTION); break;
    case 's':
    case 'b': commandMotion(BACKWARD_MOTION); break;
    case 'a':
    case 'l': commandMotion(PIVOT_LEFT); break;
    case 'd':
    case 'r': commandMotion(PIVOT_RIGHT); break;
    case 'q': commandMotion(FORWARD_LEFT); break;
    case 'e': commandMotion(FORWARD_RIGHT); break;
    case 'z': commandMotion(BACKWARD_LEFT); break;
    case 'c': commandMotion(BACKWARD_RIGHT); break;

    case 'x':
    case ' ':
      stopMotors(F("STOP"));
      break;

    case '+':
    case '=':
      changeDriveSpeed(kSpeedStep);
      break;

    case '-':
    case '_':
      changeDriveSpeed(-kSpeedStep);
      break;

    case '0':
    case '1':
    case '2':
    case '3':
    case '4':
    case '5':
    case '6':
    case '7':
    case '8':
    case '9':
      setSpeedLevel(command);
      break;

    case '?': printStatus(); break;
    case 'h': printHelp(); break;
    case '\n':
    case '\r':
    case '\t':
      break;

    default:
      stopMotors(F("ERROR: unknown command; motors released"));
      break;
  }
}

void setup() {
  releaseAll();
  Serial.begin(9600);
  Serial.println(F("ROBOTCAR READY"));
  printHelp();
  printStatus();
}

void loop() {
  while (Serial.available() > 0) {
    handleCommand(Serial.read());
  }

  if (currentMotion != STOPPED &&
      millis() - lastMotionCommandMs >= kCommandTimeoutMs) {
    stopMotors(F("TIMEOUT: motors released"));
  }
}
