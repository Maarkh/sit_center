import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';
import ErrorBoundary from './components/Common/ErrorBoundary';
import { registerServiceWorker } from './sw-register';

// Global unhandled error handler
window.addEventListener('unhandledrejection', (event) => {
  console.error('[Unhandled Promise]', event.reason);
});

registerServiceWorker();

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </StrictMode>,
);
