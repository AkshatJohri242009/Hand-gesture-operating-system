# Gesture Vocabulary

Apex Control intentionally limits its gesture vocabulary to ~10 gestures. Fewer gestures means higher recognition accuracy and lower cognitive load for the user.

## Navigation Gestures

```
Swipe Left       ────  Previous Tab / Previous Song
Swipe Right      ────  Next Tab / Next Song
Swipe Up         ────  Task View / Mission Control
Swipe Down       ────  Show Desktop
```

All swipes are detected by tracking palm center velocity over a window of ~5 frames. A swipe requires a minimum displacement and velocity threshold to trigger.

## Selection Gestures

```
Open Palm        ────  Cursor Mode (track hand position as mouse)
Pinch            ────  Left Click
Two Finger Pinch ────  Right Click
Double Pinch     ────  Play / Pause
```

Pinch is detected by measuring distance between thumb tip and index/middle fingertips. When distance drops below a threshold for >3 consecutive frames, the pinch is registered.

## System Gestures

```
Rotate Clockwise        ────  Volume Up
Rotate Counterclockwise ────  Volume Down
Closed Fist             ────  Drag (hold to drag, release to drop)
Thumbs Up               ────  Confirm / Accept
```

Rotation is calculated using the angle of the wrist-to-middle-finger vector projected onto the image plane. Fist is detected when all fingertips are within a small radius of the palm center.

## Context-Aware Mappings

Gestures change meaning based on the active application:

| Gesture       | Chrome         | Spotify       | Explorer       |
| ------------- | -------------- | ------------- | -------------- |
| Swipe Right   | Next Tab       | Next Song     | Next Folder    |
| Swipe Left    | Previous Tab   | Previous Song | Previous Folder|
| Swipe Up      | New Tab        | Volume Up     | Parent Dir     |
| Swipe Down    | Close Tab      | Volume Down   | Open           |

## Implementation Notes

- All gestures require a minimum confidence score (configurable per gesture in `config/gestures.yaml`)
- Gestures must be held for 3–5 consecutive frames before firing to prevent false positives
- A cooldown period prevents the same gesture from firing multiple times
- The system uses exponential smoothing on landmark positions to reduce jitter
