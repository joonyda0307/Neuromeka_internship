from enum import Enum, auto
import time
from pcan_handler import PCANHandler, ServoStatus, ControlMode
import keyboard 

# 1. 상태 정의
class HandState(Enum):
    IDLE = auto()       # 사용자 입력(번호 선택) 대기
    READY = auto()      # 동작 전 준비 자세로 이동 중 (Pre-grasp 등)
    MOVING = auto()     # 실제 목표 제스처 수행 중 (Grasp 등)
    COMPLETED = auto()  # 제스처 완료 및 해당 자세 유지 (외력 저항)
    RETURNING = auto()  # 준비 상태(Ready)로 복귀
    INITIAL = auto()    # 동작 완료 후 이니셜 자세로 복귀
    EMERGENCY = auto()  # 비상 정지

# prameter setting
alpha           = 0.05 # alpha: 0.0 ~ 1.0 (1.0에 가까울수록 반응이 빠르고, 0에 가까울수록 부드러움)
threshold       = 50.0 # Convergence threshold
Sampling_freq   = 50

GESTURES = {
    # 1. 원통형 물체 옆으로 잡기
    'Side Grasp': {
        'ready': {
            2: [3758, -3723, 191, 1016],  3: [-192, 390, 527, 1200],
            4: [-19, 675, 472, 749],     5: [509, 748, 498, 268]
        },
        'set': {
            2: [3672, -3745, 1155, 2402], 3: [142, 1471, 2624, 1298],
            4: [133, 2385, 1541, 2263],  5: [214, 2235, 2106, 1523]
        }
    },

    # 2. 넓은 원통 물체 위에서 아래로 잡기
    'Top Grasp': {
        'ready': {
            2: [3563, -2599, -1004, 811], 3: [-186, 1218, 174, 1074],
            4: [76, 1008, 212, 1367],     5: [1824, 1313, 614, -348]
        },
        'set': {
            2: [2405, -2683, 794, 2079],  3: [-156, 1232, 2101, 1191],
            4: [81, 1288, 1601, 2054],    5: [1903, 3039, 1841, 893]
        }
    },

    # 3. 2점 핀치 (준비자세는 Paper로 대체 가능하도록 0 설정)
    'Pinch_2pt': {
        'ready': {
            2: [0, 0, 0, 0], 3: [0, 0, 0, 0], 4: [0, 0, 0, 0], 5: [0, 0, 0, 0]
        },
        'set': {
            2: [2828, -3215, 1986, 1687], 3: [-92, 1925, 2768, 1286],
            4: [82, -110, 765, 1843],     5: [78, -175, 1416, 816]
        }
    },

    # 4. 3점 핀치
    'Pinch_3pt': {
        'ready': {
            2: [0, 0, 0, 0], 3: [0, 0, 0, 0], 4: [0, 0, 0, 0], 5: [0, 0, 0, 0]
        },
        'set': {
            2: [3532, -3110, 890, 3608],  3: [-594, 1971, 3615, 1200],
            4: [900, 2162, 2650, 2028],   5: [1160, -678, 1229, 732]
        }
    },

    # 5. 카드 잡기
    'Card Grasp': {
        'ready': {
            2: [1998, -3882, 2696, 1579], 3: [882, 1197, 4129, 983],
            4: [601, 3643, 4176, 2328],   5: [150, 4121, 4438, 633]
        },
        'set': {
            2: [2501, -3774, 2720, 2235], 3: [867, 1335, 4699, 1094],
            4: [600, 3680, 4190, 2352],   5: [149, 4148, 4500, 726]
        }
    },

    # 10. Push 동작
    'Push': {
        'ready': { # push_start
            2: [2036, -157, 4766, 2894],  3: [213, -1143, 2518, 1951],
            4: [512, 3133, 4080, 2601],   5: [99, 2894, 3939, 2913]
        },
        'set': { # push_end
            2: [2242, -191, 4766, 2898],  3: [382, 108, 545, 25],
            4: [515, 3130, 4077, 2601],   5: [101, 2906, 3940, 2913]
        }
    },

    # 11. Hook 동작
    'Hook': {
        'ready': { # hook_start
            2: [1569, -281, 4778, 2896],  3: [267, -676, 736, 925],
            4: [530, 3131, 4078, 2601],   5: [101, 2893, 3940, 2916]
        },
        'set': { # hook_end
            2: [1574, -294, 4779, 2897],  3: [430, -532, 4639, 1733],
            4: [535, 3132, 4079, 2601],   5: [102, 2896, 3941, 2915]
        }
    },

    # 12. INITIAL 동작
    'Initial': {
        'set': { # hook_end
            2: [0, 0, 0, 0], 3: [0, 0, 0, 0], 4: [0, 0, 0, 0], 5: [0, 0, 0, 0]
        }
    }
}

current_state = HandState.IDLE
INITIAL_POS = GESTURES['Initial']['set']
filtered_positions = {id: [0.0, 0.0, 0.0, 0.0] for id in range(2, 6)}
gesture_map = list(GESTURES.keys())

# for Emergency stop
def emergency_reset(pcan, target_positions, filtered_positions):
    print("\n!!! EMERGENCY STOP ACTIVATED !!!")
    for can_id in range(2, 6):
        current_pos_int = [int(p) for p in filtered_positions[can_id]]
        target_positions[can_id] = current_pos_int
        try:
            pcan.set_target_values(can_id, current_pos_int)
        except Exception as e:
            print(f"Error setting target values for ID {can_id}: {e}")
    
    pcan.set_hand_status(ServoStatus.OFF, ControlMode.POSITION)
    print("Torque disabled. Please restart the program to re-enable.")
    return True

