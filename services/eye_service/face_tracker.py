import cv2
import numpy as np
import logging
from pathlib import Path
from typing import Optional

from mediapipe.tasks.python.vision import face_landmarker as fl
from mediapipe.tasks.python.vision.core.image import Image, ImageFormat
from mediapipe.tasks.python.core.base_options import BaseOptions

from shared.types import Landmark, FaceData

logger = logging.getLogger(__name__)


class FaceTracker:
    LEFT_EYE = [33, 246, 161, 160, 159, 158, 157, 173, 133, 155, 154, 153, 145, 144, 163, 7]
    RIGHT_EYE = [362, 398, 384, 385, 386, 387, 388, 466, 263, 249, 390, 373, 374, 380, 381, 382]
    LEFT_IRIS = 468
    RIGHT_IRIS = 473

    LEFT_EAR_PTS = (33, 159, 158, 133, 153, 145)
    RIGHT_EAR_PTS = (362, 387, 386, 263, 373, 380)

    NOSE_TIP = 1
    CHIN = 199
    LEFT_EYE_OUTER = 33
    LEFT_EYE_INNER = 133
    RIGHT_EYE_OUTER = 362
    RIGHT_EYE_INNER = 263
    MOUTH_LEFT = 61
    MOUTH_RIGHT = 291

    def __init__(self, model_path: str = "models/face_landmarker.task"):
        model_file = Path(model_path)
        if not model_file.exists():
            raise FileNotFoundError(f"Face model not found: {model_path}")
        options = fl.FaceLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=str(model_file)),
            num_faces=1,
            min_face_detection_confidence=0.5,
            min_face_presence_confidence=0.5,
            min_tracking_confidence=0.5,
            output_face_blendshapes=False,
            output_facial_transformation_matrixes=True,
        )
        self._landmarker = fl.FaceLandmarker.create_from_options(options)

    def process(self, frame: np.ndarray) -> Optional[FaceData]:
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = Image(ImageFormat.SRGB, rgb)
        result = self._landmarker.detect(image)

        if not result.face_landmarks:
            return None

        landmarks = result.face_landmarks[0]
        lm_list = [
            Landmark(x=lm.x, y=lm.y, z=lm.z, visibility=getattr(lm, 'visibility', 1.0) or 1.0)
            for lm in landmarks
        ]

        left_ear = self._compute_ear(lm_list, self.LEFT_EAR_PTS)
        right_ear = self._compute_ear(lm_list, self.RIGHT_EAR_PTS)

        left_iris = lm_list[self.LEFT_IRIS] if self.LEFT_IRIS < len(lm_list) else None
        right_iris = lm_list[self.RIGHT_IRIS] if self.RIGHT_IRIS < len(lm_list) else None

        gaze = self._estimate_gaze(lm_list, left_iris, right_iris)
        head_pose = self._estimate_head_pose(lm_list)

        left_eye_pts = self._eye_center(lm_list, self.LEFT_EYE)
        right_eye_pts = self._eye_center(lm_list, self.RIGHT_EYE)

        return FaceData(
            landmarks=lm_list,
            head_pose=head_pose,
            left_eye={
                "center": left_eye_pts,
                "aspect_ratio": left_ear,
                "open": left_ear > 0.2,
            },
            right_eye={
                "center": right_eye_pts,
                "aspect_ratio": right_ear,
                "open": right_ear > 0.2,
            },
            gaze=gaze,
        )

    def _compute_ear(self, lm: list, pts: tuple) -> float:
        p1, p2, p3, p4, p5, p6 = [lm[i] for i in pts]
        a = np.linalg.norm([p2.x - p6.x, p2.y - p6.y, p2.z - p6.z])
        b = np.linalg.norm([p3.x - p5.x, p3.y - p5.y, p3.z - p5.z])
        c = np.linalg.norm([p1.x - p4.x, p1.y - p4.y, p1.z - p4.z])
        return (a + b) / (2.0 * c + 1e-6)

    def _eye_center(self, lm: list, indices: list) -> tuple:
        xs = [lm[i].x for i in indices]
        ys = [lm[i].y for i in indices]
        return (sum(xs) / len(xs), sum(ys) / len(ys))

    def _estimate_gaze(self, lm: list, left_iris, right_iris) -> tuple[float, float]:
        h, w = 1.0, 1.0
        if left_iris and right_iris:
            l_eye = self._eye_center(lm, self.LEFT_EYE)
            r_eye = self._eye_center(lm, self.RIGHT_EYE)
            gaze_x = (left_iris.x - l_eye[0]) + (right_iris.x - r_eye[0])
            gaze_y = (left_iris.y - l_eye[1]) + (right_iris.y - r_eye[1])
            return (gaze_x * 2.0, gaze_y * 2.0)
        return (0.0, 0.0)

    def _estimate_head_pose(self, lm: list) -> dict:
        img_pts = np.array([
            [lm[self.NOSE_TIP].x, lm[self.NOSE_TIP].y],
            [lm[self.CHIN].x, lm[self.CHIN].y],
            [lm[self.LEFT_EYE_OUTER].x, lm[self.LEFT_EYE_OUTER].y],
            [lm[self.RIGHT_EYE_OUTER].x, lm[self.RIGHT_EYE_OUTER].y],
            [lm[self.MOUTH_LEFT].x, lm[self.MOUTH_LEFT].y],
            [lm[self.MOUTH_RIGHT].x, lm[self.MOUTH_RIGHT].y],
        ], dtype=np.float32)

        model_pts = np.array([
            (0.0, 0.0, 0.0),
            (0.0, -330.0, -65.0),
            (-225.0, 170.0, -135.0),
            (225.0, 170.0, -135.0),
            (-150.0, -150.0, -125.0),
            (150.0, -150.0, -125.0),
        ], dtype=np.float32)

        focal_length = 1.0
        center = (0.5, 0.5)
        camera = np.array([
            [focal_length, 0, center[0]],
            [0, focal_length, center[1]],
            [0, 0, 1]
        ], dtype=np.float32)
        dist = np.zeros((4, 1), dtype=np.float32)

        success, rvec, tvec = cv2.solvePnP(model_pts, img_pts, camera, dist)
        if success:
            rmat, _ = cv2.Rodrigues(rvec)
            angles = cv2.RQDecomp3x3(rmat)[0]
            return {
                "pitch": float(angles[0]),
                "yaw": float(angles[1]),
                "roll": float(angles[2]),
            }
        return {"pitch": 0.0, "yaw": 0.0, "roll": 0.0}

    def draw(self, frame: np.ndarray, face_data: Optional[FaceData]):
        if face_data is None:
            return
        h, w = frame.shape[:2]
        for i, lm in enumerate(face_data.landmarks[:75]):
            x, y = int(lm.x * w), int(lm.y * h)
            cv2.circle(frame, (x, y), 2, (0, 255, 0), -1)
        hp = face_data.head_pose
        cv2.putText(frame, f"Pose: p={hp['pitch']:.0f} y={hp['yaw']:.0f} r={hp['roll']:.0f}",
                    (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 2)
        le = face_data.left_eye
        re = face_data.right_eye
        cv2.putText(frame, f"L-EAR: {le['aspect_ratio']:.2f} {'OPEN' if le['open'] else 'CLOSED'}",
                    (10, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 2)
        cv2.putText(frame, f"R-EAR: {re['aspect_ratio']:.2f} {'OPEN' if re['open'] else 'CLOSED'}",
                    (10, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 2)
        gx, gy = face_data.gaze
        cv2.putText(frame, f"Gaze: ({gx:.2f}, {gy:.2f})",
                    (10, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 2)

    def close(self):
        self._landmarker.close()
