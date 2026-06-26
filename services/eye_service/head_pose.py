import logging
from dataclasses import dataclass
from typing import Optional

from shared.events import bus


@dataclass
class HeadAction:
    direction: str
    confidence: float
    angle_delta: tuple


class HeadPoseController:
    def __init__(self, pitch_threshold: float = 20.0, yaw_threshold: float = 25.0):
        self._pitch_threshold = pitch_threshold
        self._yaw_threshold = yaw_threshold
        self._prev_pitch = 0.0
        self._prev_yaw = 0.0
        self._cooldown_until = 0.0

    def update(self, head_pose: dict, now: float) -> Optional[HeadAction]:
        pitch = head_pose.get("pitch", 0.0)
        yaw = head_pose.get("yaw", 0.0)

        if now < self._cooldown_until:
            self._prev_pitch, self._prev_yaw = pitch, yaw
            return None

        action = None
        if abs(yaw) > self._yaw_threshold and abs(yaw - self._prev_yaw) > 10:
            direction = "look_right" if yaw > 0 else "look_left"
            action = HeadAction(direction, min(1.0, abs(yaw) / 45.0), (pitch, yaw))
        elif abs(pitch) > self._pitch_threshold and abs(pitch - self._prev_pitch) > 10:
            direction = "look_down" if pitch > 0 else "look_up"
            action = HeadAction(direction, min(1.0, abs(pitch) / 30.0), (pitch, yaw))

        self._prev_pitch, self._prev_yaw = pitch, yaw

        if action:
            bus.publish(
                topic="vision.head.pose",
                payload={
                    "direction": action.direction,
                    "confidence": action.confidence,
                    "pitch": pitch,
                    "yaw": yaw,
                },
                source="eye-service",
            )
            logger.info(f"Head: {action.direction} ({action.confidence:.2f})")

        return action

    def reset(self):
        self._prev_pitch = 0.0
        self._prev_yaw = 0.0
        self._cooldown_until = 0.0


logger = logging.getLogger(__name__)
