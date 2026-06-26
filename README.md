# Apex Control

**A multimodal computer operating layer** — control your computer through natural gestures, voice commands, gaze, and AI-driven context awareness.

> Eliminate keyboard and mouse for common actions.

**Branch:** `main` · **Architecture:** event-driven monorepo

---

## Architecture

```
Camera ──→ Vision Service ──→ Event Bus ──→ Gesture Service ──→ Event Bus ──→ Action Service ──→ OS
Microphone ──→ Voice Service ──┘                │                               │
                                       Context Service ←── (polls active window)  │
                                              │                                  │
                                       Workspace Service                    Mouse/Keyboard/Volume
                                              │
                                       AI Service (planned)
```

All services communicate through an **Event Bus** (pub/sub). No direct module coupling.

---

## Project Structure

```
├── shared/                    # Shared library (imported by all services)
│   ├── events/               # Event Bus, schemas, topic registry
│   ├── types/                # Landmark, HandData, HandFeatures, FingerData
│   └── utils/                # Structured logging
├── services/                 # Independent services
│   ├── vision_service/       # Camera capture, MediaPipe hand tracking
│   ├── gesture_service/      # Feature extraction, formal gesture definitions, state machine
│   ├── action_service/       # Mouse, keyboard, volume control
│   ├── context_service/      # Active window detection, activity inference
│   ├── eye_service/          # (planned) Iris tracking, blink detection
│   ├── voice_service/        # (planned) STT via Whisper/Vosk
│   ├── workspace_service/    # (planned) Study/Coding/Meeting mode launcher
│   └── ai_service/           # (planned) LangGraph agent layer
├── apps/                     # Application entry points
│   ├── desktop_client/       # Main desktop app (this is what you run)
│   ├── hud_ui/               # (planned) React/Three.js HUD overlay
│   └── control_center/       # (planned) Settings and configuration UI
├── config/                   # YAML configuration files
├── docs/                     # Documentation
├── storage/                  # Runtime data (logs, settings, memory)
└── models/                   # Downloaded ML models (.task files)
```

---

## Gesture Library (20+ gestures)

| Category  | Gestures |
|-----------|----------|
| **Static** | Open Palm, Closed Fist, Pinch, Two Finger Pinch, Point, Peace, Three Fingers, OK Sign, Rock Sign, Thumbs Up |
| **Dynamic** | Swipe Left/Right/Up/Down, Rotate CW/CCW, Wave, Double Pinch |

Formal definitions in `services/gesture_service/gesture_definitions.py` with mathematical conditions for each gesture (finger states, angles, distances, velocity thresholds).

---

## Gesture Recognition Pipeline

```
Camera Frame
    ↓
MediaPipe Hand Landmarker → 21 landmarks per hand
    ↓
Feature Extractor → finger states, curl ratios, angles, distances, palm orientation, velocity
    ↓
Gesture Classifier → matches features against formal gesture definitions
    ↓
Gesture State Machine → per-gesture FSM: IDLE → CANDIDATE → ACTIVE → COOLDOWN
    ↓
Event Bus → gesture.event (PRESS/HOLD/RELEASE/TAP)
    ↓
Action Service → executes OS actions
```

---

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Download hand model (automatically placed in models/)
python -c "import urllib.request; urllib.request.urlretrieve('https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task', 'models/hand_landmarker.task')"

# Run
python -m apps.desktop_client.main
```

Press **ESC** to exit. Debug overlay shows landmarks + detected gestures + cursor mode.

---

## Roadmap

| Stage | What |
|-------|------|
| ✅ V1 | Hand gesture controller (complete, running) |
| 🚧 V1.5 | Voice layer (STT + intent parsing) |
| ⏳ V2 | Eye tracking (iris position, blink detection) |
| ⏳ V2.5 | Head tracking (look ↔ desktop navigation) |
| ⏳ V3 | Smart context layer (AI intent understanding) |
| ⏳ V4 | HUD interface (React/Electron/Three.js) |

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Vision | OpenCV, MediaPipe 0.10 (task API) |
| Gesture | Formal definition system, rule-based classifier |
| Actions | PyAutoGUI, keyboard, pycaw |
| Context | pygetwindow |
| Voice (planned) | Whisper, Vosk |
| AI (planned) | LangGraph, Ollama |
| HUD (planned) | React, Electron, Three.js |
| Event Bus | In-process pub/sub (swappable for Redis/NATS) |

---

## License

MIT
