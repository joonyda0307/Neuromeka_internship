import time
from pcan_handler import PCANHandler, ServoStatus, ControlMode

# Predefined positions for rock-paper-scissors gestures
GESTURES = {
    'rock': {
        # 주먹 쥐기
        2: [2500, -1000, 2500, 3000],     # 엄지: 안쪽으로 굽히고, z축 회전
        3: [0, 3000, 3000, 3000],     # 검지: 완전히 접기
        4: [0, 3000, 3000, 3000],     # 중지: 완전히 접기
        5: [0, 3000, 3000, 3000]      # 약지/소지: 완전히 접기
    },
    'scissors': {
        # 가위 - 검지와 중지만 펴고 나머지는 접기
        2: [2500, -1000, 2500, 3000],     # 엄지: 안쪽으로 굽히고, z축 회전
        3: [0, 0, 0, 0],                # 검지: 펴기(기본 자세)
        4: [0, 0, 0, 0],                # 중지: 펴기(기본 자세)
        5: [0, 3000, 3000, 3000]      # 약지/소지: 완전히 접기
    },
    'paper': {
        # 보자기 - 기본 자세(영위치)
        2: [0, 0, 0, 0],                # 엄지: 기본 자세
        3: [0, 0, 0, 0],                # 검지: 기본 자세
        4: [0, 0, 0, 0],                # 중지: 기본 자세
        5: [0, 0, 0, 0]                 # 약지/소지: 기본 자세
    },
    'grip_pencil': {
        # 연필 잡기 - 엄지, 검지, 중지로 연필을 잡는 동작
        2: [2000, -2600, 2500, 2500],    # 엄지: 모든 관절을 굽혀서 검지/중지와 마주보도록 함
        3: [-900, 2000, 2500, 2500],       # 검지: 더 굽혀서 엄지와 만나도록 함
        4: [-1200, 3000, 2500, 2500],       # 중지: 검지와 비슷하게 굽혀서 엄지와 만나도록 함
        5: [-1200, 3000, 3000, 3000]        # 약지/소지: 완전히 접기
    }
}

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
        for can_id in range(2, 6): # 레인지 변경을 통해 여러개로 확장 가능.
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
        for can_id in range(2, 6): # 레인지 변경을 통해 여러개로 확장 가능.
            # voltage 0 보내기
            pcan.set_target_values(can_id, [0, 0, 0, 0])
            time.sleep(0.1)

        pcan.close()
        print("\nTest complete!")


