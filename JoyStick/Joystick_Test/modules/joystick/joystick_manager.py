import threading
import pygame
import time
import os
from modules.global_data import MODULE_PATH, JoystickCommand
from modules.global_func import get_time
from pkg.utils.blackboard import GlobalBlackboard
from pkg.utils.file_io import load_json
from pkg.utils.logging import Logger
from queue import Queue

bb = GlobalBlackboard()

class JoystickManager():
    default_deadzone = 0.2 #0.18 
    default_gain = 0.2
    POLL_INTERVAL= 1.0
    round_digit = 2
    def __init__(self, *args, **kwargs):
        # 초기화
        self.event_queue = Queue()  # FIFO 큐
        self.event_list = []
        self.connected = {}
        self.dpad_map = {}
        self.thread = None
        self.axis_map = {}      # axis 번호 → action
        self.prev_axis = {}     # axis 번호 → 이전 값 저장

        self.load_model()

        pygame.init()
        pygame.joystick.quit() # 강제 재초기화

        pygame.joystick.init()

        pygame.event.set_allowed([pygame.JOYDEVICEADDED,
                          pygame.JOYDEVICEREMOVED,
                          pygame.JOYAXISMOTION,
                          pygame.JOYBUTTONDOWN,
                          pygame.JOYBUTTONUP])
        
        self.last_poll_time = time.time()

        self.scan_joysticks(initial=True)
        self.running = False
        self.start()

    def load_model(self):
        joystick_info = load_json(os.path.join(MODULE_PATH, "joystick", "joystick_info.json"))
        target_model = "handheld"
        self.joystick_deadzone = self.default_deadzone
        self.joystick_gain = self.default_gain
        max_delta = joystick_info.get("max_delta", {})
        self.max_zoom_delta = max_delta.get("zoom")
        self.max_tilt_w_delta = max_delta.get("tilt_w")
        self.max_tilt_u_delta = max_delta.get("tilt_u")
        self.max_tilt_v_delta = max_delta.get("tilt_v")
        self.dpad_map = {
            joystick_info["controllers"][target_model]["buttons"]["R"]:JoystickCommand.VOICE_ON, # 3
            joystick_info["controllers"][target_model]["buttons"]["R_2"]:JoystickCommand.VOICE_ON, # 3

            joystick_info["controllers"][target_model]["buttons"]["x2"]: JoystickCommand.ZOOM_IN, # 8
            joystick_info["controllers"][target_model]["buttons"]["x3"]: JoystickCommand.ZOOM_OUT,  # 9

            joystick_info["controllers"][target_model]["buttons"]["x1"]:JoystickCommand.TILT_W_CW, # 3
            joystick_info["controllers"][target_model]["buttons"]["x4"]:JoystickCommand.TILT_W_CCW, # 3

            joystick_info["controllers"][target_model]["buttons"]["x5"]:JoystickCommand.ENABLE, # 3
            
        }
        self.axis_map = {
            joystick_info["controllers"][target_model]["axes"]["up_down"]: JoystickCommand.TILT_V, # 1
            joystick_info["controllers"][target_model]["axes"]["left_right"]: JoystickCommand.TILT_U, # 0
            joystick_info["controllers"][target_model]["axes"]["trigger"]: JoystickCommand.UPDATE_GAIN, # 0
        }


    def scan_joysticks(self, initial=False):
        """현재 연결된 조이스틱 스캔"""
        js_dict = {}
        for i in range(pygame.joystick.get_count()):
            js = pygame.joystick.Joystick(i)
            js.init()
            js_dict[i] = js

        if initial:
            if js_dict:
                print(f"초기 연결: {[js.get_name() for js in js_dict.values()]}")
            else:
                print("초기 연결된 조이스틱 없음")

        return js_dict


    def poll_joysticks(self):
        if time.time() - self.last_poll_time > self.POLL_INTERVAL:
            current = self.scan_joysticks()
            # 새로 연결된 조이스틱
            for jid, js in current.items():
                if jid not in self.connected:
                    self.connected[jid] = js
                    Logger.debug(f"{get_time()}: [Joystick] 연결됨 (폴링): {js.get_name()}")
                    bb.set("joystick/state/connect",True)
                    
            # 해제된 조이스틱
            for jid, js in list(self.connected.items()):
                if jid not in current:
                    self.connected.pop(jid)
                    Logger.debug(f"{get_time()}: [Joystick] 해제됨 (폴링): {js.get_name()}")
                    bb.set("joystick/state/connect",False)
            self.last_poll_time = time.time()

    def handle_event(self, event):
        action, value = None, None
        """이벤트별 처리 로직"""
        if event.type == pygame.JOYDEVICEADDED:
            js = pygame.joystick.Joystick(event.device_index)
            js.init()
            self.connected[event.device_index] = js
            action = JoystickCommand.DISCONNECT
            value = None
            Logger.debug(f"{get_time()}: [Joystick] 연결됨 (이벤트): {js.get_name()}")

            bb.set("joystick/state/connect",True)

        elif event.type == pygame.JOYDEVICEREMOVED:
            js = self.connected.pop(event.instance_id, None)
            if js:
                action = JoystickCommand.DISCONNECT
                value = None
                Logger.debug(f"{get_time()}: [Joystick] 해제됨 (이벤트): {js.get_name()}")
                bb.set("joystick/state/connect",False)

        elif event.type == pygame.JOYAXISMOTION:
            event_axis = event.axis
            action = self.axis_map.get(event_axis)
            if action:
                event_value = round(float(event.value), self.round_digit)
                # print(event_value,self.joystick_deadzone)
                if abs(event_value) < self.joystick_deadzone:
                    event_value = 0.0

                prev_value = self.prev_axis.get(event_axis, None)
                if prev_value == None: # self.prev_axis[event_axis]
                    prev_value = event_value
                    value = 0
                    action = None

                elif prev_value != event_value:
                    value = event_value * self.joystick_gain
                else:
                    value = 0
                    action = None
                self.prev_axis[event_axis]  = event_value

        elif event.type == pygame.JOYBUTTONDOWN:
            # print(event.button)
            action = self.dpad_map.get(event.button)
            if action:
                value = True

        elif event.type == pygame.JOYBUTTONUP:
            action = self.dpad_map.get(event.button)
            if action:
                value = False

        if action is not None:
            # self.event_queue.put((action, value))
            self.event_list.append((action, value))

            #
            return action,value
        else:
            return None, None

    def start(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self.run, daemon=True)
            self.thread.start()

    def stop(self):
        if self.running:
            self.running = False
            if self.thread:
                self.thread.join()

    def run(self):
        while self.running:
            try:
                time.sleep(100)                

            except Exception as e:
                self.stop()

        
if __name__ == "__main__":
    manager = JoystickManager()
    manager.start()
    try:
        manager.run()
    except KeyboardInterrupt:
        manager.stop()