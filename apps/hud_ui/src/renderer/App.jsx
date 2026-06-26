import React, { useState, useCallback } from 'react';
import { useWebSocket } from './hooks/useWebSocket.js';
import HandView from './components/HandView.jsx';
import AmbientRing from './components/AmbientRing.jsx';
import GestureBadge from './components/GestureBadge.jsx';
import VoiceTranscript from './components/VoiceTranscript.jsx';
import StatusBar from './components/StatusBar.jsx';
import EyePanel from './components/EyePanel.jsx';

export default function App() {
  const [state, setState] = useState({
    hands: [],
    cursorMode: false,
    gesture: '',
    gestureConfidence: 0,
    voiceText: '',
    blinkType: '',
    gaze: '',
    headPose: '',
    appContext: 'default',
    workspace: '',
    activity: '',
  });

  const onEvent = useCallback((data) => {
    const { topic, payload } = data;
    setState((prev) => {
      const next = { ...prev };

      if (topic === 'vision.hand.landmarks') {
        next.hands = payload.hands || [];
      }
      if (topic === 'gesture.event') {
        next.gesture = payload.gesture || '';
        next.gestureConfidence = payload.confidence || 0;
      }
      if (topic === 'gesture.dynamic.detected') {
        next.gesture = `→ ${payload.gesture || ''}`;
        next.gestureConfidence = payload.confidence || 0;
      }
      if (topic === 'voice.transcription') {
        next.voiceText = payload.text || '';
      }
      if (topic === 'vision.eye.blink') {
        next.blinkType = payload.blink_type || '';
      }
      if (topic === 'vision.eye.gaze') {
        next.gaze = payload.direction || payload.label || '';
      }
      if (topic === 'vision.head.pose') {
        next.headPose = payload.direction || '';
      }
      if (topic === 'context.app.changed') {
        next.appContext = payload.app || 'default';
      }
      if (topic === 'workspace.active') {
        next.workspace = payload.mode || '';
      }
      if (topic === 'context.activity.inferred') {
        next.activity = payload.activity || '';
      }

      return next;
    });
  }, []);

  useWebSocket(onEvent);

  return (
    <div className="hud-container">
      <div className="hud-canvas">
        <AmbientRing active={state.gesture !== '' || state.voiceText !== ''} />
        {state.hands.length > 0 && <HandView hands={state.hands} />}
      </div>

      <GestureBadge gesture={state.gesture} confidence={state.gestureConfidence} />
      <VoiceTranscript text={state.voiceText} />
      <EyePanel blink={state.blinkType} gaze={state.gaze} head={state.headPose} />
      <StatusBar
        app={state.appContext}
        workspace={state.workspace}
        cursorMode={state.cursorMode}
        activity={state.activity}
        handCount={state.hands.length}
      />
    </div>
  );
}
