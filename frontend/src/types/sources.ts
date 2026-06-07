export type SourceType = 'host_agent' | 'http_pull' | 'kafka' | 'http_push';

export interface DataSource {
  id: string;
  name: string;
  type: SourceType;
  config: Record<string, unknown>;
  enabled: boolean;
}

export interface SourceCreate {
  name: string;
  type: SourceType;
  config: Record<string, unknown>;
  enabled: boolean;
}

export interface SourceTestResult {
  ok: boolean;
  sample?: Record<string, unknown>;
  error?: string;
}
