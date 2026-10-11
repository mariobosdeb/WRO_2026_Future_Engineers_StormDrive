"""Parametri WRO Future Engineers 2026 - Adeept PiCar-B Mars Rover.

CONVENTII (peste tot in cod):
  * metri, secunde, grade (doar unde scrie _DEG)
  * cadrul masinii: origine = centrul axei din spate, X inainte, Y la STANGA
  * unghi de directie / yaw pozitiv = STANGA (counter-clockwise)
  * CCW = +1 (peretele interior e la stanga), CW = -1 (interior la dreapta)

Valorile marcate [MASOARA] sunt estimari pentru kitul Adeept; se corecteaza din
calibrate.py (se salveaza in calibration.json, incarcat automat la pornire).
"""
import json
import math
import os

# ---------------------------------------------------------------- misiune
MODE = "open"                    # "open" | "obstacle"  (suprascris din linia de comanda)
ROUND_TIME_LIMIT = 176.0         # runda dureaza 180 s
TOTAL_CORNERS = 12               # 3 ture x 4 colturi
CCW, CW = +1, -1
FORCE_DIRECTION = None           # None = detectat automat; sau CCW / CW (doar pentru teste)
VERBOSE = True
LOOP_HZ = 25.0

# ---------------------------------------------------------------- vehicul [MASOARA]
CAR_LENGTH = 0.25
CAR_WIDTH = 0.18                 # trebuie <= 0.20 (parcare 20 cm)
WHEELBASE = 0.16                 # distanta axa fata - axa spate
REAR_TO_HEAD = 0.15              # axa spate -> axa pan a capului (camera+ultrasonic)
REAR_TO_FRONT = 0.21             # axa spate -> botul masinii
REAR_TO_BACK = 0.04              # axa spate -> spatele masinii
STEER_MAX_DEG = 52.0             # deflexia maxima a servo-ului directie
WHEEL_PER_SERVO = 0.39           # unghi roata / unghi servo (liniaj directie)
STEER_SIGN = +1                  # -1 daca servo-ul vireaza invers
STEER_TRIM_DEG = 0.0             # corectie centru
V_PER_PCT = 0.00952              # m/s la 1% putere (la baterie plina)
BATT_COMP = True                 # scade viteza estimata cu tensiunea bateriei

# ---------------------------------------------------------------- viteze (% putere)
SPEED_STRAIGHT = 36
SPEED_CORNER = 30
SPEED_CAUTIOUS = 27
SPEED_OBSTACLE = 31
SPEED_REVERSE = 28
SPEED_PARK = 24
SPEED_MIN = 18                   # sub aceasta valoare motorul nu porneste

# ---------------------------------------------------------------- cap: camera + ultrasonic (ACELASI pan/tilt!)
PAN_CH, TILT_CH, STEER_CH = 1, 2, 0
PAN_TRIM_DEG = 0.0               # corectie de centru a capului (grade, + = stanga); se seteaza din calibrate.py pasul 4
PAN_SIGN = +1                    # +1: unghi pozitiv = stanga
PAN_PEEK_DEG = 70.0              # privire laterala a ultrasonicului
START_SCAN = False
TILT_SERVO_DEG = -15.0           # deflexia servo-ului tilt in conducere
PAN_SETTLE_BASE = 0.07
PAN_SETTLE_PER_DEG = 0.0016
PEEK_PERIOD = 3.0                # secunde intre doua verificari laterale ultrasonic
PEEK_PERIOD_RESCUE = 0.7         # cand camera nu vede peretii: privire laterala cu ultrasonicul mult mai deasa (pozitie + unghi din sonar)
PEEK_ENABLED = True
PAN_LOOK_DEG = 22.0              # privire spre peretele interior (vede coltul din timp); 0 = dezactivat

