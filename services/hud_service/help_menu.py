import cv2
import numpy as np

GESTURES = [
    ("Gesture", "Action", "Confidence"),
    ("open_palm", "Toggles cursor mode ON", "≥80%"),
    ("closed_fist", "Drag (hold) / drop (release)", "≥80%"),
    ("pinch", "Left click (tap)", "≥85%"),
    ("two_finger_pinch", "Right click", "≥80%"),
    ("point", "Cursor movement mode", "≥80%"),
    ("peace", "Double click", "≥75%"),
    ("three_fingers", "Volume up (context)", "≥75%"),
    ("ok_sign", "Volume down (context)", "≥70%"),
    ("rock_sign", "Mute toggle", "≥70%"),
    ("thumbs_up", "Confirm / Enter", "≥75%"),
    ("swipe_left", "Previous desktop / tab", "≥70%"),
    ("swipe_right", "Next desktop / tab", "≥70%"),
    ("swipe_up", "Task view / overview", "≥70%"),
    ("swipe_down", "Show desktop", "≥70%"),
    ("rotate_clockwise", "Zoom in / rotate CW", "≥70%"),
    ("rotate_counterclockwise", "Zoom out / rotate CCW", "≥70%"),
]

EYE_COMMANDS = [
    ("Blink Type", "Action"),
    ("Single blink", "Left click"),
    ("Double blink", "Double click"),
    ("Long blink (hold)", "Right click"),
    ("Look left", "Previous virtual desktop"),
    ("Look right", "Next virtual desktop"),
    ("Look up", "Task view"),
    ("Look down", "Show desktop"),
]

VOICE_COMMANDS = [
    ("Command", "Action"),
    ('"open [app]"', "Launch app (chrome, spotify, code…)"),
    ('"volume up/down"', "Adjust system volume"),
    ('"volume N%"', "Set volume to N percent"),
    ('"mute" / "screenshot"', "Toggle mute / capture screen"),
    ('"lock computer"', "Lock workstation"),
    ('"play/pause/next song"', "Media control"),
    ('"study/work/focus mode"', "Switch workspace"),
    ('"hey apex [anything]"', "AI agent handles the request"),
    ('"apex [anything]"', "AI agent (short form)"),
]

WORKSPACES = [
    ("Mode", "Opens", "Layout"),
    ("study", "Chrome + OneNote + Spotify", "Side by side"),
    ("work", "Chrome + Code + Slack + Spotify", "Grid"),
    ("focus", "Code editor (maximized)", "Maximize"),
    ("meeting", "Chrome + Teams", "Side by side"),
    ("research", "Chrome + Zotero + OneNote", "Grid"),
    ("gaming", "Closes background apps", "None"),
]

KEYS = [
    ("Key", "Function"),
    ("ESC", "Exit Apex Control"),
    ("H", "Toggle this help menu"),
    ("C", "Switch to next camera"),
    ("D", "Toggle debug overlay"),
]


def _col(text, width):
    s = str(text)
    return s.ljust(width)[:width]


def _sep(w1, w2, w3=0, w4=0):
    return "-" * w1 + " + " + "-" * w2 + (" + " + "-" * w3 if w3 else "") + (" + " + "-" * w4 if w4 else "")


def _draw_table(frame, x, y, rows, col_widths, title, color=(0, 255, 255)):
    h, w = frame.shape[:2]
    cw1, cw2, cw3, cw4 = (col_widths + [0, 0, 0])[:4]

    # Calculate box dimensions
    line_h = 16
    header_h = 24
    sep_h = 2
    total_h = header_h + sep_h + len(rows) * line_h + 8
    total_w = sum(col_widths) + 4 * len(col_widths) + 10

    # Clip to frame
    if y + total_h > h:
        y = h - total_h - 10
    if x + total_w > w:
        x = w - total_w - 10

    # Semi-transparent background
    overlay = frame.copy()
    cv2.rectangle(overlay, (x, y), (x + total_w, y + total_h), (20, 20, 30), -1)
    cv2.addWeighted(overlay, 0.85, frame, 0.15, 0, frame)

    # Title
    cv2.putText(frame, title, (x + 6, y + 18), cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 1)

    # Separator
    sep = _sep(cw1, cw2, cw3, cw4)
    cv2.putText(frame, sep, (x + 6, y + header_h + 6), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (100, 100, 100), 1)

    # Rows
    yy = y + header_h + sep_h + 4
    for i, row in enumerate(rows):
        c1, c2, c3, c4 = (list(row) + ["", "", ""])[:4]
        line = f"  {_col(c1, cw1)}  {_col(c2, cw2)}"
        if cw3:
            line += f"  {_col(c3, cw3)}"
        if cw4:
            line += f"  {_col(c4, cw4)}"
        clr = (180, 180, 180) if i == 0 else (220, 220, 220)
        cv2.putText(frame, line, (x + 6, yy + 12), cv2.FONT_HERSHEY_SIMPLEX, 0.4, clr, 1)
        yy += line_h


def draw_help(frame):
    """Draw the full help overlay on the frame."""
    h, w = frame.shape[:2]

    # Left column: Gestures + Eye
    _draw_table(frame, 20, 30, GESTURES, [16, 32, 10], "HAND GESTURES", (0, 255, 255))
    ges_bottom = 30 + 24 + 4 + len(GESTURES) * 16 + 8
    _draw_table(frame, 20, ges_bottom + 10, EYE_COMMANDS, [18, 30], "EYE / HEAD TRACKING", (100, 200, 255))

    # Right column: Voice + Workspaces + Keys
    rx = w // 2 + 10
    _draw_table(frame, rx, 30, VOICE_COMMANDS, [22, 42], "VOICE COMMANDS", (100, 255, 200))
    vc_bottom = 30 + 24 + 4 + len(VOICE_COMMANDS) * 16 + 8
    _draw_table(frame, rx, vc_bottom + 10, WORKSPACES, [12, 30, 16], "WORKSPACE MODES", (200, 200, 100))
    ws_bottom = vc_bottom + 10 + 24 + 4 + len(WORKSPACES) * 16 + 8
    _draw_table(frame, rx, ws_bottom + 10, KEYS, [16, 30], "KEYBOARD SHORTCUTS", (200, 150, 100))

    # Footer
    cv2.putText(frame, "Press H to close help", (w // 2 - 90, h - 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)

    return frame
