#include <Servo.h>
#include <Wire.h>
#include <HUSKYLENS.h>

// ── OBJECTS ─────────────────────────────
Servo s;
HUSKYLENS huskylens;

// ── L298N PINS ──────────────────────────
const int IN1 = 7;
const int IN2 = 8;
const int ENA = 5;

// ── SERVO PIN ───────────────────────────
const int SERVO_PIN = 10;

// ── NORMAL SERVO SETTINGS ───────────────
const int drept   = 90;
const int stanga  = 55;
const int dreapta = 125;

// ── CORNER SERVO SETTINGS FOR ID 3 AND 4 ──
const int stangaColt  = 65;
const int dreaptaColt = 115;

// ── FAST SERVO SETTINGS FOR ID 1 AND 2 ──
const int stangaRapid  = 45;
const int dreaptaRapid = 135;

// ── MOTOR SETTINGS ──────────────────────
const int vitezaMers    = 160;
const int vitezaID1_2   = 120;
const int vitezaColt    = 115; // <-- NEW: Lower speed specifically for turning corners
const int impulsPornire = 180;
const int timpImpuls    = 300;

const int vitezaCautareParcare = 100;
const int vitezaParcare        = 95;

// ── HUSKYLENS IDS ───────────────────────
const int ID_ROSU       = 1;
const int ID_VERDE      = 2;
const int ID_ALBASTRU   = 3;
const int ID_PORTOCALIU = 4;
const int ID_MAGENTA    = 5;

// ── SCREEN AREA SETTINGS ────────────────
const long HUSKY_SCREEN_AREA  = 320L * 240L;
const long SHIFT_TRIGGER_AREA = HUSKY_SCREEN_AREA / 50;
const long PARK_TRIGGER_AREA  = HUSKY_SCREEN_AREA / 50;

// ── TIMING SETTINGS ─────────────────────
const unsigned long intervalCitire = 60;

const unsigned long timpVirajID1_2     = 700;
const unsigned long timpRevenireID1_2  = 150;
const unsigned long timpDreptDupaID1_2 = 900;

const unsigned long timpIgnoraID3_4DupaID1_2 = 1250;
unsigned long ignoraID3_4PanaLa = 0;

const unsigned long timpVirajID3_4  = 1900;
const unsigned long timpIgnoraID3_4 = 2400;

// ── LAP COUNTING ────────────────────────
const int COLTURI_PE_TUR = 4;
const int TURE_DE_FACUT  = 3;
const int TOTAL_COLTURI  = COLTURI_PE_TUR * TURE_DE_FACUT;
int colturiTrecute = 0;

// ── PARKING SETTINGS ────────────────────
const bool PARCARE_ACTIVATA = true;

const unsigned long timpTrecerePeLanga = 800;
const unsigned long timpMarsarier1     = 1100;
const unsigned long timpMarsarier2     = 950;
const unsigned long timpCorectieFata   = 250;
const unsigned long timpMaximCautare   = 8000;

// ── STATE ───────────────────────────────
int modManevra = 0;
int directieBlocata = 0;
int directieColturi = 0;

unsigned long timpStartManevra = 0;
unsigned long timpUltimaCitire = 0;
unsigned long timpStartCautare = 0;

bool huskyOK = false;

// ════════════════════════════════════════
// VISION DATA
// ════════════════════════════════════════
struct VisionData {
  bool vedeRosu = false;
  bool vedeVerde = false;
  bool vedeAlbastru = false;
  bool vedePortocaliu = false;
  bool vedeMagenta = false;

  long areaRosu = 0;
  long areaVerde = 0;
  long areaAlbastru = 0;
  long areaPortocaliu = 0;
  long areaMagenta = 0;

  bool cameraOK = false;
};

// ════════════════════════════════════════
// SERVO
// ════════════════════════════════════════
void servoDrept()        { s.write(drept); }
void servoStanga()       { s.write(stanga); }
void servoDreapta()      { s.write(dreapta); }
void servoStangaRapid()  { s.write(stangaRapid); }
void servoDreaptaRapid() { s.write(dreaptaRapid); }

void aplicaVirajRapid(int directie) {
  if (directie == 1) servoStangaRapid();
  if (directie == 2) servoDreaptaRapid();
}

void aplicaVirajNormal(int directie) {
  if (directie == 1) servoStanga();
  if (directie == 2) servoDreapta();
}

void aplicaVirajColt(int directie) {
  if (directie == 1) s.write(stangaColt);
  if (directie == 2) s.write(dreaptaColt);
}

