import can
import time
from enum import Enum
from typing import Dict, Any, Optional

class ControlMode(Enum):
    VOLTAGE = 0x0000
    POSITION = 0x00FF

class ServoStatus(Enum):
    OFF = 0x0000
    ON = 0x00FF

class PCANHandler:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(PCANHandler, cls).__new__(cls)
        return cls._instance

    def __init__(self, channel='PCAN_USBBUS1', bitrate=1000000) -> None:
        if hasattr(self, '_initialized') and self._initialized:
            return
        self.bus = None
        self._initialized = True
        self._is_connected = False
        self._channel = channel
        self._bitrate = bitrate
        
        try:
            self._connect_to_bus()
        except Exception as e:
            self._is_connected = False
            print(f"Failed to initialize PCAN: {e}")

    def _connect_to_bus(self) -> bool:
        """Connect to the CAN bus"""
        try:
            if self.bus is not None:
                try:
                    self.bus.shutdown()
                except Exception as e:
                    print(f"Error during bus shutdown: {e}")
                self.bus = None
                time.sleep(0.1)
            
            self.bus = can.interface.Bus(bustype='pcan', channel=self._channel, bitrate=self._bitrate)
            self._is_connected = True
            print(f"Connected to PCAN: channel={self._channel}, bitrate={self._bitrate}")
            return True
                
        except Exception as e:
            self._is_connected = False
            print(f"Failed to connect to PCAN: {e}")
            return False

    def set_hand_status(self, status: ServoStatus, mode: ControlMode) -> bool:
        """Set both servo status and control mode in a single message
        
        Args:
            status: ServoStatus.ON or ServoStatus.OFF
            mode: ControlMode.VOLTAGE or ControlMode.POSITION
        """
        if not self._is_connected or self.bus is None:
            return False
            
        try:
            data = bytearray(8)
            # First byte: Status (D1)
            data[0] = status.value & 0xFF
            # Second byte: Mode (D2)
            data[1] = mode.value & 0xFF
            # Other bytes are don't care (XX)

            print("Setting servo status: ", data)

            msg = can.Message(arbitration_id=1, data=data, is_extended_id=False)
            self.bus.send(msg)
            time.sleep(0.001)
            return True
        except Exception as e:
            print(f"Error setting hand status: {e}")
            return False

    def set_target_values(self, can_id: int, targets: list) -> bool:
        """Set target values for the actuators
        
        Args:
            can_id: CAN ID (2-5)
            targets: List of target values for 4 joints
        """
        if not 2 <= can_id <= 5 or not self._is_connected or self.bus is None:
            return False
            
        try:
            data = bytearray(8)  # 8 bytes for 4 joints (2 bytes each)
            
            # Pack 4 joint values into the data field
            # Each joint value uses 2 bytes (high byte and low byte)
            for i in range(min(len(targets), 4)):
                target = targets[i]
                data[i*2] = (target >> 8) & 0xFF     # High byte (D1, D3, D5, D7)
                data[i*2 + 1] = target & 0xFF        # Low byte (D2, D4, D6, D8)
            
            # Send message only to the specified CAN ID
            msg = can.Message(arbitration_id=can_id, data=data, is_extended_id=False)
            self.bus.send(msg)
            
            time.sleep(0.001)
            return True
        except Exception as e:
            print(f"Error setting target values: {e}")
            return False

    def receive_frame(self, timeout: float = 0.01) -> Optional[Dict[str, Any]]:
        """Receive and parse a CAN frame
        
        Returns:
            Dictionary containing parsed data or None if no data received
        """
        if not self._is_connected or self.bus is None:
            return None
            
        try:
            msg = self.bus.recv(timeout=timeout)
            if msg is None:
                return None
                
            can_id = msg.arbitration_id
            data = msg.data
            
            if can_id == 1:  # Status message
                # D1: Servo status (1 byte)
                status1 = data[0]
                # D2: Control mode (1 byte)
                status2 = data[1]
                return {
                    'can_id': can_id,
                    'servo_status': status1,
                    'control_mode': status2
                }
            elif 2 <= can_id <= 5:  # Position feedback
                positions = []
                # Parse 4 joint positions (2 bytes each)
                for i in range(4):
                    position = (data[i*2] << 8) | data[i*2 + 1]
                    # Convert to signed integer if in position mode
                    if position > 32767:
                        position -= 65536
                    positions.append(position)
                return {
                    'can_id': can_id,
                    'positions': positions
                }
            
            return None
        except Exception as e:
            print(f"Error receiving frame: {e}")
            return None

    def close(self) -> None:
        """Close the CAN bus connection"""
        try:
            if self.bus is not None:
                self.bus.shutdown()
                self._is_connected = False
                print("PCAN bus closed")
        except Exception as e:
            print(f"Error closing PCAN bus: {e}")

    def is_connected(self) -> bool:
        """Check if PCAN is connected"""
        return self._is_connected and self.bus is not None