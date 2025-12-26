import grpc
from concurrent import futures
import time
from pcan_handler import PCANHandler, ServoStatus, ControlMode 
from coppeliasim_zmqremoteapi_client import RemoteAPIClient
import Hand_pb2
import Hand_pb2_grpc
# 실제 환경에 맞게 PCANHandler와 ServoStatus 등을 import 하세요

# GESTURES = {
#     'rock': {2: [2500, -1000, 2500, 3000], 3: [0, 3000, 3000, 3000], 4: [0, 3000, 3000, 3000], 5: [0, 3000, 3000, 3000]},
#     'scissors': {2: [2500, -1000, 2500, 3000], 3: [0, 0, 0, 0], 4: [0, 0, 0, 0], 5: [0, 3000, 3000, 3000]},
#     'paper': {2: [0, 0, 0, 0], 3: [0, 0, 0, 0], 4: [0, 0, 0, 0], 5: [0, 0, 0, 0]},
#     'grip_pencil': {2: [2000, -2600, 2500, 2500], 3: [-900, 2000, 2500, 2500], 4: [-1200, 3000, 2500, 2500], 5: [-1200, 3000, 3000, 3000]}
# }

GESTURES = {
    'rock': {2: 1.5, 3: 1.5, 4: 1.5, 5: 1.5},
    'scissors': {2: 1.5, 3: 0.0, 4: 0.0, 5: 1.5},
    'paper': {2: 0.0, 3: 0.0, 4: 0.0, 5: 0.0},
    'grip_pencil': {2: 0.8, 3: 1.0, 4: 1.0, 5: 1.5}
}

