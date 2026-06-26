"""Test fixtures: synthetic hand landmarks and feature builders."""
import sys
sys.path.insert(0, '.')

import numpy as np
import pytest

from shared.types import (
    Landmark, HandData, HandFeatures, FingerData, FingerState,
)


# ---------------------------------------------------------------------------
# Landmark helpers — MediaPipe 21-landmark format
# ---------------------------------------------------------------------------
# Indices: 0=wrist, 1-4=thumb(CMC,MCP,IP,TIP), 5-8=index(MCP,PIP,DIP,TIP),
# 9-12=middle, 13-16=ring, 17-20=pinky

def make_landmarks(coords_21: list) -> list[Landmark]:
    """coords_21: list of (x, y, z) tuples for 21 landmarks."""
    return [Landmark(x=c[0], y=c[1], z=c[2]) for c in coords_21]


def make_open_palm_landmarks() -> list[Landmark]:
    """Synthetic open-palm landmarks (all fingers extended and spread)."""
    return make_landmarks([
        (0.50, 0.80, 0.00),  # 0 wrist
        (0.48, 0.70, 0.01),  # 1 thumb CMC
        (0.45, 0.62, 0.02),  # 2 thumb MCP
        (0.43, 0.55, 0.03),  # 3 thumb IP
        (0.42, 0.48, 0.04),  # 4 thumb TIP
        (0.52, 0.68, 0.00),  # 5 index MCP
        (0.53, 0.58, 0.01),  # 6 index PIP
        (0.54, 0.48, 0.02),  # 7 index DIP
        (0.55, 0.40, 0.03),  # 8 index TIP
        (0.57, 0.66, 0.01),  # 9 middle MCP
        (0.59, 0.55, 0.02),  # 10 middle PIP
        (0.60, 0.45, 0.03),  # 11 middle DIP
        (0.61, 0.37, 0.04),  # 12 middle TIP
        (0.62, 0.65, 0.02),  # 13 ring MCP
        (0.65, 0.54, 0.03),  # 14 ring PIP
        (0.67, 0.44, 0.04),  # 15 ring DIP
        (0.68, 0.36, 0.05),  # 16 ring TIP
        (0.67, 0.64, 0.03),  # 17 pinky MCP
        (0.71, 0.54, 0.04),  # 18 pinky PIP
        (0.73, 0.46, 0.05),  # 19 pinky DIP
        (0.74, 0.39, 0.06),  # 20 pinky TIP
    ])


def make_closed_fist_landmarks() -> list[Landmark]:
    """Fingers curled into palm, TIP at MCP position for curl ~0 (FOLDED)."""
    return make_landmarks([
        (0.50, 0.80, 0.00),
        (0.48, 0.76, 0.01),
        (0.46, 0.72, 0.02),
        (0.45, 0.70, 0.02),
        (0.44, 0.69, 0.02),  # 4 thumb TIP
        (0.53, 0.75, 0.00),  # 5 index MCP
        (0.54, 0.73, 0.01),  # 6 PIP
        (0.53, 0.75, 0.00),  # 7 DIP = MCP
        (0.53, 0.75, 0.00),  # 8 TIP = MCP → curl=0 → FOLDED
        (0.56, 0.74, 0.01),  # 9 middle MCP
        (0.57, 0.72, 0.01),  # 10 PIP
        (0.56, 0.74, 0.01),  # 11 DIP = MCP
        (0.56, 0.74, 0.01),  # 12 TIP = MCP → FOLDED
        (0.59, 0.73, 0.02),  # 13 ring MCP
        (0.60, 0.71, 0.02),  # 14 PIP
        (0.59, 0.73, 0.02),  # 15 DIP = MCP
        (0.59, 0.73, 0.02),  # 16 TIP = MCP → FOLDED
        (0.62, 0.72, 0.03),  # 17 pinky MCP
        (0.63, 0.70, 0.03),  # 18 PIP
        (0.62, 0.72, 0.03),  # 19 DIP = MCP
        (0.62, 0.72, 0.03),  # 20 TIP = MCP → FOLDED
    ])


def make_point_landmarks() -> list[Landmark]:
    """Index extended (TIP far from MCP), others folded (TIP = MCP)."""
    idx_mcp = (0.54, 0.70, 0.00)
    return make_landmarks([
        (0.50, 0.80, 0.00),
        (0.49, 0.73, 0.01),
        (0.48, 0.67, 0.02),
        (0.47, 0.61, 0.03),
        (0.46, 0.55, 0.04),
        idx_mcp,                  # 5 index MCP
        (0.56, 0.60, 0.01),      # 6 PIP
        (0.58, 0.46, 0.02),      # 7 DIP
        (0.60, 0.33, 0.03),      # 8 index TIP far from MCP → EXTENDED
        (0.57, 0.69, 0.01),      # 9 middle MCP
        (0.57, 0.67, 0.01),
        (0.57, 0.69, 0.01),      # 11 DIP = MCP
        (0.57, 0.69, 0.01),      # 12 TIP = MCP → FOLDED
        (0.60, 0.68, 0.02),      # 13 ring MCP
        (0.60, 0.66, 0.02),
        (0.60, 0.68, 0.02),      # 15 DIP = MCP
        (0.60, 0.68, 0.02),      # 16 TIP = MCP → FOLDED
        (0.63, 0.67, 0.03),      # 17 pinky MCP
        (0.63, 0.65, 0.03),
        (0.63, 0.67, 0.03),      # 19 DIP = MCP
        (0.63, 0.67, 0.03),      # 20 TIP = MCP → FOLDED
    ])


