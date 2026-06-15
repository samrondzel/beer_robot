// TB6612FNG pins

const int STBY_PIN = 14;

const int LEFT_PWM_PIN = 25;
const int LEFT_IN1_PIN = 26;
const int LEFT_IN2_PIN = 27;

const int RIGHT_PWM_PIN = 33;
const int RIGHT_IN1_PIN = 32;
const int RIGHT_IN2_PIN = 13;


// PWM settings

const int PWM_FREQ = 1000;
const int PWM_RESOLUTION = 8;

const int LEFT_PWM_CHANNEL = 0;
const int RIGHT_PWM_CHANNEL = 1;


void setupMotorPins() {
  pinMode(STBY_PIN, OUTPUT);

  pinMode(LEFT_IN1_PIN, OUTPUT);
  pinMode(LEFT_IN2_PIN, OUTPUT);

  pinMode(RIGHT_IN1_PIN, OUTPUT);
  pinMode(RIGHT_IN2_PIN, OUTPUT);

  digitalWrite(STBY_PIN, HIGH);

  ledcAttach(
    LEFT_PWM_PIN,
    PWM_FREQ,
    PWM_RESOLUTION
  );

  ledcAttach(
    RIGHT_PWM_PIN,
    PWM_FREQ,
    PWM_RESOLUTION
  );
}


int speedToPwm(float speed) {
  speed = constrain(speed, -1.0, 1.0);

  int pwm = abs(speed) * 255;

  return pwm;
}


void setMotor(
  float speed,
  int in1Pin,
  int in2Pin,
  int pwmChannel
) {
  speed = constrain(speed, -1.0, 1.0);

  int pwm = speedToPwm(speed);

  if (speed > 0.01) {
    digitalWrite(in1Pin, HIGH);
    digitalWrite(in2Pin, LOW);
  }

  else if (speed < -0.01) {
    digitalWrite(in1Pin, LOW);
    digitalWrite(in2Pin, HIGH);
  }

  else {
    digitalWrite(in1Pin, LOW);
    digitalWrite(in2Pin, LOW);
    pwm = 0;
  }

  ledcWrite(pwmChannel, pwm);
}


void setMotors(float leftSpeed, float rightSpeed) {
  setMotor(
    leftSpeed,
    LEFT_IN1_PIN,
    LEFT_IN2_PIN,
    LEFT_PWM_CHANNEL
  );

  setMotor(
    rightSpeed,
    RIGHT_IN1_PIN,
    RIGHT_IN2_PIN,
    RIGHT_PWM_CHANNEL
  );

  Serial.print("LEFT speed=");
  Serial.print(leftSpeed);
  Serial.print(" pwm=");
  Serial.print(speedToPwm(leftSpeed));

  Serial.print(" | RIGHT speed=");
  Serial.print(rightSpeed);
  Serial.print(" pwm=");
  Serial.println(speedToPwm(rightSpeed));
}


void stopMotors() {
  setMotors(0.0, 0.0);
  Serial.println("Motors stopped");
}


void setup() {
  Serial.begin(115200);
  delay(1000);

  setupMotorPins();

  stopMotors();

  Serial.println("ESP32 TB6612 motor controller ready");
}


void loop() {
  if (!Serial.available()) {
    return;
  }

  String command = Serial.readStringUntil('\n');
  command.trim();

  if (command.length() == 0) {
    return;
  }

  Serial.print("Received: ");
  Serial.println(command);

  if (command.startsWith("MOVE")) {
    float left = 0.0;
    float right = 0.0;

    int parsed = sscanf(
      command.c_str(),
      "MOVE %f %f",
      &left,
      &right
    );

    if (parsed == 2) {
      setMotors(left, right);
    } else {
      Serial.println("Bad MOVE command");
    }
  }

  else if (command == "STOP") {
    stopMotors();
  }

  else {
    Serial.println("Unknown command");
  }
}