void aplicaVirajParcare(int directie) {
  if (directie == 1) servoStangaRapid();
  if (directie == 2) servoDreaptaRapid();
}

int directieOpusa(int directie) {
  if (directie == 1) return 2;
  if (directie == 2) return 1;
  return 0;
}

// ════════════════════════════════════════
// MOTOR
// ════════════════════════════════════════
void motorInainte(int viteza) {
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, HIGH);
  analogWrite(ENA, constrain(viteza, 0, 255));
}

void motorInapoi(int viteza) {
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);
  analogWrite(ENA, constrain(viteza, 0, 255));
}

void opresteMotor() {
  analogWrite(ENA, 0);
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);
}

// ════════════════════════════════════════
// HUSKYLENS INIT
// ════════════════════════════════════════
void initHusky() {
  if (huskylens.begin(Wire)) {
    huskyOK = true;
    huskylens.writeAlgorithm(ALGORITHM_COLOR_RECOGNITION);
    Serial.println("HuskyLens connected!");
  } else {
    huskyOK = false;
    Serial.println("HuskyLens not responding. Car goes straight.");
  }
}

// ════════════════════════════════════════
// READ HUSKYLENS
// ════════════════════════════════════════
VisionData citesteHusky() {
  VisionData v;

  if (!huskyOK) {
    if (huskylens.begin(Wire)) {
      huskyOK = true;
      huskylens.writeAlgorithm(ALGORITHM_COLOR_RECOGNITION);
      Serial.println("HuskyLens reconnected!");
    } else {
      return v;
    }
  }

  if (!huskylens.request()) {
    huskyOK = false;
    Serial.println("HuskyLens lost.");
    return v;
  }

  v.cameraOK = true;

  if (!huskylens.isLearned() || !huskylens.available()) {
    return v;
  }

  while (huskylens.available()) {
    HUSKYLENSResult result = huskylens.read();
    if (result.command != COMMAND_RETURN_BLOCK) continue;

    long area = (long)result.width * (long)result.height;

    if (result.ID == ID_ROSU && area > v.areaRosu) {
      v.vedeRosu = true;  v.areaRosu = area;
    }
    if (result.ID == ID_VERDE && area > v.areaVerde) {
      v.vedeVerde = true; v.areaVerde = area;
    }
    if (result.ID == ID_ALBASTRU && area > v.areaAlbastru) {
      v.vedeAlbastru = true; v.areaAlbastru = area;
    }
    if (result.ID == ID_PORTOCALIU && area > v.areaPortocaliu) {
      v.vedePortocaliu = true; v.areaPortocaliu = area;
    }
    if (result.ID == ID_MAGENTA && area > v.areaMagenta) {
      v.vedeMagenta = true; v.areaMagenta = area;
    }
  }

  return v;
}

// ════════════════════════════════════════
// AREA CHECK FOR ID 1 / ID 2
// ════════════════════════════════════════
bool id1_2EsteMare(VisionData v) {
  return max(v.areaRosu, v.areaVerde) >= SHIFT_TRIGGER_AREA;
}

// ════════════════════════════════════════
// START MANEUVERS
// ════════════════════════════════════════
void pornesteID1_2(int directie) {
  modManevra = 1;
  directieBlocata = directie;
  timpStartManevra = millis();
  aplicaVirajRapid(directieBlocata);
}

void pornesteID3_4(int directie) {
  modManevra = 2;
  directieBlocata = directie;
  timpStartManevra = millis();

  if (directieColturi == 0) {
    directieColturi = directie;
  }

  colturiTrecute++;
  Serial.print("Corner ");
  Serial.print(colturiTrecute);
  Serial.print(" / ");
  Serial.println(TOTAL_COLTURI);

  aplicaVirajColt(directieBlocata);
}

// ════════════════════════════════════════
// SETUP
// ════════════════════════════════════════
void setup() {
  // straighten wheels IMMEDIATELY on power-up
  s.attach(SERVO_PIN);
  s.write(drept);
  delay(300);

  Serial.begin(9600);
  Wire.begin();

  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(ENA, OUTPUT);
  opresteMotor();

  initHusky();

  Serial.println("START! Robot is going.");
  motorInainte(impulsPornire);
  delay(timpImpuls);
}

