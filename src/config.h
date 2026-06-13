#ifndef CONFIG_H
#define CONFIG_H

// ── L298N PINS ──────────────────────────
const int IN1 = 7;
const int IN2 = 8;
const int ENA = 5;

// ── SERVO PIN ───────────────────────────
const int SERVO_PIN = 10;

// ── SERVO SETTINGS ──────────────────────
const int drept       = 90;
const int stanga      = 55;
const int dreapta     = 125;
const int stangaColt  = 65;
const int dreaptaColt = 115;
const int stangaRapid = 45;
const int dreaptaRapid = 135;

// ── MOTOR SPEEDS ────────────────────────
const int vitezaMers         = 160;
const int vitezaID1_2        = 120;
const int vitezaColt         = 115;
const int impulsPornire      = 180;
const int timpImpuls         = 300;
const int vitezaCautareParcare = 100;
const int vitezaParcare      = 95;

// ── HUSKYLENS IDS ───────────────────────
const int ID_ROSU         = 1;
const int ID_VERDE        = 2;
const int ID_ALBASTRU     = 3;
const int ID_PORTOCALIU   = 4;
const int ID_MAGENTA      = 5;

// ── THRESHOLDS ──────────────────────────
const long HUSKY_SCREEN_AREA  = 320L * 240L;
const long SHIFT_TRIGGER_AREA = HUSKY_SCREEN_AREA / 50;
const long PARK_TRIGGER_AREA  = HUSKY_SCREEN_AREA / 50;

// ── TIMING SETTINGS ─────────────────────
const unsigned long intervalCitire = 60;
const unsigned long timpVirajID1_2      = 700;
const unsigned long timpRevenireID1_2   = 150;
const unsigned long timpDreptDupaID1_2 = 900;
const unsigned long timpIgnoraID3_4DupaID1_2 = 1250;
const unsigned long timpVirajID3_4      = 1900;
const unsigned long timpIgnoraID3_4     = 2400;

// ── PARKING TIMINGS ─────────────────────
const unsigned long timpTrecerePeLanga = 800;
const unsigned long timpMarsarier1     = 1100;
const unsigned long timpMarsarier2     = 950;
const unsigned long timpCorectieFata   = 250;
const unsigned long timpMaximCautare   = 8000;

// ── LAP COUNTING ────────────────────────
const int COLTURI_PE_TUR = 4;
const int TURE_DE_FACUT  = 3;
const int TOTAL_COLTURI  = COLTURI_PE_TUR * TURE_DE_FACUT;

#endif
