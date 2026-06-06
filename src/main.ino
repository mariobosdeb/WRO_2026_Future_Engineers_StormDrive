#include <Servo.h>

Servo s;

const int IN1 = 7;
const int IN2 = 8;
const int ENA = 9;
const int SERVO_PIN = 10;

const int drept  = 90;
const int stanga = 55;
const int viteza = 255;

void setup() {
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(ENA, OUTPUT);

  s.attach(SERVO_PIN);

  // 1. sta drept 5 secunde
  s.write(drept);
  delay(5000);

  // 2. merge inainte drept
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, HIGH);
  analogWrite(ENA, viteza);
  delay(2200);

  // 3. prima oara
  s.write(stanga);
  delay(500);
  analogWrite(ENA, 0);
  s.write(drept);
  delay(800);
  analogWrite(ENA, viteza);
  delay(18000);

  // 4. a doua oara
  s.write(stanga);
  delay(500);
  analogWrite(ENA, 0);
  s.write(drept);
  delay(500);
  analogWrite(ENA, viteza);
  delay(12000);

  // STOP FINAL
  analogWrite(ENA, 0);
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);
  s.write(drept);
}

void loop() {
  // gol — nu se mai repeta
}
