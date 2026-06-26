import logging
import numpy as np
from typing import Optional

from shared.events import bus, Event
from .audio_capture import AudioCapture
from .transcriber import Transcriber
from .intent_parser import IntentParser

logger = logging.getLogger(__name__)


class VoiceService:
    def __init__(self):
        self.audio = AudioCapture(sample_rate=16000, chunk_seconds=4.0)
        self.transcriber = Transcriber(model_name="tiny", language="en")
        self.intent = IntentParser()
        self._setup()

    def _setup(self):
        bus.subscribe("voice.command", self._on_voice_command, "voice-service")

    def start(self):
        self.transcriber.load_async()
        self.audio.start(self._on_audio)
        logger.info("Voice service started (model loading in background)")

    def _on_audio(self, audio: np.ndarray):
        text = self.transcriber.transcribe(audio)
        if text:
            intent = self.intent.parse(text)
            if intent:
                bus.publish(
                    "voice.command",
                    intent,
                    source="voice-service",
                )
                logger.info("Voice command: %s → %s", intent["text"], intent["action"])

    def _on_voice_command(self, event: Event):
        pass  # Action service will handle via event bus subscription

    def stop(self):
        self.audio.stop()
        logger.info("Voice service stopped")
