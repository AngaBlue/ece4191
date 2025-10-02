import os

# General
WINDOW_SCALE = 2.0    # scale camera view in window (1.0 = 640x480)
DRAW_FPS = 60         # target UI refresh rate (Hz)
SCREENSHOT_DIR = "screenshots"

# Commands
PORT = 65001

# Camera
W, H = 640, 480

# Joysticks
DEADZONE = 0.05             # joystick deadzone (0.0–0.2 typical)
EXPO = 0.8                  # response shaping (0=linear, 1=very soft center)
K_TURN_SPEED = 1.0          # reduce turning at speed (0=none, 1=full)
QUICKTURN_THRESH = 0.10     # allow full spin when |forward| < threshold
LEFT_GAIN = 1.0             # scaling for left track (0.0–1.0)
RIGHT_GAIN = 1.0            # scaling for right track (0.0–1.0)
MIN_DUTY = 0.55             # minimum duty cycle to overcome stiction
TURN_AXIS_INVERT = -1.0     # set to -1.0 if your X axis is reversed, else 1.0

# Control
SAMPLE_RATE = 0.01

BRIGHTNESS_STEP = 1
BRIGHTNESS_MIN = 0
BRIGHTNESS_MAX = 6

PAN_MIN = 0
PAN_MAX = 270
PAN_HOME = 135
TILT_MIN = 80
TILT_HOME = 135
TILT_MAX = 180
SERVO_RATE = 200 * SAMPLE_RATE  # deg per tick

# YOLO
YOLO_MODEL = os.environ.get("YOLO_MODEL", "model.pt")
YOLO_CONF = float(os.environ.get("YOLO_CONF", "0.25"))
YOLO_IOU = float(os.environ.get("YOLO_IOU",  "0.45"))
CLASS_NAMES = ["kangaroo", "cockatoo", "tasmanian_devil",
               "frog", "platypus", "crocodile", "koala"]
