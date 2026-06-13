#include <Servo.h>
#include <Wire.h>
#include <HUSKYLENS.h>
#include "config.h"

// ── OBIECTE ─────────────────────────────
Servo s;
HUSKYLENS huskylens;

// ── VARIABILE GLOBALE ──────────────────
int modManevra = 0; // 0: Start, 1: Mers, 2: Evitare, 3: Parcare
int colturiTrecute = 0;
bool huskyOK = false;

// ── FUNCȚII MOTOR & SERVO ──────────────
void opresteMotor() { 
  analogWrite(ENA, 0); 
  digitalWrite(IN1, LOW); 
  digitalWrite(IN2, LOW); 
}

void motorInainte(int v) {
  digitalWrite(IN1, LOW); 
  digitalWrite(IN2, HIGH);
  analogWrite(ENA, v);
}

void motorInapoi(int v) {
  digitalWrite(IN1, HIGH); 
  digitalWrite(IN2, LOW);
  analogWrite(ENA, v);
}

// ── SETUP ──────────────────────────────
void setup() {
  Serial.begin(9600);
  Wire.begin();
  
  s.attach(SERVO_PIN);
  s.write(drept);
  
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(ENA, OUTPUT);

  if (huskylens.begin(Wire)) {
    huskyOK = true;
    huskylens.writeAlgorithm(ALGORITHM_COLOR_RECOGNITION);
  }

  delay(2000); // Așteaptă stabilizarea
  motorInainte(impulsPornire);
  delay(timpImpuls);
}

// ── LOOP PRINCIPAL (STATE MACHINE) ─────
void loop() {
  if (!huskyOK) return; // Siguranță dacă senzorul cade

  // Logica de bază a mașinii de stări
  switch (modManevra) {
    case 0: // Mers normal
      motorInainte(vitezaMers);
      if (huskylens.request()) {
        while (huskylens.available()) {
          HUSKYLENSResult res = huskylens.read();
          // Verifică dacă vede obstacol (ID_ROSU sau ID_VERDE)
          if ((res.ID == ID_ROSU || res.ID == ID_VERDE) && (long)res.width * res.height > HUSKY_SCREEN_AREA / 50) {
            modManevra = 1; // Trece la evitare
          }
        }
      }
      break;

    case 1: // Manevră evitare
      // Aici pui logica ta de viraj folosind constantele din config.h
      aplicaVirajRapid(1); // Exemplu: stânga
      motorInainte(vitezaID1_2);
      delay(timpVirajID1_2);
      modManevra = 0; // Revine la mers
      break;

    case 8: // Oprire finală
      opresteMotor();
      while(1); // Blocare infinită la final
      break;
  }
}

// ── FUNCȚII DE SUPORT ──────────────────
void aplicaVirajRapid(int directie) {
  s.write(directie == 1 ? stangaRapid : dreaptaRapid);
}