# for Select Menu
def show_menu():
    print("\n" + "="*30)
    print(f"{' [ Gesture Menu ] ':-^30}") # 가운데 정렬 스타일
    for i, name in enumerate(gesture_map, 1):
        print(f"{i:2d}: {name}")
    print(f" {'0: Exit (Program End)':<28}")
    print("="*30)

    result = input("Select Gesture: ").strip()
    return result

# for smooth moving
def Set_position_LPF(filtered_positions, target_positions) : 
    max_error = 0
    for can_id in range(2, 6):
        for i in range(4):
            filtered_positions[can_id][i] = (alpha * target_positions[can_id][i]) + \
                                            ((1 - alpha) * filtered_positions[can_id][i])
            max_error += abs(target_positions[can_id][i] - filtered_positions[can_id][i])\
            
    return max_error

# Pcan initializing
def Pcan_init(ServoStatus, Control_Mode):
    pcan = PCANHandler()
    if not pcan.is_connected():
        print("Failed to connect to PCAN")
        return False
    
    pcan.set_hand_status(ServoStatus, Control_Mode), time.sleep(0.5)
    # clear Receive buf
    while pcan.receive_frame(timeout=.01): pass
    return pcan


def time_idling(t_start):
    time_remain = (time.perf_counter() - t_start)
    if time_remain > 1/Sampling_freq:
        return
    else:
        dt = 1/Sampling_freq - time_remain
        time.sleep(max(0, dt))

def test_Hand_State_Machine():
    global current_state # 전역 변수 사용 시
    pcan = Pcan_init(ServoStatus.ON, ControlMode.POSITION)
    if not pcan: return
    
    print(f"{INITIAL_POS}")

    # 초기 target_positions 설정 (Initial의 set 데이터)
    target_positions = GESTURES['Initial']['set'] 
    motion_selected = None
    max_error = 0 # 초기화
    
    while True:
        t_start = time.perf_counter()

        # 1. IDLE (Menu)
        if current_state == HandState.IDLE:
            choice = show_menu()
            
            if choice == '0': break
            
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(gesture_map):
                    motion_selected = gesture_map[idx]
                    
                    # 'ready'가 있는지 확인하고 없으면 바로 'set'으로
                    if 'ready' in GESTURES[motion_selected]:
                        target_positions = GESTURES[motion_selected]['ready']
                        current_state = HandState.READY
                        print(f"State: READY - Moving to pre-pose...")
                    else:
                        target_positions = GESTURES[motion_selected]['set']
                        current_state = HandState.MOVING
                        print(f"State: MOVING - No ready pose, direct start...")

        # 2. READY -> MOVING
        elif current_state == HandState.READY and max_error < threshold:
            print(f"\r[READY] Pre-pose reached. Press 'Enter' to start {motion_selected}...", end="")

            if keyboard.is_pressed('enter'):
                target_positions = GESTURES[motion_selected]['set']
                current_state = HandState.MOVING
                print(f"\nState: MOVING - Executing {motion_selected}...")

        # 3. MOVING -> COMPLETED
        elif current_state == HandState.MOVING and max_error < threshold:
            current_state = HandState.COMPLETED
            print(f"\n[COMPLETED] {motion_selected} finished.")
            print(" - Repeat motion: Press 'Enter'")
            print(" - Reset to Home: Press 'r'")

        # 4. COMPLETED -> INITIAL
        elif current_state == HandState.COMPLETED:
            
            if keyboard.is_pressed('r'):
                target_positions = GESTURES['Initial']['set']
                current_state = HandState.INITIAL # 5번 단계인 INITIAL(RETURNING 역할을 함)로 이동
                print("\rState: INITIAL - Returning to Home...", end="")
                time.sleep(0.2) # 키 입력 중복 방지를 위한 짧은 대기
            
            elif keyboard.is_pressed('enter'):
                print("State: Ready")
                if 'ready' in GESTURES[motion_selected]:
                    target_positions = GESTURES[motion_selected]['ready']
                    current_state = HandState.READY
                    print(f"\rState: READY - Moving to {motion_selected} pre-pose...")
                else:
                    target_positions = GESTURES[motion_selected]['set']
                    current_state = HandState.MOVING
                    print(f"\rState: MOVING - Re-executing {motion_selected}...", end="")
                time.sleep(0.2)

        # 5. INITIAL -> IDE
        elif current_state == HandState.INITIAL and max_error < threshold:
            current_state = HandState.IDLE
            print("State: IDLE - Ready for next command.")


        # LPF
        max_error = Set_position_LPF(filtered_positions, target_positions)

        # Set Position
        if current_state != HandState.EMERGENCY:
            for can_id in range(2, 6):
                cmd = [int(p) for p in filtered_positions[can_id]]
                # for Debug
                # print(f"cmd = {cmd}") 
                pcan.set_target_values(can_id, cmd)

        # Emergency Stop
        if keyboard.is_pressed('esc'):
            current_state = HandState.EMERGENCY
            emergency_reset(pcan, target_positions, filtered_positions)
            break

        time_idling(t_start)

    print("Program End")

if __name__== "__main__":
    test_Hand_State_Machine()