# ---------------------------------------------------------------- camera [MASOARA / calibrate.py]
CAM_SIZE = (320, 240)
CAM_HFLIP, CAM_VFLIP = 0, 0
CAM_HFOV_DEG = 53.5            # orizontal (62 deg din fisa Adeept e pe DIAGONALA)
CAM_HEIGHT = 0.15                # inaltimea camerei fata de podea
CAM_PITCH_DEG = 18.0             # inclinare in jos
CAM_FWD_OFFSET = 0.03            # camera fata de axa pan
DARK_FRAC = 0.45                 # perete = pixeli cu V < DARK_FRAC * P90(V)
DARK_V_MIN, DARK_V_MAX = 35, 120
WALL_BINS = 64
WALL_RUN_MIN = 6                 # inaltime minima (pixeli) a peretelui
CAM_ROI_TOP, CAM_ROI_BOTTOM = 0.02, 0.97
BIN_DARK_FRAC = 0.55
LINE_ROI_TOP = 0.16
LINE_MIN_PIXELS = 1000              # liniile colorate conteaza doar de aproape (masurat 10.10: >=1000 px doar cand linia e in fata masinii)
LINE_CLEAR_PIXELS = 140
LINE_FIT_PIXELS = 1000           # minim pixeli ca sa estimam dreapta liniei colorate (intersectie = colt interior)
LINE_EVENT_GAP = 0.45
LINE_WALL_TOL = 4                # liniile colorate se cauta doar sub baza peretelui (minus atatia pixeli)
DIR_DECIDE = 2                   # scor minim pentru directie (culoare = 1/cadru, colt camera = 2, gol ultrasonic = 2)
DIR_COLOR_MIN_FRONT = 0.75       # culoarea conteaza doar cu peretele din fata mai departe de atat (altfel prima linie a trecut)
DIR_SONAR_JUMP = 0.35            # stanga+dreapta mai mare decat la start cu atat => peretele interior s-a terminat
PILLAR_MIN_AREA = 28
MARKER_MIN_AREA = 40

# HSV OpenCV (H 0..179). Camera Picamera2 RGB888 = ordine B,G,R => se foloseste BGR2HSV.
ORANGE = ((6, 110, 90), (24, 255, 255))
BLUE = ((100, 110, 50), (128, 255, 255))
RED = (((0, 130, 105), (5, 255, 255)), ((168, 130, 105), (179, 255, 255)))   # V>=105: peretii inchisi cu dominanta rosiatica (V~50-65 in poza) nu mai sunt "stalpi"
GREEN = ((40, 90, 50), (84, 255, 255))
MAGENTA = ((136, 90, 70), (166, 255, 255))

# ---------------------------------------------------------------- estimare
FIT_X_MAX = 2.2                  # punctele de perete mai departe de atat nu se folosesc la fit
FIT_INLIER = 0.035               # toleranta RANSAC (m)
FIT_MAX_ANGLE_DEG = 38.0         # panta maxima a unui perete lateral
FIT_MIN_POINTS = 4
SIDE_MIN_Y = 0.10
FRONT_AZ_DEG = 9.0               # coloanele centrale pentru peretele din fata
GATE_Y = 0.06                    # salt maxim al pozitiei laterale per cadru camera (m)
GATE_PSI = math.radians(7.0)    # salt maxim al heading-ului per cadru camera
SMOOTH = 0.55                    # filtru exponential pe d_stanga/d_dreapta/psi
OPEN_DY = 0.07                   # cat mai departe lateral => deschidere
CORRIDOR_W_NOMINAL = 0.85        # latime culoar presupusa cand nu se cunoaste
CORRIDOR_W_RANGE = (0.45, 1.25)
SCALE_ALPHA = 0.12               # invatare scala camera din ultrasonic
SONAR_MAX = 2.0
SONAR_FWD = 0.053                # fata ultrasonicului e la atat in fata axei pan (masurat 10.10: 39.3 cm citit la 40 cm de la bot)
SONAR_OVERRIDE = 0.15            # ultrasonicul lateral contrazice camera cu atat => camera e ignorata pe partea aceea
CAM_BAD_HOLD = 4.0               # (s) cat timp; o noua privire laterala de acord o reabiliteaza
CAM_MAX_X = 4.0                  # (TEST URMATOR: 0.85; in sim 0.85 da 6/8 fata de 8/8) punctele de perete din camera mai departe de atat (de la axa spate) nu se folosesc: masurat 10.10,
                                 # camera e precisa (0-4 cm) pana la ~0.80 m, apoi greseste 15-35 cm (inclinarea masinii/covor)
SONAR_AGE_MAX = 3.5

# ---------------------------------------------------------------- control culoar
KY_DEG_PER_M = 105.0             # directie (grade) per metru eroare laterala
KPSI = 1.0                       # directie (grade) per grad eroare de heading
KY_I = 4.0                       # integrator lent (grade per m*s)
PSI_APPROACH_MAX = 32.0          # unghi maxim fata de axa cand corectam o eroare laterala mare
I_CLAMP_M = 0.12
MARGIN_WALL = 0.085              # cat de aproape de perete (de la marginea masinii) acceptam
STEER_SLEW_DPS = 260.0           # viteza maxima de variatie a directiei (grade/s)
HOLD_ESTIMATE_S = 0.6            # cat folosim estimarea veche daca nu mai vedem peretii

