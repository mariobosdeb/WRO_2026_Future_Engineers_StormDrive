#include "config.h"
#include <Servo.h>

Servo s;
bool hasRun = false; // Garantează că traseul se execută o singură dată

void setup() {
  // Inițializare pini motor conform codului tău
  pinMode(IN1_PIN, OUTPUT);
  pinMode(IN2_PIN, OUTPUT);
  pinMode(ENA_PIN, OUTPUT);

  // Inițializare buton pornire (WRO)
  pinMode(START_BUTTON_PIN, INPUT_PULLUP);

  s.attach(SERVO_PIN);
  s.write(DREPT); // Robotul pornește cu roțile drepte
}

void loop() {
  // Robotul așteaptă apăsarea butonului de pe pinul 2 ca să înceapă cursa
  if (!hasRun && digitalRead(START_BUTTON_PIN) == LOW) {
    delay(500); // Mică pauză anti-bouncing
    runRaceSequence();
    hasRun = true; // Blochează repetarea codului
  }
}

// Logica ta exactă de mișcare, activată la buton
void runRaceSequence() {
  // 1. Sta drept 5 secunde
  s.write(DREPT);
  delay(5000);

  // 2. Merge inainte drept
  digitalWrite(IN1_PIN, LOW);
  digitalWrite(IN2_PIN, HIGH);
  analogWrite(ENA_PIN, VITEZA);
  delay(2200);

  // 3. Prima oara (Viraj stânga)
  s.write(STANGA);
  delay(500);
  analogWrite(ENA_PIN, 0);
  s.write(DREPT);
  delay(800);
  analogWrite(ENA_PIN, VITEZA);
  delay(18000);

  // 4. A doua oara (Viraj stânga)
  s.write(STANGA);
  delay(500);
  analogWrite(ENA_PIN, 0);
  s.write(DREPT);
  delay(500);
  analogWrite(ENA_PIN, VITEZA);
  delay(12000);

  // STOP FINAL (Frână totală)
  analogWrite(ENA_PIN, 0);
  digitalWrite(IN1_PIN, LOW);
  digitalWrite(IN2_PIN, LOW);
  s.write(DREPT);
}
