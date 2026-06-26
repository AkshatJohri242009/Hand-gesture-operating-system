import { useEffect, useRef, useCallback } from 'react';

const WS_URL = 'ws://127.0.0.1:8765';

export function useWebSocket(onEvent) {
  const ws = useRef(null);
  const cb = useRef(onEvent);
  cb.current = onEvent;

  useEffect(() => {
    let reconnectTimer;
    let running = true;

    function connect() {
      if (!running) return;
      try {
        const sock = new WebSocket(WS_URL);
        ws.current = sock;

        sock.onopen = () => console.log('HUD connected');

        sock.onmessage = (msg) => {
          try {
            const data = JSON.parse(msg.data);
            cb.current(data);
          } catch {}
        };

        sock.onclose = () => {
          ws.current = null;
          if (running) reconnectTimer = setTimeout(connect, 2000);
        };

        sock.onerror = () => sock.close();
      } catch {
        if (running) reconnectTimer = setTimeout(connect, 2000);
      }
    }

    connect();

    return () => {
      running = false;
      clearTimeout(reconnectTimer);
      if (ws.current) ws.current.close();
    };
  }, []);

  return ws;
}
