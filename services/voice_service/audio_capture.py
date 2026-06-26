import numpy as np
import sounddevice as sd
import logging
import threading
from typing import Optional, Callable

logger = logging.getLogger(__name__)


class AudioCapture:
    def __init__(self, sample_rate: int = 16000, chunk_seconds: float = 4.0):
        self.sample_rate = sample_rate
        self.chunk_samples = int(sample_rate * chunk_seconds)
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._callback: Optional[Callable[[np.ndarray], None]] = None

    def start(self, callback: Callable[[np.ndarray], None]):
        self._callback = callback
        self._running = True
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()
        logger.info("Audio capture started (rate=%d, chunk=%.1fs)", self.sample_rate, self.chunk_samples / self.sample_rate)

    def _capture_loop(self):
        buffer = np.zeros(0, dtype=np.float32)
        with sd.InputStream(samplerate=self.sample_rate, channels=1, dtype='float32') as stream:
            while self._running:
                chunk, _ = stream.read(int(self.sample_rate * 0.1))
                buffer = np.append(buffer, chunk.flatten())
                if len(buffer) >= self.chunk_samples:
                    if self._callback:
                        self._callback(buffer[:self.chunk_samples].copy())
                    buffer = np.zeros(0, dtype=np.float32)

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
        logger.info("Audio capture stopped")
