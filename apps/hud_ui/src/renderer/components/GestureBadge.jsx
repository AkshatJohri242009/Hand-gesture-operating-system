import React from 'react';

export default function GestureBadge({ gesture, confidence }) {
  if (!gesture) return null;
  return (
    <div className="gesture-badge">
      {gesture.replace(/_/g, ' ')}
      {confidence > 0 && (
        <span style={{ marginLeft: 8, fontSize: 11, opacity: 0.5 }}>
          {(confidence * 100).toFixed(0)}%
        </span>
      )}
    </div>
  );
}