// ════════════════════════════════════════
// LOOP
// ════════════════════════════════════════
void loop() {

  if (modManevra == 8) {
    opresteMotor();
    return;
  }

  if (modManevra == 5) {
    int spreZid = directieOpusa(directieColturi);
    aplicaVirajParcare(spreZid);
    motorInapoi(vitezaParcare);
    if (millis() - timpStartManevra >= timpMarsarier1) {
      modManevra = 6;
      timpStartManevra = millis();
      Serial.println("Parking phase 2.");
    }
    return;
  }

  if (modManevra == 6) {
    aplicaVirajParcare(directieColturi);
    motorInapoi(vitezaParcare);
    if (millis() - timpStartManevra >= timpMarsarier2) {
      modManevra = 7;
      timpStartManevra = millis();
      servoDrept();
      Serial.println("Parking phase 3.");
    }
    return;
  }

  if (modManevra == 7) {
    servoDrept();
    motorInainte(vitezaParcare);
    if (millis() - timpStartManevra >= timpCorectieFata) {
      opresteMotor();
      servoDrept();
      modManevra = 8;
      Serial.println("PARKED. Round complete!");
    }
    return;
  }

  if (modManevra == 4) {
    servoDrept();
    motorInainte(vitezaCautareParcare);
    if (millis() - timpStartManevra >= timpTrecerePeLanga) {
      opresteMotor();
      delay(150);
      modManevra = 5;
      timpStartManevra = millis();
      Serial.println("Parking phase 1.");
    }
    return;
  }

  if (modManevra == 1) {
    motorInainte(vitezaID1_2);
  } else if (modManevra == 3) {
    motorInainte(vitezaCautareParcare);
  } else {
    motorInainte(vitezaMers);
  }

  if (millis() - timpUltimaCitire < intervalCitire) {
    return;
  }
  timpUltimaCitire = millis();

  if (modManevra == 3) {
    if (millis() - timpStartCautare >= timpMaximCautare) {
      opresteMotor();
      modManevra = 8;
      Serial.println("Magenta not found - stopped in section.");
      return;
    }

    VisionData v = citesteHusky();
    if (!v.cameraOK) { servoDrept(); return; }

    if (v.vedeMagenta && v.areaMagenta >= PARK_TRIGGER_AREA) {
      Serial.println("MAGENTA spotted.");
      modManevra = 4;
      timpStartManevra = millis();
      return;
    }

    servoDrept();
    return;
  }

  if (modManevra == 1) {
    unsigned long t = millis() - timpStartManevra;

    if (t < timpVirajID1_2) {
      aplicaVirajRapid(directieBlocata);
      return;
    }
    if (t < timpVirajID1_2 + timpRevenireID1_2) {
      aplicaVirajRapid(directieOpusa(directieBlocata));
      return;
    }
    if (t < timpVirajID1_2 + timpRevenireID1_2 + timpDreptDupaID1_2) {
      servoDrept();
      return;
    }

    servoDrept();
    modManevra = 0;
    directieBlocata = 0;
    ignoraID3_4PanaLa = millis() + timpIgnoraID3_4DupaID1_2;
    return;
  }

  if (modManevra == 2) {
    VisionData v = citesteHusky();

    if ((v.vedeRosu || v.vedeVerde) && id1_2EsteMare(v)) {
      if (v.areaRosu >= v.areaVerde) {
        pornesteID1_2(2);
      } else {
        pornesteID1_2(1);
      }
      return;
    }

    unsigned long t = millis() - timpStartManevra;

    if (t < timpVirajID3_4) {
      aplicaVirajColt(directieBlocata);
      return;
    }

    servoDrept();

    if (t >= timpIgnoraID3_4) {
      modManevra = 0;
      directieBlocata = 0;

      if (colturiTrecute >= TOTAL_COLTURI) {
        if (PARCARE_ACTIVATA) {
          modManevra = 3;
          timpStartCautare = millis();
          Serial.println("3 laps done -> searching for parking.");
        } else {
          opresteMotor();
          modManevra = 8;
          Serial.println("3 laps done -> stopped.");
        }
      }
    }
    return;
  }

  VisionData v = citesteHusky();

  if (!v.cameraOK) {
    servoDrept();
    return;
  }

  bool existaID1_2 = v.vedeRosu || v.vedeVerde;
  bool existaID3_4 = v.vedeAlbastru || v.vedePortocaliu;

  if (existaID1_2 && id1_2EsteMare(v)) {
    if (v.areaRosu >= v.areaVerde) {
      pornesteID1_2(2);
    } else {
      pornesteID1_2(1);
    }
    return;
  }

  if (existaID3_4 && millis() >= ignoraID3_4PanaLa) {
    if (v.areaPortocaliu >= v.areaAlbastru) {
      pornesteID3_4(2);
    } else {
      pornesteID3_4(1);
    }
    return;
  }

  servoDrept();
}
