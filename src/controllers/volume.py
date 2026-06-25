import logging
from typing import Optional

logger = logging.getLogger(__name__)

try:
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    from comtypes import CLSCTX_ALL
    import comtypes
    HAS_PYCAW = True
except ImportError:
    HAS_PYCAW = False
    logger.warning("pycaw not available; volume control disabled")


class VolumeController:
    def __init__(self):
        self._interface = None
        self._min_db = -65.0
        self._max_db = 0.0
        self._step = 0.05
        if HAS_PYCAW:
            self._init_pycaw()

    def _init_pycaw(self):
        try:
            comtypes.CoInitialize()
            devices = AudioUtilities.GetSpeakers()
            self._interface = devices.EndpointVolume
            self._min_db, self._max_db, _ = self._interface.GetVolumeRange()
            logger.info("Volume controller initialized")
        except Exception as e:
            logger.warning("Failed to init pycaw: %s", e)
            self._interface = None

    def get_volume(self) -> float:
        if self._interface is None:
            return -1.0
        try:
            return self._interface.GetMasterVolumeLevelScalar()
        except Exception:
            return -1.0

    def set_volume(self, level: float):
        if self._interface is None:
            return
        try:
            self._interface.SetMasterVolumeLevelScalar(max(0.0, min(1.0, level)), None)
            logger.debug("Volume set to %.2f", level)
        except Exception as e:
            logger.error("Failed to set volume: %s", e)

    def volume_up(self, amount: Optional[float] = None):
        step = amount if amount is not None else self._step
        current = self.get_volume()
        if current < 0:
            return
        self.set_volume(min(1.0, current + step))

    def volume_down(self, amount: Optional[float] = None):
        step = amount if amount is not None else self._step
        current = self.get_volume()
        if current < 0:
            return
        self.set_volume(max(0.0, current - step))

    def mute(self):
        if self._interface is None:
            return
        try:
            self._interface.SetMute(1, None)
            logger.debug("Volume muted")
        except Exception as e:
            logger.error("Failed to mute: %s", e)

    def unmute(self):
        if self._interface is None:
            return
        try:
            self._interface.SetMute(0, None)
            logger.debug("Volume unmuted")
        except Exception as e:
            logger.error("Failed to unmute: %s", e)
