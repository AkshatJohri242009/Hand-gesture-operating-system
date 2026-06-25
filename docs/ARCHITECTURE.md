# Architecture

## Overview

Apex Control is a layered pipeline system. Each layer is independent and communicates through standardized interfaces. See [`PLAN.md`](../PLAN.md) for the detailed V1 build plan and implementation order.

## V1 Pipeline (Gesture Controller)

```
Webcam Frame
     │
     ▼
Camera Module (OpenCV)
     │
     ▼
Hand Tracker (MediaPipe) ──→ 21 landmarks per hand
     │
     ├──▶ Static Gesture Classifier ──→ per-frame labels
     │         │
     │         ▼
     │    Gesture State Machine ──→ gesture events (PRESS/HOLD/RELEASE)
     │         │
     ├──▶ Dynamic Gesture Detector ──→ swipe/rotate events
     │
     └──▶ Cursor Position (palm center + smoothing)
              │
              ▼
       Gesture Event Queue
              │
       ┌──────┴──────┐
       │  Context     │ ← polls active window every 1s
       │  Manager     │
       └──────┬──────┘
              ▼
       Command Mapper
              │
       ┌──────┴──────┐
       │  Controllers  │
       │  (mouse,      │
       │   keyboard,    │
       │   volume)      │
       └───────────────┘
```

## Key Design Decisions

### Two-Layer Gesture Recognition

| Layer | Purpose | Output |
|-------|---------|--------|
| Frame Classifier | Classifies a single frame's landmarks | Gesture label + confidence |
| State Machine | Tracks gesture across N consecutive frames | Gesture event (PRESS/HOLD/RELEASE) |

This prevents flicker from single-frame false positives and gives us drag for free (pinch-hold + move = drag, release = drop).

### Gesture State Machine

```
IDLE ──(1 frame ≥ threshold)──→ CANDIDATE
  ↑                                       │
  │                           (3 frames stable)──→ ACTIVE ── fires PRESS event
  │                                       │
  │                         (gesture lost)──→ COOLDOWN ── fires RELEASE event
  │                                       │
  └────────(cooldown expires)─────────────┘
```

### Gesture Categories

| Type | Examples | Detection Method |
|------|----------|------------------|
| Static | Open Palm, Pinch, Fist, Thumbs Up | Landmark distance ratios + angles |
| Dynamic | Swipe, Rotate, Double Pinch | Position/angle tracking across frame window |

## Module Design (V1)

### 1. Vision Module (`src/vision/`)

- **camera.py** — OpenCV capture wrapper (start, stop, read, resize)
- **hand_tracker.py** — MediaPipe Hands wrapper; returns 21 landmarks per hand
- **gesture_recognizer.py** — Frame classifier + state machine + dynamic detectors

### 2. Controllers (`src/controllers/`)

- **mouse.py** — PyAutoGUI: move, click, drag, scroll
- **keyboard.py** — Pynput: hotkeys for tab switching, volume
- **volume.py** — Pycaw: system volume get/set

### 3. Core (`src/core/`)

- **command_mapper.py** — Routes gesture events → controller actions
- **context_manager.py** — Polls active window title for context-aware mappings
- **gesture_state.py** — Per-gesture state machine
- **gesture_dynamics.py** — Swipe and rotation detectors

### 4. Utils (`src/utils/`)

- **config.py** — YAML config loader with validation

## Data Flow (V1)

```
Camera (30 FPS) → Hand Tracker → Gesture Recognizer → Gesture Event
                                                           │
                                              ┌────────────┴────────────┐
                                              │  Command Mapper        │
                                              │  (reads active context)│
                                              └────────────┬────────────┘
                                                           ▼
                                                   Controller Action
```

## Future Layers (Post-V1)

All future input modalities (voice, eye tracking, head tracking) will inject events into the same `Gesture Event Queue`, keeping the core pipeline unchanged. See `PLAN.md` for the full roadmap.

## Configuration

All configuration is YAML-based in `config/`:

- `settings.yaml` — General app settings (camera, thresholds, logging)
- `gestures.yaml` — Gesture-to-action mapping + confidence thresholds
- `voice_commands.yaml` — Voice trigger → action mapping
