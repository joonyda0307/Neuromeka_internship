"""Shared global singletons separated from configuration constants."""

voice_manager = None
from modules.joystick.joystick_manager import JoystickManager  # noqa: WPS433

joystick_manager = JoystickManager()


