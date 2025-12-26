import grpc
import Hand_pb2
import Hand_pb2_grpc

def run():
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = Hand_pb2_grpc.HandStub(channel)
        
        while True:
            print("\n=== gRPC Hand Control Menu ===")
            print("1: Rock / 2: Scissors / 3: Paper / 4: Pencil Grip / 5: Exit")
            choice = input("Enter choice: ")

            if choice == '5': break
            
            # 매핑 처리
            gesture_type = {
                '1': Hand_pb2.GestureRequest.ROCK,
                '2': Hand_pb2.GestureRequest.SCISSORS,
                '3': Hand_pb2.GestureRequest.PAPER,
                '4': Hand_pb2.GestureRequest.PENCIL_GRIP
            }.get(choice)

            if gesture_type is not None:
                # 서버에 요청 전송
                response = stub.Gesture(Hand_pb2.GestureRequest(gesture=gesture_type))
                
                # 결과 출력
                print(f"\n[결과] {response.message}")
                for can_id, pos in response.finger_positions.items():
                    print(f"  CAN ID {can_id}: {pos}")
            else:
                print("Invalid input.")

if __name__ == "__main__":
    run()
