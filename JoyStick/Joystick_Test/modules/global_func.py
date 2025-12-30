from datetime import datetime
import yaml
from pathlib import Path

from modules.constants import RobotState
from pkg.utils.blackboard import GlobalBlackboard
from pkg.utils.logging import Logger
import time

bb = GlobalBlackboard()
wait_time = 0.05

def get_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def get_intvar_address(int_var, addr):
    return next((int(item['value']) for item in int_var if item['addr'] == addr), None)

def get_dio_channel(di, ch):
    return next((int(item['state']) for item in di if item['address'] == ch), None)

def get_di(data, address):
    try:
        datav = data[0]['states'][address]
        return datav 
    except: 
        return None

def switch_teleop():
    bb.set("teleop/switch", True)
    while True:
        if bb.get("teleop/switch")== False:
            break
        time.sleep(wait_time)
        Logger.debug(f"{get_time()}: [GLOBAL] Waiting for teleop switching...")
    Logger.debug(f"{get_time()}: [GLOBAL] Teleop switched")

def set_control_gain(control_gain):
    bb.set("control/mode",control_gain)
    bb.set("control/mode_trigger",True)
    while True:
        if bb.get("control/mode_trigger")== False:
            break
        if bb.get("robot/state/op") != RobotState.OP_IDLE:
            Logger.debug(f"{get_time()}: [GLOBAL] Robot is not Idle")
            break
        time.sleep(wait_time)
        Logger.debug(f"{get_time()}: [GLOBAL] Waiting for control_gain change...")
    Logger.debug(f"{get_time()}: [GLOBAL] Control_gain changed")

def enable_SDK(tf):
    bb.set("control/customSDK",tf)
    bb.set("control/customSDK_trigger",True)
    while True:
        if bb.get("control/customSDK_trigger")== False:
            break
        time.sleep(wait_time)
        Logger.debug(f"{get_time()}: [GLOBAL] Waiting for SDK change...")
    Logger.debug(f"{get_time()}: [GLOBAL] SDK changed")

def _initialize_paths(yaml_file: str = "paths.yaml"):
    """
    YAML 파일을 읽어서 프로젝트 경로를 초기화합니다.
    반환값: dict { 'base': Path, 'config': Path, ... }
    """
    base_path = Path(__file__).resolve().parent.parent  # 프로젝트 기준 경로

    yaml_path = base_path / yaml_file
    if not yaml_path.exists():
        raise FileNotFoundError(f"경로 설정 파일이 없습니다: {yaml_path}")

    with open(yaml_path, "r") as f:
        raw_paths = yaml.safe_load(f)

    # 각 경로를 절대 경로로 변환
    paths = {k: (base_path / v).resolve() for k, v in raw_paths.items()}
    paths["base"] = base_path

    return paths
