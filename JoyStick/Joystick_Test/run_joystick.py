import time

import pygame

from modules.joystick.joystick_manager import JoystickManager  

if __name__ == '__main__':
 
    joystick_manager = JoystickManager()

    joystick_manager.start()
    
    motion_events = {}

    while True:
        if True:
            time.sleep(0.01)
            for event in pygame.event.get():
                print(event)
                if event.type == pygame.JOYAXISMOTION:
                    motion_events[event.axis] = event
                else:
                    action, value = joystick_manager.handle_event(event)

            for axis, latest_event in motion_events.items():
                action, value = joystick_manager.handle_event(latest_event)


            motion_events.clear()
