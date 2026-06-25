# V1 Build Plan — Gesture Controller

## Refined Architecture Decisions

### 1. Gesture Recognition: Rule-Based with State Machines

Frame-by-frame classification flickers. We solve this with a **two-layer system**:

```
Layer 1: Frame Classifier     ← classifies every frame independently
Layer 2: Gesture State Machine ← tracks state across frames, fires events
```

**State machine per gesture:**

```
IDLE ──(1 frame above threshold)──→ CANDIDATE
  ↑                                      │
  │                           (N frames stable)──→ ACTIVE ── fires gesture_event(PRESS)
  │                                      │
  │                         (gesture released)──→ COOLDOWN ── fires gesture_event(RELEASE)
  │                                      │
  └──────(cooldown expires)──────────────┘
```

This means:
- A **pinch** fires `PRESS` when held 3+ frames, fires `RELEASE` when released
- Cursor **drag** comes for free: pinch-hold + move = drag; release = drop
- No false positives from single-frame noise

### 2. Two Gesture Categories

| Type     | Examples                                    | Detection                                     |
| -------- | ------------------------------------------- | --------------------------------------------- |
| **Static** | Open Palm, Pinch, Fist, Thumbs Up          | Landmark distances + angles within a single frame |
| **Dynamic** | Swipe, Rotate, Double Pinch              | Motion tracking across a sliding window of frames |

Static gestures feed the state machine. Dynamic gestures fire once when detected.

### 3. Landmark Features (Scale-Invariant)

MediaPipe gives 21 landmarks per hand. We compute:

```
palm_width = distance(wrist, middle_MCP)

For each finger:
  curl_ratio = distance(TIP, MCP) / distance(PIP, MCP)
  # >0.8 = extended, <0.5 = curled

Thumb abduction = angle(thumb_TIP→thumb_MCP, index_MCP→wrist)
```

All thresholds are defined as ratios or angles — resolution-independent.

### 4. Cursor Control

- Only moves when `Open Palm` is ACTIVE (cursor mode)
- Exponential smoothing: `cursor = α × raw + (1-α) × prev`
- Hand position (0–1) mapped to screen resolution via PyAutoGUI
- Dead zone near center to prevent drift when hand is still

### 5. Dynamic Gesture Detection

**Swipe:** Track palm center (landmark 9) over last 6 frames. Compute displacement vector. If magnitude > threshold, classify direction by dominant axis (x or y).

**Rotate:** Compute angle of vector wrist→middle_MCP. Track cumulative angle change. Clockwise > 30° = rotate right event, < -30° = rotate left event.

**Double Pinch:** Two pinch PRESS events within 500ms window.

### 6. Context Awareness (V1)

- Use `pygetwindow` (Windows) to poll active window title every 1s
- Match title with regex patterns: Chrome, Spotify, Explorer, etc.
- Load gesture→action mappings from `config/gestures.yaml` per context

---

## Project Structure (Refined)

```
src/
├── main.py                     # Entry point, wires everything together
├── vision/
│   ├── __init__.py
│   ├── camera.py               # Camera capture wrapper
│   ├── hand_tracker.py         # MediaPipe Hands wrapper
│   └── gesture_recognizer.py   # Frame classification → gesture events
├── controllers/
│   ├── __init__.py
│   ├── mouse.py                # PyAutoGUI cursor, click, drag
│   ├── keyboard.py             # Pynput hotkeys
│   └── volume.py               # Pycaw system volume
├── core/
│   ├── __init__.py
│   ├── command_mapper.py       # Routes gesture events → controller actions
│   ├── context_manager.py      # Active window detection
│   ├── gesture_state.py        # State machine per gesture
│   └── gesture_dynamics.py     # Swipe and rotation detectors
└── utils/
    ├── __init__.py
    └── config.py               # YAML config loader
```

---

## Phase-by-Phase Build Order

### Phase 1 — Foundation Files (build in order)

| Order | File                   | What it does                                      |
|-------|------------------------|---------------------------------------------------|
| 1     | `utils/config.py`      | Load YAML configs with Pydantic validation         |
| 2     | `vision/camera.py`     | OpenCV webcam wrapper: start, stop, read, resize   |
| 3     | `vision/hand_tracker.py` | MediaPipe wrapper: returns 21 landmarks per hand |
| 4     | `vision/gesture_recognizer.py` | Classifies landmarks into gesture labels   |

**Milestone:** Running the pipeline with debug visualization showing landmarks + gesture label.

### Phase 2 — State Machine & Events

| Order | File                       | What it does                                      |
|-------|----------------------------|---------------------------------------------------|
| 5     | `core/gesture_state.py`    | Per-gesture state machine (IDLE→CANDIDATE→ACTIVE) |
| 6     | `core/gesture_dynamics.py` | Swipe + rotation detection from frame history      |

**Milestone:** Gesture events fire reliably without false positives.

### Phase 3 — Controllers

