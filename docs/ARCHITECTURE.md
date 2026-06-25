# Architecture

## Overview

Apex Control is a layered pipeline system. Each layer is independent and communicates through standardized interfaces, allowing features to be added or removed without breaking the core.

## Pipeline

```
[Input Sources]          → [Processing]         → [Recognition]       → [Mapping]      → [Execution]
────────────────────────────────────────────────────────────────────────────────────────────────────

Webcam (OpenCV)          MediaPipe Hands         Gesture Classifier    Command Mapper    PyAutoGUI
Microphone (PyAudio)     Vosk / Whisper          Intent Detector       ───────────────→  Pynput
Camera (OpenCV)          MediaPipe Face Mesh     Blink / Gaze          Context Manager   Spotify API
                                                                    ↓
                                                              AI Agent (V3)
```

## Module Design

### 1. Vision Module (`src/vision/`)

- **hand_tracking.py** — MediaPipe Hands wrapper; returns hand landmarks
- **gesture_recognition.py** — Classifies landmark positions into gesture labels
- **face_mesh.py** — MediaPipe Face Mesh; iris position, head orientation

Each class follows this interface:

```python
class VisionModule:
    def process(self, frame: np.ndarray) -> dict:
        """Process a single frame. Returns structured data."""
        ...
```

### 2. Voice Module (`src/voice/`)

- **speech_to_text.py** — Pluggable backend (Vosk, Whisper, Google)
- **intent_detection.py** — Regex + keyword matching against `voice_commands.yaml`

### 3. Controllers (`src/controllers/`)

Stateless action executors:

- **mouse_controller.py** — Move, click, drag, scroll
- **keyboard_controller.py** — Hotkeys, shortcuts, text input
- **volume_controller.py** — System volume (Pycaw)
- **spotify_controller.py** — Spotify API (Spotipy)

### 4. Core (`src/core/`)

- **command_mapper.py** — Routes gesture labels → controller actions
- **context_manager.py** — Detects active window; remaps gestures per app
- **macro_engine.py** — Records and replays macro sequences
- **ai_context.py** — V3: LLM-driven intent resolution

## Data Flow

```
Camera Frame (30 FPS)
  │
  ▼
Hand Tracking ──→ Landmarks (21 points × x,y,z)
  │                  │
  ▼                  ▼
Face Mesh ───→ Iris Position + Head Euler Angles
  │
  ▼
Gesture Classifier ──→ Gesture Label + Confidence
                              │
Spoken Audio ──→ STT ──→ Text ──→ Intent
                              │
                              ▼
                    Context Manager
                      │  (checks active window,
                      │   user habits, saved macros)
                      ▼
               ┌──────┴──────┐
               │  Command    │
               │  Mapper     │
               └──────┬──────┘
                      ▼
            Controller Action
```

## Threading Model

```
Main Thread:        ┌─ Gesture Pipeline (30 FPS loop)
                    │
                    ├─ Voice Pipeline (async IO, runs on demand)
                    │
                    ├─ Eye Tracking (every 2nd frame)
                    │
                    └─ Context Monitor (every 1s, checks active window)
```

All pipelines write to a shared command queue. The command mapper reads from this queue sequentially, preventing race conditions.

## Configuration

All configuration is YAML-based in `config/`:

- `settings.yaml` — General app settings (camera, thresholds, logging)
- `gestures.yaml` — Gesture-to-action mapping + confidence thresholds
- `voice_commands.yaml` — Voice trigger → action mapping
