import { useEffect, useRef } from 'react';

// Periodically invoke `callback` so list/dashboard views pick up new alerts and
// incidents without a manual refresh. Skips ticks while the tab is hidden, and
// fires once immediately when the tab becomes visible again.
export function usePolling(callback: () => void, intervalMs = 15000) {
  const saved = useRef(callback);
  useEffect(() => { saved.current = callback; }, [callback]);

  useEffect(() => {
    const tick = () => { if (!document.hidden) saved.current(); };
    const id = window.setInterval(tick, intervalMs);
    const onVisible = () => { if (!document.hidden) saved.current(); };
    document.addEventListener('visibilitychange', onVisible);
    return () => {
      window.clearInterval(id);
      document.removeEventListener('visibilitychange', onVisible);
    };
  }, [intervalMs]);
}