def test_rock_paper_scissors():
    # Initialize PCAN
    pcan = PCANHandler()
    if not pcan.is_connected():
        print("Failed to connect to PCAN")
        return

    try:
        print("\n=== Rock Paper Scissors Test ===")
        print("Setting hand ON with position control mode...")
        pcan.set_hand_status(ServoStatus.ON, ControlMode.POSITION)
        time.sleep(1)

        while True:
            print("\nMenu:")
            print("1: Make Rock gesture")
            print("2: Make Scissors gesture")
            print("3: Make Paper gesture")
            print("4: Reset to neutral (Paper position)")
            print("5: Fine-tune current gesture")
            print("6: Test single finger")
            print("7: Read joint positions")
            print("8: Make Pencil grip gesture")
            print("9: Exit")
            
            choice = input("\nEnter your choice (1-9): ")
            
            if choice in ['1', '2', '3']:
                gesture = ['rock', 'scissors', 'paper'][int(choice)-1]
                print(f"\nMaking {gesture} gesture...")
                positions = GESTURES[gesture]
                
                # Apply positions for all fingers simultaneously
                for can_id in range(2, 6):
                    pcan.set_target_values(can_id, positions[can_id])

                time.sleep(1)

                # 각 손가락의 포지션 값 읽기

                # 중요: 수신 전 버퍼에 쌓인 쓸모없는 데이터 싹 비우기
                # while pcan.receive_frame(timeout=0.01):
                #     pass

                print("\nReading joint positions:")
                for can_id in range(2, 6):
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
                
            elif choice == '4':
                print("\nResetting to neutral position (Paper)...")
                positions = GESTURES['paper']
                for can_id in range(2, 6):
                    pcan.set_target_values(can_id, positions[can_id])
                
                # 각 손가락의 포지션 값 읽기
                print("\nReading joint positions:")
                for can_id in range(2, 6):
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
                    
            elif choice == '5':
                try:
                    can_id = int(input("Enter CAN ID to adjust (2-5): "))
                    if not 2 <= can_id <= 5:
                        print("Invalid CAN ID. Must be between 2 and 5")
                        continue
                    
                    print("\nEnter positions for each joint (-3000 to 3000):")
                    positions = []
                    for i in range(4):
                        pos = int(input(f"Joint {i+1}: "))
                        if not -3000 <= pos <= 3000:
                            print(f"Invalid position value. Must be between -3000 and 3000")
                            break
                        positions.append(pos)
                    
                    if len(positions) == 4:
                        pcan.set_target_values(can_id, positions)
                        print(f"\nAdjusted positions for CAN ID {can_id}: {positions}")
                        
                        # 포지션 값 읽기
                        response = pcan.receive_frame(timeout=1.0)
                        if response and 'positions' in response:
                            finger_name = {
                                2: "Thumb",
                                3: "Index",
                                4: "Middle",
                                5: "Ring/Little"
                            }[can_id]
                            print(f"\n{finger_name} (CAN ID {can_id}) current positions:")
                            for i, pos in enumerate(response['positions']):
                                print(f"  Joint {i+1}: {pos}")
                        else:
                            print(f"\nNo response received for CAN ID {can_id}")
                    
                except ValueError:
                    print("Invalid input. Please enter numbers only.")

            elif choice == '6':
                try:
                    print("\nFinger test mode:")
                    print("CAN ID 2: Thumb")
                    print("CAN ID 3: Index finger")
                    print("CAN ID 4: Middle finger")
                    print("CAN ID 5: Ring/Little fingers")
                    
                    can_id = int(input("\nEnter CAN ID to test (2-5): "))
                    if not 2 <= can_id <= 5:
                        print("Invalid CAN ID. Must be between 2 and 5")
                        continue

                    print("\nTesting sequence for selected finger...")
                    # 단계별로 테스트
                    test_positions = [
                        [0, 0, 0, 0],              # 기본 자세
                        [1500, 0, 0, 0],           # 첫 번째 관절만
                        [0, 1500, 0, 0],           # 두 번째 관절만
                        [0, 0, 1500, 0],           # 세 번째 관절만
                        [0, 0, 0, 1500],           # 네 번째 관절만
                        [1500, 1500, 1500, 1500],  # 모든 관절 굽히기
                        [-1500, 0, 0, 0],          # 첫 번째 관절 뒤로
                        [0, -1500, 0, 0],          # 두 번째 관절 뒤로
                        [0, 0, -1500, 0],          # 세 번째 관절 뒤로
                        [0, 0, 0, -1500],          # 네 번째 관절 뒤로
                        [0, 0, 0, 0]               # 다시 기본 자세
                    ]
                    
                    for i, pos in enumerate(test_positions):
                        print(f"\nStep {i+1}: Position = {pos}")
                        pcan.set_target_values(can_id, pos)
                        
                        # 포지션 값 읽기
                        response = pcan.receive_frame(timeout=1.0)
                        if response and 'positions' in response:
                            finger_name = {
                                2: "Thumb",
                                3: "Index",
                                4: "Middle",
                                5: "Ring/Little"
                            }[can_id]
                            print(f"Current positions:")
                            for j, curr_pos in enumerate(response['positions']):
                                print(f"  Joint {j+1}: {curr_pos}")
                        else:
                            print("No response received")
                        
                        time.sleep(2)  # 각 동작 관찰을 위한 대기
                        
                except ValueError:
                    print("Invalid input. Please enter numbers only.")
                
            elif choice == '7':
                test_read_positions()
                
            elif choice == '8':
                print("\nMaking pencil grip gesture...")
                positions = GESTURES['grip_pencil']
                
                # Apply positions for all fingers simultaneously
                for can_id in range(2, 6):
                    pcan.set_target_values(can_id, positions[can_id])
                
                # 각 손가락의 포지션 값 읽기
                print("\nReading joint positions:")
                for can_id in range(2, 6):
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
                
            elif choice == '9':
                break
                
            else:
                print("Invalid choice. Please enter 1-9")

    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"\nError during test: {e}")
    finally:
        # Clean up
        print("\nCleaning up...")
        # Reset to neutral position (paper)
        positions = GESTURES['paper']
        for can_id in range(2, 6):
            pcan.set_target_values(can_id, positions[can_id])
        pcan.set_hand_status(ServoStatus.OFF, ControlMode.POSITION)
        pcan.close()
        print("Test completed")

if __name__ == "__main__":
    # test_rock_paper_scissors()
    test_read_positions()