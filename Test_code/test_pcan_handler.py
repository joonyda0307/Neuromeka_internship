import time
from pcan_handler import PCANHandler, ServoStatus, ControlMode
import keyboard 

# Predefined positions for rock-paper-scissors gestures
GESTURES = {
    
    # Grasping Motions
    # 1
    'Side Grasp': {
        # 원통형 물체 옆으로 잡기 (측정 데이터 반영)
        2: [3672, -3745, 1155, 2402],  # Thumb
        3: [142, 1471, 2624, 1298],    # Index
        4: [133, 2385, 1541, 2263],    # Middle
        5: [214, 2235, 2106, 1523]     # Ring/Little
    },

    # 2
    'Top Grasp': {
        # 넓은 원통 물체 위에서 아래로 잡기
        2: [2405, -2683, 794, 2079],   # Thumb
        3: [-156, 1232, 2101, 1191],   # Index
        4: [81, 1288, 1601, 2054],     # Middle
        5: [1903, 3039, 1841, 893]     # Ring/Little
    },

    # 3
    'Pinch_2pt': {
        # 2점 핀치: 엄지와 검지 끝을 맞댐
        2: [2828, -3215, 1986, 1687],  # Thumb
        3: [-92, 1925, 2768, 1286],    # Index
        4: [82, -110, 765, 1843],      # Middle
        5: [78, -175, 1416, 816]       # Ring/Little
    },

    # 4
    'Pinch_3pt': {
        # 2점 핀치: 엄지와 검지 끝을 맞댐
        2: [3532, -3110, 890, 3608],   # Thumb
        3: [-594, 1971, 3615, 1200],   # Index
        4: [900, 2162, 2650, 2028],    # Middle
        5: [1160, -678, 1229, 732]     # Ring/Little
    },

    # 5
    'Card Grasp': {
        2: [2351, -3774, 2720, 2235],  # Thumb
        3: [867, 1335, 4699, 1094],    # Index
        4: [600, 3680, 4190, 2352],    # Middle
        5: [149, 4148, 4500, 726]      # Ring/Little
    },

    # Task Specific Motions

    # 6
    'grip_pencil': {
        # 연필 잡기: 엄지, 검지, 중지의 삼각지지
        2: [2000, -2600, 2500, 2500], 
        3: [-900, 2000, 2500, 2500], 
        4: [-1200, 3000, 2500, 2500], 
        5: [-1200, 3000, 3000, 3000]
    },

    # 7
    'rock': { 
        2: [2500, -1000, 2500, 3000],  # 엄지: 안쪽 접기
        3: [0, 3000, 3000, 3000],     # 검지: 완전히 접기
        4: [0, 3000, 3000, 3000],     # 중지: 완전히 접기
        5: [0, 3000, 3000, 3000]      # 약지/소지: 완전히 접기
    },

    # 8
    'scissors': {
        2: [2500, -1000, 2500, 3000], 
        3: [0, 0, 0, 0],              # 검지: 펴기
        4: [0, 0, 0, 0],              # 중지: 펴기
        5: [0, 3000, 3000, 3000]
    },

    # 9
    'paper': {
        2: [0, 0, 0, 0], 
        3: [0, 0, 0, 0], 
        4: [0, 0, 0, 0], 
        5: [0, 0, 0, 0] 
    },
    
    # # 10
    # 'push_start': {
    #     2: [2500, -1000, 2500, 3000],  # 엄지: 안쪽 접기
    #     3: [0, 3000, 3000, 3000],     # 검지: 완전히 접기
    #     4: [0, 3000, 3000, 3000],     # 중지: 완전히 접기
    #     5: [0, 3000, 3000, 3000]      # 약지/소지: 완전히 접기
    # },

    # 'push_end':   {
    #     2: [2500, -1000, 2500, 3000],  # 엄지: 안쪽 접기
    #     3: [0, 3000, 3000, 3000],     # 검지: 완전히 접기
    #     4: [0, 3000, 3000, 3000],     # 중지: 완전히 접기
    #     5: [0, 3000, 3000, 3000]      # 약지/소지: 완전히 접기
    # }, # 검지만 최대로 폄 (혹은 굽힘)

    # 11
    # 'hook_start': {
    #     2:, 
    #     3:, 
    #     4:, 
    #     5:
    # },

    # 'hook_end':   {
    #     2:, 
    #     3:[0,2000,2000,0], 
    #     4:, 
    #     5:
    # }, # 검지만 갈고리 모양
}



# for Emergency stop
def emergency_reset(pcan, target_positions, filtered_positions):
    print("\n!!! EMERGENCY STOP ACTIVATED !!!")
    for can_id in range(2, 6):
        target_positions[can_id] = list(filtered_positions[can_id])
        pcan.set_target_values(can_id, target_positions[can_id])
    
    pcan.set_hand_status(ServoStatus.OFF, ControlMode.POSITION)
    print("Torque disabled. Please restart the program to re-enable.")
    return True


