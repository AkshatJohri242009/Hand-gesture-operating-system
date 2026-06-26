# Implementation Plan

See [README.md](./README.md) for architecture overview.

## Current Status

### Completed (V1 Core)

- [x] Formal gesture definition system with 20+ gestures
- [x] Feature extraction pipeline (finger states, distances, angles, velocity)
- [x] Gesture state machine (press/hold/release/tap events)
- [x] Event bus architecture (pub/sub)
- [x] Service-based monorepo structure
- [x] Mouse controller (move, click, drag, scroll)
- [x] Keyboard controller (hotkeys, shortcuts)
- [x] Volume controller (system volume via pycaw)
- [x] Context awareness (active window detection)
- [x] Camera service (MediaPipe 0.10 task API)

### In Progress

- [ ] Voice service (Whisper/Vosk integration)
- [ ] Eye tracking service (iris + blink)
- [ ] Head tracking service (orientation → desktop nav)

### Planned

- [ ] AI agent layer (LangGraph)
- [ ] Workspace engine
- [ ] HUD overlay (React/Three.js)
- [ ] Unit test suite
- [ ] Installation script
- [ ] Cross-platform support
