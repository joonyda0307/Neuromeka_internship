from enum import IntEnum

from modules.global_func import _initialize_paths

# Voice 사용 여부를 제어하는 옵션
Use_Voice = True
# Joystick 사용 여부를 제어하는 옵션
Use_Joystick = False

PATHS = _initialize_paths()
BASE_PATH = PATHS["base"]
# CONFIG_PATH = PATHS.get("config")
MODULE_PATH = PATHS.get("module")

class JoystickCommand:
    DISCONNECT = -1
    NONE = 0
    ROTATE_CCW = 1
    ROTATE_CW = 2
    ENABLE = 3
    DEACT_SDK = 4
    ACT_SDK = 5
    TILT_U = 6
    TILT_V = 7
    TILT_W = 8

    TILT_NONE = 9
    TILT_LEFT = 10
    TILT_RIGHT = 11
    TILT_UP = 12
    TILT_DOWN = 13

    CUSTOM_MODE = 14
    FREE_MOTION_MODE = 15
    FIXED_POINT_MODE = 16
    FIXED_LINE_MODE = 17
    UPDATE_JTS = 18

    MODE_CHANGE = 19
    ZOOM_IN = 20    
    ZOOM_OUT = 21

    TILT_W_CW = 22
    TILT_W_CCW = 23

    UPDATE_GAIN = 24

    VOICE_ON = 25

class ControlMode(IntEnum):
    NONE = -1
    FIXED_JOINT = 3
    FREE_MOTION = 0
    FIXED_POINT = 1
    FIXED_LINE  = 2
    UPDATE_JTS  = 4
    RCM_MODE = 5
    EMERGENCY_MODE = 6
    RECOVER_MODE = 7 
    
class ControlMotion(IntEnum):
    NONE = 0
    ROTATE_CCW = 1
    ROTATE_CW = 2
    ZOOM_OUT = 4
    ZOOM_IN = 5
    TILT_LEFT = 9
    TILT_RIGHT = 10
    TILT_UP = 11
    TILT_DOWN = 12

class RobotState(IntEnum):
    OP_SYSTEM_OFF = 0
    OP_SYSTEM_ON = 1
    OP_VIOLATE = 2
    OP_RECOVER_HARD = 3
    OP_RECOVER_SOFT = 4
    OP_IDLE = 5
    OP_MOVING = 6
    OP_TEACHING = 7
    OP_COLLISION = 8
    OP_STOP_AND_OFF = 9
    OP_COMPLIANCE = 10
    OP_BRAKE_CONTROL = 11
    OP_SYSTEM_RESET = 12
    OP_SYSTEM_SWITCH = 13
    OP_VIOLATE_HARD = 15
    OP_MANUAL_RECOVER = 16
    TELE_OP = 17


