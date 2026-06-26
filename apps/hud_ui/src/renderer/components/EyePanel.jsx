import React from 'react';

export default function EyePanel({ blink, gaze, head }) {
  if (!blink && !gaze && !head) return null;
  return (
    <div className="eye-panel">
      {blink && <div>{blink.replace(/_/g, ' ')}</div>}
      {gaze && <div>gaze: {gaze}</div>}
      {head && <div>head: {head}</div>}
    </div>
  );
}