# ---------------------------------------------------------------- colturi
TURN_STEER_DEG = 52.0
TURN_RADIUS = None               # None = calculat din WHEELBASE; [MASOARA] raza reala la TURN_STEER_DEG
TURN_MARGIN = 0.03               # incepe virajul cu putin mai devreme
TURN_HANDOFF_YAW = 62.0          # dupa atatea grade rotite predam controlul laterii peretilor
TURN_DONE_YAW = 84.0
TURN_MAX_YAW = 112.0
TURN_MAX_TIME = 5.0
TURN_MIN_FRONT = 0.10            # (cap) sub aceasta distanta frontala -> recuperare
CORNER_LOCKOUT_M = 0.55          # distanta minima intre doua colturi (odometrie)
CORNER_SAME_M = 0.9              # viraj pornit mai devreme de atat dupa cel anterior = acelasi colt (nu se numara)
FRONT_FORCE = 0.32               # (cap) perete foarte aproape -> vireaza oricum
RECOVER_REVERSE_M = 0.22
FRONT_STOP_GAP = 0.08            # daca golul pana la perete/obstacol in fata scade sub atat (m) -> da cu spatele
STATUS_PERIOD_S = 0.5            # la cat timp afiseaza linia de stare in terminal
EXIT_HANDOFF_ANGLE = 40.0        # |psi| maxim acceptat la predare

# ---------------------------------------------------------------- finish Open Challenge
FINISH_STOP_X_OPEN = 0.40        # opreste cand coltul interior al urmatorului colt e la atat (cap)
FINISH_MIN_TRAVEL = 0.28         # minim parcurs dupa viraj inainte sa ne oprim
FINISH_MAX_TRAVEL = 0.95
FINISH_MARGIN = -0.12            # (negativ) opreste putin dupa locul de start, ca sa fie sigur in sectiune
FINISH_TRAVEL = 0.50             # parcurs dupa predarea virajului 12 inainte de oprire

# ---------------------------------------------------------------- Obstacle: stalpi
PILLAR_HALF = 0.025
PASS_CLEAR = 0.065               # distanta libera intre masina si stalp
PILLAR_LOOKAHEAD = 1.6
PILLAR_FORGET_BEHIND = 0.30      # stalpul e "depasit" cand e cu atat in spatele axei spate
PILLAR_REGISTER_Y = 0.55         # stalpi cu |Y| mai mare se ignora (alt culoar)
PILLAR_SPEED = 0.9               # factor viteza cand stalpul e aproape

# ---------------------------------------------------------------- parcare [REGLAJ OBLIGATORIU]
PARKING_ENABLED = True
PARK_LANE_OFFSET = 0.36          # distanta axa masinii -> peretele exterior cand cautam locul
PARK_SEARCH_MAX_M = 2.2
PARK_REV_STEER_DEG = 28.0
PARK_REV_SPEED = 22
PARK_STAGE1_YAW = 38.0
PARK_WALL_STOP = 0.045
PARK_LOT_LEN = 1.5 * CAR_LENGTH  # lungimea libera a locului (regulament: 1.5 x lungimea masinii)

# ---------------------------------------------------------------- hardware (Adeept Robot HAT V3.x)
PCA_ADDRESS = 0x5F
PCA_FREQUENCY = 50
MOTOR_IN1, MOTOR_IN2 = 15, 14    # M1 = singurul motor de tractiune
MOTOR_DIRECTION = 1
ULTRA_TRIGGER, ULTRA_ECHO = 23, 24
SERVO_CENTRE = 90
SERVO_MIN_PULSE, SERVO_MAX_PULSE = 500, 2400
START_BUTTON_PIN = 26
START_BUTTON_PULL_UP = True
ALLOW_KEYBOARD_START = False
STATUS_LED_PINS = (9, 25, 11)
BUZZER_PIN = 18
IR_PINS = (22, 27, 17)           # line tracker (doar diagnoza)
USE_IR_CONFIRM = False
IMU_ENABLED = False              # MPU6050 pe I2C 0x68 (optional, recomandat)
IMU_ADDRESS = 0x68
IMU_SIGN = +1
# farurile RGB (0..1): slabe, ca lumina lor sa nu se reflecte in podea si sa para stalp/linie
LIGHTS_BRIGHTNESS = 0.2

