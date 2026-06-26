import logging
from typing import Optional
from dataclasses import dataclass

from shared.events import bus


@dataclass
class GazeTarget:
    screen_x: float
    screen_y: float
    confidence: float
    is_looking: bool


class GazeController:
    def __init__(self, smoothing: float = 0.4):
        self._smoothing = smoothing
        self._gaze_x = 0.5
        self._gaze_y = 0.5
        self._threshold = 0.03
        self._publish_cooldown = 0.0

    def update(self, gaze_x: float, gaze_y: float, now: float) -> Optional[GazeTarget]:
        self._gaze_x += (gaze_x - self._gaze_x) * self._smoothing
        self._gaze_y += (gaze_y - self._gaze_y) * self._smoothing

        clamped_x = max(0.0, min(1.0, self._gaze_x))
        clamped_y = max(0.0, min(1.0, self._gaze_y))

        is_looking = abs(gaze_x) > self._threshold or abs(gaze_y) > self._threshold

        target = GazeTarget(
            screen_x=clamped_x,
            screen_y=clamped_y,
            confidence=min(1.0, abs(gaze_x) + abs(gaze_y)),
            is_looking=is_looking,
        )

        if now > self._publish_cooldown:
            bus.publish(
                topic="vision.eye.gaze",
                payload={
                    "x": clamped_x,
                    "y": clamped_y,
                    "is_looking": is_looking,
                    "confidence": target.confidence,
                },
                source="eye-service",
            )
            self._publish_cooldown = now + 0.05

        return target

    def reset(self):
        self._gaze_x = 0.5
        self._gaze_y = 0.5