# Control test code (made by joon)
def test_Hand():
    # Initialize PCAN
    pcan = PCANHandler()
    if not pcan.is_connected():
        print("Failed to connect to PCAN")
        return

    # prameter setting
    alpha = 0.05 # alpha: 0.0 ~ 1.0 (1.0에 가까울수록 반응이 빠르고, 0에 가까울수록 부드러움)
    threshold = 5.0 # Convergence threshold
    Sampling_freq = 50
    dt = 1.0 / Sampling_freq


    target_positions = {id: [0,0,0,0] for id in range(2, 6)}
    filtered_positions = {id: [0.0, 0.0, 0.0, 0.0] for id in range(2, 6)}
    
    pcan.set_hand_status(ServoStatus.ON, ControlMode.POSITION)
    time.sleep(0.5) # 서보 안정화 대기
    # Receive buf를 초기화
    while pcan.receive_frame(timeout=.01): pass
    is_emergency = False

    # 매핑 확장 (1~9번까지 GESTURES 키와 연결)
    gesture_map = {
        '1': 'Side Grasp',
        '2': 'Top Grasp',
        '3': 'Pinch_2pt',
        '4': 'Pinch_3pt',
        '5': 'Card Grasp',
        '6': 'grip_pencil',
        '7': 'rock',
        '8': 'scissors',
        '9': 'paper'
    }

    # Outer Setting loop
    while True:
        # 1. Select gesture
        print("\n" + "="*30)
        print(" [ Gesture Menu ]")
        for key, name in gesture_map.items():
            print(f" {key}: {name}")
        print(" 0: Exit (Program End)")
        print("="*30)
        choice = input("Select Gesture: ")
        
        if choice == '0': break
        
        # 2. update target buf
        if choice in gesture_map:
            gesture_key = gesture_map[choice]
            target_update = GESTURES[gesture_key]
            for can_id in range(2, 6):
                target_positions[can_id] = target_update[can_id]
            print(f"\nMoving to [{gesture_key}]... (Press 'ESC' to Stop)")
        else:
            print("Invalid choice. Try again.")
            continue

        # Inner control loop
        while True:
            t_start = time.perf_counter()

            # chect emergency stop
            if keyboard.is_pressed('esc'): 
                emergency_reset(pcan, target_positions, filtered_positions)
                is_emergency = True
                break # Exit inner loop

            max_error = 0
            for can_id in range(2, 6):
                # 1. LPF (Low Pass Filter: Y = a*Target + (1-a)*Prev_Y) and 
                for i in range(4):
                    filtered_positions[can_id][i] = \
                        (alpha * target_positions[can_id][i]) + ((1 - alpha) * filtered_positions[can_id][i])
                    max_error += abs(target_positions[can_id][i] - filtered_positions[can_id][i])
                
                # 2. CMD input (change int)
                cmd = [int(p) for p in filtered_positions[can_id]]
                print(f"cmd = {cmd}")
                pcan.set_target_values(can_id, cmd)

            # clear buf
            while pcan.receive_frame(timeout=0.001): pass

            # 4. Convergence check
            if max_error < threshold:
                print("Gesture completed (Converged).")
                break
            
            # Time Idling
            time.sleep(max(0, dt - (time.perf_counter() - t_start)))

        if is_emergency:
            print("Exiting due to emergency.")
            break

    print("Program terminated.")


def test_read_positions():
    # Initialize PCAN
    pcan = PCANHandler()
    if not pcan.is_connected():
        print("Failed to connect to PCAN")
        return

    try:
        print("\n=== Joint Position Reading Test ===")
        print("Setting hand ON with voltage control mode...")
        pcan.set_hand_status(ServoStatus.ON, ControlMode.VOLTAGE)
        time.sleep(0.1)

        # Receive buf를 초기화
        while pcan.receive_frame(timeout=0.01): pass

        input("\nPress Enter to send voltage 0 to all joints and read positions...")

        # 각 손가락별로 voltage 0 보내고 바로 포지션 읽기
        print("\nSending voltage 0 and reading positions for each finger:")
        for can_id in range(2, 6):
            # voltage 0 보내기
            pcan.set_target_values(can_id, [0, 0, 0, 0])
            time.sleep(0.1)
            
            # 바로 응답 읽기
            response = pcan.receive_frame(timeout=1.0)
            if response and 'positions' in response:
                finger_name = {
                    2: "Thumb",
                    3: "Index",
                    4: "Middle",
                    5: "Ring/Little"
                }[can_id]
                print(f"\n{finger_name} (CAN ID {can_id}):")
                for i, pos in enumerate(response['positions']):
                    print(f"  Joint {i+1}: {pos}")
            else:
                print(f"\nNo response received for CAN ID {can_id}")

    except Exception as e:
        print(f"\nError during test: {e}")

    finally:
        for can_id in range(2, 6):
            # voltage 0 보내기
            pcan.set_target_values(can_id, [0, 0, 0, 0])
            time.sleep(0.1)

        pcan.close()
        print("\nTest complete!")


if __name__ == "__main__":
    # test_read_positions()
    test_Hand()