ADEEPT_WEB_DIR = ("/home/robonavodari/Desktop/ADR012-V5.1_PiCar-B_MarsRover_"
                  "SmartCarKit_for_RPi-20260407/Code/adeept_picar-b2/web")
BATTERY_I2C_ADDRESS = 0x48
BATTERY_ADC_CHANNEL = 0
BATTERY_ADC_VREF = 4.93
BATTERY_DIVISION_RATIO = 1000.0 / (3000.0 + 1000.0)
BATTERY_FULL_VOLTAGE = 8.4
BATTERY_WARNING_VOLTAGE = 6.3
BATTERY_MIN_VALID_VOLTAGE = 5.5
BATTERY_SAMPLES = 10
AUTO_STOP_ON_CRITICAL_BATTERY = True

DEBUG_DIR = "debug"
LAST_COLOR_FILE = "last_color.json"
CALIBRATION_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                "calibration.json")


def turn_radius():
    """Raza (m) a axei din spate la viraj maxim."""
    if TURN_RADIUS:
        return TURN_RADIUS
    import math
    wheel = math.radians(TURN_STEER_DEG * WHEEL_PER_SERVO)
    return WHEELBASE / max(1e-3, math.tan(wheel))


def apply(overrides):
    """Suprascrie parametri (dict nume->valoare), ex. din calibration.json."""
    g = globals()
    for key, value in overrides.items():
        if key.startswith("_") or key not in g:
            continue
        if isinstance(value, list):
            value = _tuplify(value)
        g[key] = value


def _tuplify(value):
    return tuple(_tuplify(v) if isinstance(v, list) else v for v in value)


def _calib_paths():
    home = os.path.expanduser("~")
    try:
        import pwd
        sudo_user = os.environ.get("SUDO_USER")
        if sudo_user:
            home = pwd.getpwnam(sudo_user).pw_dir
    except Exception:
        pass
    return [CALIBRATION_FILE, os.path.join(home, ".wro_calibration.json")]


def load_calibration(path=None):
    ok = False
    for p in ([path] if path else _calib_paths()):
        try:
            with open(p, "r", encoding="utf-8") as fh:
                data = json.load(fh)
        except (OSError, ValueError):
            continue
        apply(data)
        ok = True
    return ok