def make_peace_landmarks() -> list[Landmark]:
    """Index + middle extended (V-sign), ring + pinky folded."""
    return make_landmarks([
        (0.50, 0.80, 0.00),
        (0.49, 0.72, 0.01),
        (0.48, 0.65, 0.02),
        (0.47, 0.58, 0.03),
        (0.46, 0.52, 0.04),
        (0.54, 0.69, 0.00),  # 5 index MCP
        (0.56, 0.58, 0.01),
        (0.58, 0.45, 0.02),
        (0.60, 0.32, 0.03),  # 8 index TIP → EXTENDED
        (0.57, 0.68, 0.01),  # 9 middle MCP
        (0.59, 0.57, 0.02),
        (0.61, 0.44, 0.03),
        (0.63, 0.31, 0.04),  # 12 middle TIP → EXTENDED
        (0.60, 0.67, 0.02),  # 13 ring MCP
        (0.60, 0.65, 0.02),
        (0.59, 0.64, 0.02),
        (0.59, 0.63, 0.02),  # 16 ring TIP → FOLDED
        (0.63, 0.66, 0.03),  # 17 pinky MCP
        (0.63, 0.64, 0.03),
        (0.62, 0.63, 0.03),
        (0.62, 0.62, 0.03),  # 20 pinky TIP → FOLDED
    ])


def make_pinch_landmarks() -> list[Landmark]:
    """Thumb tip touching index tip, other fingers extended."""
    return make_landmarks([
        (0.50, 0.80, 0.00),
        (0.48, 0.73, 0.01),
        (0.47, 0.68, 0.02),
        (0.48, 0.62, 0.04),
        (0.49, 0.60, 0.06),
        (0.54, 0.72, 0.00),
        (0.53, 0.66, 0.02),
        (0.52, 0.63, 0.04),
        (0.50, 0.60, 0.06),
        (0.57, 0.70, 0.01),
        (0.60, 0.60, 0.02),
        (0.62, 0.50, 0.03),
        (0.64, 0.40, 0.04),
        (0.62, 0.69, 0.02),
        (0.65, 0.59, 0.03),
        (0.67, 0.49, 0.04),
        (0.69, 0.39, 0.05),
        (0.66, 0.68, 0.03),
        (0.69, 0.58, 0.04),
        (0.71, 0.48, 0.05),
        (0.73, 0.38, 0.06),
    ])


def make_thumbs_up_landmarks() -> list[Landmark]:
    """Thumb extended upward, other fingers folded (TIP = MCP for curl=0)."""
    return make_landmarks([
        (0.50, 0.80, 0.00),
        (0.48, 0.72, -0.02),
        (0.46, 0.64, -0.03),
        (0.44, 0.55, -0.04),
        (0.42, 0.46, -0.05),  # 4 thumb TIP far from MCP → EXTENDED
        (0.54, 0.74, 0.00),  # 5 index MCP
        (0.54, 0.72, 0.01),
        (0.54, 0.74, 0.00),  # 7 DIP = MCP
        (0.54, 0.74, 0.00),  # 8 TIP = MCP → FOLDED
        (0.57, 0.73, 0.01),  # 9 middle MCP
        (0.57, 0.71, 0.01),
        (0.57, 0.73, 0.01),  # 11 DIP = MCP
        (0.57, 0.73, 0.01),  # 12 TIP = MCP → FOLDED
        (0.60, 0.72, 0.02),  # 13 ring MCP
        (0.60, 0.70, 0.02),
        (0.60, 0.72, 0.02),  # 15 DIP = MCP
        (0.60, 0.72, 0.02),  # 16 TIP = MCP → FOLDED
        (0.63, 0.71, 0.03),  # 17 pinky MCP
        (0.63, 0.69, 0.03),
        (0.63, 0.71, 0.03),  # 19 DIP = MCP
        (0.63, 0.71, 0.03),  # 20 TIP = MCP → FOLDED
    ])


# ---------------------------------------------------------------------------
# HandFeatures builders
# ---------------------------------------------------------------------------

def make_finger_state(name: str, state: str, curl: float = 1.0,
                      angle: float = 0.5) -> FingerData:
    return FingerData(
        name=name,
        state=FingerState[state],
        curl_ratio=curl,
        angle_to_palm=angle,
        spread_angle=angle,
    )


def make_features(
    fingers: dict[str, str],
    thumb_index_dist: float = 0.2,
    thumb_middle_dist: float = 0.2,
    index_middle_dist: float = 0.1,
    speed: float = 0.0,
    palm_center: tuple = (0.5, 0.5),
    palm_width: float = 0.1,
    direction: str = "none",
) -> HandFeatures:
    """Build HandFeatures from a dict of finger_name -> state."""
    fd = [make_finger_state(name, state) for name, state in fingers.items()]
    return HandFeatures(
        fingers=fd,
        thumb_index_dist=thumb_index_dist,
        thumb_middle_dist=thumb_middle_dist,
        index_middle_dist=index_middle_dist,
        speed=speed,
        palm_center=palm_center,
        palm_width=palm_width,
        direction=direction,
    )


def make_fd(handedness: str = "Right", landmarks: list = None,
            palm_center: tuple = (0.5, 0.5), palm_width: float = 0.1
            ) -> HandData:
    return HandData(
        landmarks=landmarks or make_open_palm_landmarks(),
        handedness=handedness,
        palm_center=palm_center,
        palm_width=palm_width,
    )
