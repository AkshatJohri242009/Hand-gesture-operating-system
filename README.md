# Apex Control

**A multimodal computer operating layer** — control your computer through natural gestures, voice commands, gaze, and AI-driven context awareness.

> Eliminate keyboard and mouse for common actions.

---

## Demo

A 30-second video of controlling your desktop with hand movements is more compelling than most software projects. Record one early.

---

## Roadmap

### V1 — Gesture Controller (Current)

| Gesture              | Action       |
| -------------------- | ------------ |
| Open Palm            | Cursor Mode  |
| Pinch                | Left Click   |
| Two Finger Pinch     | Right Click  |
| Swipe Left / Right   | Tab Switch   |
| Rotate Wrist         | Volume       |
| Closed Fist          | Drag         |
| Double Pinch         | Play/Pause   |

**Stack:** Python, OpenCV, MediaPipe, PyAutoGUI

### V1.5 — Voice Layer

**Tools:** SpeechRecognition, Vosk (offline), OpenAI Whisper

Voice commands for app launching, media control, system actions, and volume.

### V2 — Eye Tracking

Iris position drives cursor. Blinks become clicks. Single blink → click, double → double click, long → right click.

### V2.5 — Head Tracking

Head orientation maps to desktop navigation. Look up → Task View, Look left → Previous Desktop, etc.

### V3 — Smart Context Layer

Say "I want to study" — system opens browser, notes, Spotify study playlist, and enables focus mode automatically.

### V4 — Tony Stark Interface

Floating HUD panels, radial menus, motion graphics, gesture-controlled UI built with Electron, Three.js, React, and Framer Motion.

---

## Architecture

```
Webcam ──┐
         ├── MediaPipe ──→ Gesture Recognition ──→ Command Mapper ──→ OS Actions
Microphone ──┐
             ├── STT Engine ──→ Intent Detection ──┘
Camera ──┐
         ├── Face Mesh ──→ Eye/Head Tracking ──────┘
                              │
                         Context Manager
                              │
                    ┌─────────┴─────────┐
                    │                   │
              App Awareness       AI Agent (V3)
                    │                   │
              Contextual Macros    Learning Layer
```

---

## Project Structure

```
├── src/
│   ├── vision/             # Computer Vision (hand tracking, face mesh, eye tracking)
│   ├── voice/              # Speech-to-text, intent detection
│   ├── controllers/        # Mouse, keyboard, volume, Spotify actions
│   ├── core/               # Command mapper, context manager, macro engine
│   └── main.py             # Application entry point
├── config/                 # YAML configuration files for gestures, voice, settings
├── docs/                   # Architecture & gesture vocabulary docs
├── tests/                  # Unit tests for each module
├── scripts/                # Setup and utility scripts
├── interface/              # V4 — React/Three.js HUD interface
└── requirements.txt        # Python dependencies
```

---

## Getting Started

```bash
# Clone the repository
git clone https://github.com/AkshatJohri24209/Hand-gesture-operating-system.git
cd Hand-gesture-operating-system

# Create virtual environment
python -m venv .venv
source .venv/bin/activate   # Linux/Mac
.venv\Scripts\activate      # Windows

# Install dependencies
pip install -r requirements.txt

# Run
python src/main.py
```

---

## Design Philosophy

- **Minimal gesture vocabulary** — ~10 gestures, not 50
- **Context-aware mappings** — gestures change meaning based on active application
- **Fail gracefully** — if confidence is low, don't execute
- **Privacy-first** — offline voice models by default (Vosk)
- **Extensible** — each module is independent; add or remove layers freely

---

## Tech Stack

| Layer              | Technology                          |
| ------------------ | ----------------------------------- |
| Computer Vision    | OpenCV, MediaPipe                   |
| Voice              | Whisper, Vosk, SpeechRecognition    |
| Desktop Control    | PyAutoGUI, Pynput, Pycaw            |
| AI/Agent           | LangGraph, LangChain, Local LLM     |
| HUD Interface (V4) | React, Electron, Three.js, Framer Motion |

---

## License

MIT
