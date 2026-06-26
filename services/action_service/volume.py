import logging

logger = logging.getLogger(__name__)

try:
    from pycaw.pycaw import AudioUtilities
    import comtypes
    HAS_PYCAW = True
except ImportError:
    HAS_PYCAW = False


class VolumeController:
    def __init__(self):
        self._iface = None
        self._step = 0.05
        if HAS_PYCAW:
            self._init()

    def _init(self):
        try:
            comtypes.CoInitialize()
            self._iface = AudioUtilities.GetSpeakers().EndpointVolume
            logger.info("Volume controller ready")
        except Exception as e:
            logger.warning("Volume init failed: %s", e)

    def get(self) -> float:
        if not self._iface:
            return -1.0
        try:
            return self._iface.GetMasterVolumeLevelScalar()
        except:
            return -1.0

    def set(self, level: float):
        if not self._iface:
            return
        try:
            self._iface.SetMasterVolumeLevelScalar(max(0.0, min(1.0, level)), None)
        except Exception as e:
            logger.error("Volume set failed: %s", e)

    def up(self, amt: float = None):
        v = self.get()
        if v < 0:
            return
        self.set(min(1.0, v + (amt or self._step)))

    def down(self, amt: float = None):
        v = self.get()
        if v < 0:
            return
        self.set(max(0.0, v - (amt or self._step)))

    def mute(self):
        if self._iface:
            try:
                self._iface.SetMute(1, None)
            except:
                pass

    def unmute(self):
        if self._iface:
            try:
                self._iface.SetMute(0, None)
            except:
                pass
