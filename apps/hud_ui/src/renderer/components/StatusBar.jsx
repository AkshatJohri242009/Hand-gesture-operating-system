import React from 'react';

export default function StatusBar({ app, workspace, cursorMode, activity, handCount }) {
  return (
    <div className="status-bar">
      <div className="status-item">
        <span className="dot cyan" />
        {handCount > 0 ? `${handCount} hand${handCount > 1 ? 's' : ''}` : 'no hands'}
      </div>

      <div className="status-divider" />

      <div className="status-item">
        <span className="dot green" />
        {app}
      </div>

      {workspace && (
        <>
          <div className="status-divider" />
          <div className="status-item">
            <span className="dot purple" />
            {workspace}
          </div>
        </>
      )}

      {activity && (
        <>
          <div className="status-divider" />
          <div className="status-item">
            <span className="dot orange" />
            {activity}
          </div>
        </>
      )}

      <div className="status-divider" />

      <div className="status-item">
        <span className={`dot ${cursorMode ? 'green' : 'yellow'}`} />
        cursor {cursorMode ? 'on' : 'off'}
      </div>
    </div>
  );
}
