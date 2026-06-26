import React from 'react';

export default function VoiceTranscript({ text }) {
  if (!text) return null;
  return <div className="voice-transcript">{text}</div>;
}
