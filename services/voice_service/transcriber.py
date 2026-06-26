import logging
import numpy as np
import threading
from typing import Optional

from shared.events import bus

logger = logging.getLogger(__name__)

try:
    from faster_whisper import WhisperModel
    HAS_WHISPER = True
except ImportError:
    HAS_WHISPER = False


class Transcriber:
    def __init__(self, model_name: str = "tiny", language: str = "en", download_root: str = "models/whisper"):
        self.language = language
        self._model = None
        self._available = False
        self._model_name = model_name
        self._download_root = download_root
        self._load_thread: Optional[threading.Thread] = None

    def load_async(self):
        if not HAS_WHISPER or self._available:
            return
        self._load_thread = threading.Thread(target=self._load_model, daemon=True)
        self._load_thread.start()
        logger.info("Whisper model loading in background")

    def _load_model(self):
        try:
            logger.info("Loading faster-whisper '%s'...", self._model_name)
            self._model = WhisperModel(self._model_name, device="cpu", compute_type="int8", download_root=self._download_root)
            self._available = True
            logger.info("Whisper model loaded")
        except Exception as e:
            logger.warning("Whisper model load failed: %s", e)

    def transcribe(self, audio: np.ndarray) -> Optional[str]:
        if not self._available or self._model is None:
            return None
        try:
            segments, _ = self._model.transcribe(audio, language=self.language)
            text = " ".join(seg.text for seg in segments).strip()
            if text:
                bus.publish("voice.transcription", {"text": text, "language": self.language}, source="voice-service")
                return text
        except Exception as e:
            logger.error("Transcription failed: %s", e)
        return None

    def is_available(self) -> bool:
        return self._available
