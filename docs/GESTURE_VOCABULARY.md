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
- Gestures must be held for 3 consecutive frames before firing (CANDIDATE → ACTIVE transition)
- A 200ms cooldown period prevents the same gesture from firing multiple times
- The system uses exponential smoothing on landmark positions to reduce jitter
- Two-layer architecture: frame classifier → gesture state machine
- Dynamic gestures (swipe, rotate) use a sliding window of 6 frames for velocity/angle tracking
- Cursor only moves when Open Palm is in ACTIVE state
- Pinch-hold = drag; release = drop (gesture state machine handles this automatically)

### State Machine Details

```
States:  IDLE → CANDIDATE → ACTIVE → COOLDOWN → IDLE

IDLE       → CANDIDATE:  gesture detected with confidence ≥ threshold (1 frame)
CANDIDATE  → ACTIVE:     gesture stable for 3 consecutive frames
ACTIVE     → COOLDOWN:   gesture released (fires RELEASE event)
COOLDOWN   → IDLE:       wait 200ms before accepting new gestures
```

### Scroll Interactions

Scroll up / down can replace volume rotation when the active context is a scrollable window (browser, file explorer).

In V1, scroll is assigned to two-finger vertical drag (index and middle tips moving together up/down). This is activated after a pinch-hold on the scrollbar area.