def save_calibration(updates, path=None):
    """Salveaza in calibration.json; daca folderul nu e scriibil (ex. creat cu sudo), foloseste ~/.wro_calibration.json."""
    apply(updates)
    last_err = None
    for p in ([path] if path else _calib_paths()):
        try:
            try:
                with open(p, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
            except (OSError, ValueError):
                data = {}
            data.update(updates)
            with open(p, "w", encoding="utf-8") as fh:
                json.dump(data, fh, indent=2, sort_keys=True)
            print("salvat in", p)
            return p
        except OSError as exc:
            last_err = exc
    print("NU am putut salva calibrarea (%s). Valorile sunt active doar in aceasta sesiune." % last_err)
    return None


KT_R_MIN = 0.55                  # raza reala peste care colturile se fac in mai multe miscari (K-turn)
KT_R_TRIGGER = 0.45              # K-turn: raza folosita pentru momentul inceperii virajului
KT_FRONT_GAP = 0.06              # K-turn: opreste inaintarea la atat de perete
KT_REV_M = 0.28                  # K-turn: cat merge cu spatele
KT_MAX_TIME = 30.0
NORMALIZE_STEER = True           # castigurile regulatorului sunt in grade de roata
NOMINAL_WPS = 0.8                # raportul roata/servo la care au fost acordate castigurile
AUTOCAL_PITCH = True            # corecteaza online inclinarea camerei din paralelismul peretilor
AUTOCAL_RANGE_DEG = 7.0
AUTOCAL_XMAX = 1.6
AUTOCAL_PSI_MAX = 15.0
AUTOCAL_VOTES = 8
AUTOCAL_RATE = 0.6
AUTOCAL_DEADBAND_DEG = 0.4
LEARN_GAIN = True                # invata online unghiul real al rotilor din viraje
LEARN_GAIN_RATE = 0.5
LEARN_GAIN_DELAY = 0.8
LEARN_GAIN_MAX_TURNS = 6
WHEEL_PER_SERVO_MIN = 0.25
WHEEL_PER_SERVO_MAX = 0.60
TURN_VISION_YAW = True           # in viraj: unghiul rotit = estimarea din camera (nu doar odometrie)
OPEN_OUTER = True                # Open: urmareste peretele exterior la OUTER_W/2 (robust la latimea 0.6/1.0)
OUTER_W = 0.60
OUTER_BAND_NEAR = 0.05           # cat de aproape de peretele exterior fata de OUTER_W/2 (m)
OUTER_BAND_FAR = 0.12            # cat de departe de peretele exterior (spre interior) acceptam fara corectie (m)
OPEN_KF = True                   # Open: latime clasificata (0.6/1.0) + filtru Kalman
OPEN_WIDTHS = (0.6, 1.0)
W_VOTE_N = 4
W_VOTE_SPREAD = 0.16
W_VOTE_TOL = 0.18
W_RELEASE_N = 6
EARLY_TURN_M = 0.35              # Obstacle: virajul poate incepe cu pana la atat inaintea punctului geometric (ca sa evite un stalp)
OBS_LOOK_DIST = 1.0              # Obstacle: cu cat inainte de colt privim spre interior
OBS_LOOK_DEG = 20.0
FRONT_FIT_X_MAX = 1.2           # peretele din fata se foloseste pentru psi doar pana la aceasta distanta (cuantizare pixeli)
FRONT_FIT_MAX_GAP = 0.15        # gol maxim (m, pe Y) intre punctele peretelui din fata; mai mare = puncte de pe pereti diferiti

# Invatare online a "trim-ului" directiei (centru servo gresit): integrator persistent pe eroarea de heading
TRIM_LEARN = True
TRIM_KI = 0.6                    # grade steer per (grad heading * s)
TRIM_CLAMP = 5.0

# Autocalibrare pitch cu ultrasonicul (perete din fata vazut de camera vs sonar)
SONARCAL_PITCH = True
SONARCAL_PSI_MAX = 4.0           # grade
SONARCAL_STEER_MAX = 8.0
SONARCAL_XMIN, SONARCAL_XMAX = 0.5, 1.2   # (cadrul masinii)
SONARCAL_VOTES = 4
AUTOCAL_PITCH = False            # varianta pe peretii laterali (putine esantioane) - dezactivata

# Oprire finala dupa distanta frontala (sonar) fata de cea de la start: independenta de erorile de odometrie
FINISH_BY_FRONT = True
FINISH_F0_N = 4
FINISH_F_MARGIN = 0.02           # (m) oprire cand distanta frontala <= f0 - marja (negativ = mai putin)
FINISH_ODO_EXTRA = 0.25          # (m) plasa de siguranta: odometria opreste cu acest plus daca sonarul nu a declansat

# Detectie "blocat": comandat sa mearga, dar fara inaintare => da cu spatele
PF_USE_LINES = False             # liniile colorate in filtrul de particule: geometria din sim nu e verificata pe covorul real
STUCK_TIME_S = 1.6
STUCK_MIN_M = 0.20

# Open: declanseaza virajul dupa distanta pana la peretele din fata (precisa), nu doar dupa colt (estimat din vedere laterala)
TURN_BY_FRONT = True

# Calibrare viteza (odometrie) cu sonarul
SPEEDCAL = True
SPEEDCAL_STEER_MAX = 10.0
SPEEDCAL_FMIN, SPEEDCAL_FMAX = 0.25, 1.9
SPEEDCAL_WINDOW_M = 0.40
SPEEDCAL_MIN_M = 0.22
SPEEDCAL_RATE = 0.7
SPEEDCAL_MIN, SPEEDCAL_MAX = 0.6, 1.5
LEARN_GAIN_MIN_SPEEDCAL = 1
SPEEDCAL_SETTLE_S = 0.7           # dupa o schimbare de comanda de viteza asteptam ca viteza reala sa se stabilizeze
SPEEDCAL_RES_MAX = 0.02           # abatere standard maxima a regresiei (m)

# Obstacle: oprire si privire spre culoarul urmator inainte de viraj
CORNER_LOOK = True
CORNER_LOOK_PAN = 48.0
CORNER_LOOK_FRAMES = 2
CORNER_LOOK_MAX_S = 1.2

# Planificator Obstacle: margini de siguranta (m) fata de pereti / stalpi
PLAN_MARGIN_WALL = 0.04
PLAN_MARGIN_PIL = 0.06
PLAN_TURN_MARGIN_WALL = 0.05
PLAN_TURN_MARGIN_PIL = 0.05
SONARCAL_RATE = 0.9
SONARCAL_CAP = 1.5
SONARCAL_DEADBAND = 0.4