class HandServicer(Hand_pb2_grpc.HandServicer):
    # def __init__(self):
    #     self.pcan = PCANHandler() # 서버 시작 시 하드웨어 연결
    #     if self.pcan.is_connected():
    #         print("PCAN Connected")
    #         self.pcan.set_hand_status(ServoStatus.ON, ControlMode.POSITION)
    #     else:
    #         print("PCAN Connection Failed")
    
    def __init__(self):
        # 1. 코펠리아심 연결
        self.client = RemoteAPIClient()
        self.sim = self.client.getObject('sim')
        print("CoppeliaSim Connected!")

        all_objects = self.sim.getObjectsInTree(self.sim.handle_scene)

        print("--- 현재 CoppeliaSim 내 오브젝트 리스트 ---")
        for handle in all_objects:
            name = self.sim.getObjectAlias(handle)
            print(f"Name: {name}")
        print("------------------------------------------")

        # 2. 시뮬레이션 내 손가락 조인트 핸들 가져오기 (반복문 사용)
        self.joint_handles = {}
        fingers = ['thumb', 'index', 'middle', 'ring']

        for finger in fingers:
            # 각 손가락의 기본 경로 설정 (joint_0)
            base_path = f'/mount_respondable/kistar_mount_joint/palm_respondable/{finger}_base_joint/{finger}_basemotor_respondable/{finger}_joint_0'
            self.joint_handles[f'{finger}_joint_0'] = self.sim.getObject(base_path)
            
            # joint_1부터 joint_3까지 계층 구조를 따라 경로 생성
            current_full_path = base_path
            for i in range(1, 4):
                # 이전 joint 경로 뒤에 link_respondable과 다음 joint를 붙여 나감
                current_full_path += f'/{finger}_link_{i-1}_respondable/{finger}_joint_{i}'
                self.joint_handles[f'{finger}_joint_{i}'] = self.sim.getObject(current_full_path)

        print(f"총 {len(self.joint_handles)}개의 조인트 핸들을 로드했습니다.")

    
    # def Gesture(self, request, context):
    #     # 1. 요청에 따른 제스처 이름 매핑
    #     mapping = {
    #         Hand_pb2.GestureRequest.ROCK: 'rock',
    #         Hand_pb2.GestureRequest.SCISSORS: 'scissors',
    #         Hand_pb2.GestureRequest.PAPER: 'paper',
    #         Hand_pb2.GestureRequest.PENCIL_GRIP: 'grip_pencil',
    #         Hand_pb2.GestureRequest.NEUTRAL: 'paper'
    #     }
    #     gesture_name = mapping.get(request.gesture)
    #     positions = GESTURES[gesture_name]

    #     print(f"[서버] {gesture_name} 동작 수행 중...")
        
    #     # 2. 하드웨어 명령 전송
    #     for can_id in range(2, 6):
    #         print(f"Send {can_id} CMD: {positions[can_id]}")
    #         # self.pcan.set_target_values(can_id, positions[can_id])
        
    #     time.sleep(1) # 동작 대기

    #     # 3. 현재 위치 읽기 (결과 리턴용)
    #     readings = {}
    #     # for can_id in range(2, 6):
    #     #     response = self.pcan.receive_frame(timeout=0.5)
    #     #     if response and 'positions' in response:
    #     #         readings[can_id] = str(response['positions'])
    #     #     else:
    #     #         readings[can_id] = "No Response"

    #     return Hand_pb2.GestureResponse(
    #         success=True,
    #         message=f"{gesture_name} 완료",
    #         finger_positions= readings
    #     )

    def Gesture(self, request, context):
    # 1. 요청에 따른 제스처 이름 매핑
        mapping = {
            Hand_pb2.GestureRequest.ROCK: 'rock',
            Hand_pb2.GestureRequest.SCISSORS: 'scissors',
            Hand_pb2.GestureRequest.PAPER: 'paper',
            Hand_pb2.GestureRequest.PENCIL_GRIP: 'grip_pencil',
            Hand_pb2.GestureRequest.NEUTRAL: 'paper'
        }
        
        # CAN ID와 손가락 이름 매핑 (시뮬레이션 관절 매핑용)
        id_to_finger = {2: 'thumb', 3: 'index', 4: 'middle', 5: 'ring'}
        
        gesture_name = mapping.get(request.gesture, 'paper')
        target_values = GESTURES[gesture_name]

        print(f"[서버] {gesture_name} 동작 수행 중...")

        readings = {}
        # 2. 시뮬레이션 및 하드웨어 명령 전송
        for can_id, target_pos in target_values.items():
            finger_name = id_to_finger[can_id]
            readings[can_id] = str(target_pos)
            print(f"[{finger_name}] Target Position: {target_pos}")
            
            # --- 시뮬레이션 제어 추가 ---
            # 각 손가락의 4개 관절(joint_0~3)에 대해 제어 명령 전송
            # 실제 로봇의 구조에 따라 특정 joint에만 값을 주거나 비율을 조정할 수 있습니다.
            for i in range(4):
                joint_key = f'{finger_name}_joint_{i}'
                handle = self.joint_handles.get(joint_key)
                if handle is not None:
                    # joint_0은 회전(Yaw), 1~3은 굽힘(Pitch)일 경우가 많으므로 
                    # 보통 1~3 관절에 굽힘 값(target_pos)을 적용합니다.
                    if i == 0:
                        # joint_0(기부 관절)은 보통 0으로 고정하거나 필요시 제어
                        self.sim.setJointTargetPosition(handle, 0.0)
                    else:
                        # joint_1, 2, 3 관절에 동일한 굽힘 각도 적용
                        self.sim.setJointTargetPosition(handle, target_pos)

            # --- 하드웨어 제어 (주석 해제 시 동작) ---
            # self.pcan.set_target_values(can_id, target_pos)
        
        # 시뮬레이션에서 동작이 반영될 시간 대기
        time.sleep(0.5) 

        # 3. 결과 리턴
        return Hand_pb2.GestureResponse(
            success=True,
            message=f"{gesture_name} 시뮬레이션 적용 완료",
            finger_positions=readings
        )


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    Hand_pb2_grpc.add_HandServicer_to_server(HandServicer(), server)
    server.add_insecure_port('[::]:50051')
    print("gRPC Hand Server started on 50051...")
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
