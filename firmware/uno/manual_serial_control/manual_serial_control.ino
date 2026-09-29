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

constexpr uint8_t kDefaultSpeed = 195;  // PWM range: 0..255
constexpr uint8_t kMinimumSpeed = 195;
constexpr uint8_t kSpeedStep = 5;
constexpr uint8_t kDefaultCurveStrength = 75;
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
uint8_t curveStrength = kDefaultCurveStrength;
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
  // Curve strength reduces inside-wheel PWM; it is not a measured radius.
  // The 195 minimum applies to the base/outer PWM, not the reduced inside side.
  const uint8_t slowSpeed =
      static_cast<uint16_t>(driveSpeed) * (100 - curveStrength) / 100;
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
  runLeft(leftSpeed == 0 ? RELEASE : leftDirection);
  runRight(rightSpeed == 0 ? RELEASE : rightDirection);
  currentMotion = motion;
}

void commandMotion(Motion requestedMotion) {
  const bool changed = requestedMotion != currentMotion;
  applyMotion(requestedMotion);
  lastMotionCommandMs = millis();

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

void printConfiguration() {
  Serial.print(F("CONFIG: protocol=2 speed="));
  Serial.print(driveSpeed);
  Serial.print(F(" curve="));
  Serial.print(curveStrength);
  Serial.println(F(" min=195 max=255"));
}

void setCurveStrength(uint8_t strength) {
  curveStrength = constrain(strength, 0, 100);
  if (currentMotion != STOPPED) applyMotion(currentMotion);
  printConfiguration();
}

void setDriveSpeed(uint8_t newSpeed) {
  driveSpeed = constrain(newSpeed, kMinimumSpeed, 255);

  // Apply a speed change immediately without changing direction.
  if (currentMotion != STOPPED) {
    applyMotion(currentMotion);
  }

  Serial.print(F("SPEED: "));
  Serial.println(driveSpeed);
  printConfiguration();
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
  printConfiguration();
}

void printHelp() {
  Serial.println(F("CONTROLS"));
  Serial.println(F("  w/f forward    s/b backward"));
  Serial.println(F("  a/l pivot left d/r pivot right"));
  Serial.println(F("  q/e forward curve left/right"));
  Serial.println(F("  z/c backward curve left/right"));
  Serial.println(F("  x or space stop"));
  Serial.println(F("  +/- PWM by 5   1..9 PWM 195..255"));
  Serial.println(F("  @c0..100 followed by newline: curve strength"));
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

// Framed settings never pass their digits through as movement/speed commands.
char settingBuffer[5];
uint8_t settingLength = 0;
bool readingSetting = false;
bool discardSetting = false;
unsigned long settingStartedMs = 0;

void expireMotion() {
  if (currentMotion != STOPPED &&
      millis() - lastMotionCommandMs >= kCommandTimeoutMs) {
    stopMotors(F("TIMEOUT: motors released"));
  }
}

void handleSerialChar(char value) {
  // Stop must remain available even during a partial or malformed setting.
  if (value == 'x' || value == 'X' || value == ' ') {
    readingSetting = false;
    discardSetting = false;
    handleCommand(value);
    return;
  }
  if (value == '@') {
    readingSetting = true;
    discardSetting = false;
    settingLength = 0;
    settingStartedMs = millis();
    return;
  }
  if (discardSetting) {
    if (value == '\n') discardSetting = false;
    return;
  }
  if (!readingSetting) {
    handleCommand(value);
    return;
  }
  if (value == '\r') return;
  if (value == '\n') {
    readingSetting = false;
    bool valid = settingLength >= 2 && settingBuffer[0] == 'c';
    uint16_t strength = 0;
    for (uint8_t i = 1; i < settingLength; ++i) {
      if (settingBuffer[i] < '0' || settingBuffer[i] > '9') valid = false;
      else strength = strength * 10 + (settingBuffer[i] - '0');
    }
    if (valid && strength <= 100) setCurveStrength(strength);
    else stopMotors(F("ERROR: invalid curve setting"));
    return;
  }
  if (settingLength >= sizeof(settingBuffer) - 1) {
    readingSetting = false;
    discardSetting = true;
    stopMotors(F("ERROR: setting too long"));
    return;
  }
  settingBuffer[settingLength++] = value;
}

void loop() {
  expireMotion();
  if (readingSetting && millis() - settingStartedMs >= 100) {
    readingSetting = false;
    discardSetting = true;
    stopMotors(F("ERROR: incomplete setting"));
  }
  while (Serial.available() > 0) {
    expireMotion();
    handleSerialChar(Serial.read());
  }
}
