type MessageHandler = (data: unknown) => void;

export class AlertWebSocket {
  private ws: WebSocket | null = null;
  private token: string;
  private handlers: MessageHandler[] = [];
  private reconnectDelay = 1000;
  private maxDelay = 30000;
  private shouldReconnect = true;

  constructor(token: string) {
    // Keep the JWT in memory only. It is exchanged for a short-lived, single-use
    // ticket right before connecting, so the long-lived token never appears in
    // the WebSocket URL (which lands in proxy/access logs and history).
    this.token = token;
  }

  private async fetchTicket(): Promise<string | null> {
    try {
      const resp = await fetch('/ws/ticket', {
        method: 'POST',
        headers: { Authorization: `Bearer ${this.token}` },
      });
      if (!resp.ok) return null;
      const data = await resp.json();
      return (data?.ticket as string) ?? null;
    } catch {
      return null;
    }
  }

  private scheduleReconnect() {
    if (!this.shouldReconnect) return;
    setTimeout(() => { void this.connect(); }, this.reconnectDelay);
    this.reconnectDelay = Math.min(this.reconnectDelay * 2, this.maxDelay);
  }

  async connect() {
    this.shouldReconnect = true;

    const ticket = await this.fetchTicket();
    if (!ticket) {
      this.scheduleReconnect();
      return;
    }

    const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const url = `${proto}//${window.location.host}/ws/alerts?ticket=${ticket}`;
    this.ws = new WebSocket(url);

    this.ws.onopen = () => {
      this.reconnectDelay = 1000;
    };

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        this.handlers.forEach((h) => h(data));
      } catch { /* ignore non-JSON */ }
    };

    this.ws.onclose = () => {
      this.scheduleReconnect();
    };

    this.ws.onerror = () => {
      this.ws?.close();
    };
  }

  onMessage(handler: MessageHandler) {
    this.handlers.push(handler);
  }

  disconnect() {
    this.shouldReconnect = false;
    this.ws?.close();
    this.ws = null;
    this.handlers = [];
  }
}