| Order | File                    | What it does                                      |
|-------|-------------------------|---------------------------------------------------|
| 7     | `controllers/mouse.py`  | Cursor move, click (left/right), drag, scroll     |
| 8     | `controllers/keyboard.py` | Hotkey combos (Ctrl+Tab, Ctrl+Shift+Tab, etc.)  |
| 9     | `controllers/volume.py` | System volume get/set via Pycaw                   |

### Phase 4 — Command Mapping & Context

| Order | File                       | What it does                                      |
|-------|----------------------------|---------------------------------------------------|
| 10    | `core/context_manager.py`  | Poll active window, determine context             |
| 11    | `core/command_mapper.py`   | Route gesture + context → controller action        |

### Phase 5 — Integration

| Order | File              | What it does                                      |
|-------|-------------------|---------------------------------------------------|
| 12    | `src/main.py`     | Wire all modules, main loop, graceful shutdown    |

**Milestone:** Full pipeline — webcam → gesture → cursor moves, clicks work, swipes switch tabs.

---

## Data Structures

### GestureEvent (passed between modules)

```python
@dataclass
class GestureEvent:
    gesture: str        # "pinch", "swipe_left", "open_palm", etc.
    state: str          # "PRESS" | "HOLD" | "RELEASE" | "TAP"
    hand: str           # "left" | "right"
    confidence: float
    position: tuple     # (x, y) normalized 0-1, for cursor
    timestamp: float
```

### DetectedGesture (output of gesture_recognizer per frame)

```python
@dataclass
class DetectedGesture:
    label: str
    confidence: float
    hand_landmarks: list   # original landmarks if needed downstream
```

---

## Key Algorithms

### Static Gesture Classification

```text
For each landmark set:
  palm_center = (landmark[0] + landmark[5] + landmark[9] + landmark[13] + landmark[17]) / 5
  palm_width = dist(landmark[0], landmark[9])

  For fingers index, middle, ring, pinky:
    curl = dist(TIP, MCP) / dist(PIP, MCP)

    extended_fingers += 1 if curl > 0.8
    curled_fingers += 1 if curl < 0.5

  thumb_tip = landmark[4]
  index_tip = landmark[8]
  middle_tip = landmark[12]
  thumb_index_dist = dist(thumb_tip, index_tip) / palm_width
  thumb_middle_dist = dist(thumb_tip, middle_tip) / palm_width

  Classify:
    if thumb_index_dist < 0.08 → "pinch"
    elif thumb_middle_dist < 0.08 → "two_finger_pinch"
    elif extended_fingers >= 4 and thumb spread > 30° → "open_palm"
    elif curled_fingers >= 4 and thumb curled → "closed_fist"
    elif curled_fingers >= 4 and thumb extended → "thumbs_up"
```

### Cursor Smoothing

```text
SMOOTHING_FACTOR = 0.3
dead_zone = 0.02

raw_x, raw_y = hand_landmark[9].x, hand_landmark[9].y  # palm center
smoothed_x = SMOOTHING_FACTOR * raw_x + (1 - SMOOTHING_FACTOR) * prev_x
smoothed_y = SMOOTHING_FACTOR * raw_y + (1 - SMOOTHING_FACTOR) * prev_y

# Dead zone — only move if displacement > dead_zone
if abs(smoothed_x - prev_x) > dead_zone or abs(smoothed_y - prev_y) > dead_zone:
    screen_x = int(smoothed_x * screen_width)
    screen_y = int(smoothed_y * screen_height)
    pyautogui.moveTo(screen_x, screen_y)
```

---

## Edge Cases & Failure Modes

| Problem                     | Mitigation                                          |
|-----------------------------|-----------------------------------------------------|
| No hand detected            | Keep cursor at last position; wait                  |
| Two hands in frame          | Let user configure dominant hand; pinch to select   |
| Low confidence              | Don't fire any gesture; log for calibration         |
| Hand leaves frame mid-gesture | Gesture state resets to IDLE; no phantom click   |
| Camera lag / dropped frames | Process every frame that arrives; skip if behind    |
| PyAutoGUI blocked (UAC)     | Log warning; don't crash; continue                  |
| Gesture cooldown            | 200ms cooldown after RELEASE prevents double-fire   |
| False swipe from hand jitter| Minimum displacement + velocity threshold           |

---

## Testing Strategy

| Test          | Method                                          |
|---------------|--------------------------------------------------|
| Unit tests    | Test each classifier with known landmark arrays  |
| Integration   | Record gesture sequences, verify fired events    |
| Manual        | Debug overlay showing landmarks + detected gesture |

Each gesture gets a unit test with pre-computed landmark positions:
- Pinch: two sets (pinched, not pinched) → verify classification
- Swipe: frame sequence with palm center motion → verify swipe event
- State machine: frame sequence with gaps → verify state transitions

---

## What's NOT in V1

- Voice control (V1.5)
- Eye tracking (V2)
- Head tracking (V2.5)
- AI context layer (V3)
- HUD interface (V4)
- Spotify API integration
- Application learning
- Macro recording

These are designed for but not implemented. The core pipeline (Event → Mapper → Controller) is built to accept events from any source.
