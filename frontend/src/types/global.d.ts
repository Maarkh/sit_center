declare global {
  interface Window {
    __SENTRY_DSN__?: string;
  }
}

export {};
