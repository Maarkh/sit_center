{{/*
Common labels
*/}}
{{- define "sit-center.labels" -}}
app.kubernetes.io/name: sit-center
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "sit-center.selectorLabels" -}}
app.kubernetes.io/name: sit-center
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Common environment variables for all pods
*/}}
{{- define "sit-center.env" -}}
- name: DATABASE_URL
  value: "postgresql://{{ .Values.postgresql.user }}:$(POSTGRES_PASSWORD)@{{ .Values.postgresql.host }}:{{ .Values.postgresql.port }}/{{ .Values.postgresql.database }}"
- name: POSTGRES_USER
  value: {{ .Values.postgresql.user | quote }}
- name: POSTGRES_PASSWORD
  valueFrom:
    secretKeyRef:
      name: {{ .Values.existingSecret }}
      key: POSTGRES_PASSWORD
- name: POSTGRES_SERVER
  value: {{ .Values.postgresql.host | quote }}
- name: POSTGRES_PORT
  value: {{ .Values.postgresql.port | quote }}
- name: POSTGRES_DB
  value: {{ .Values.postgresql.database | quote }}
- name: REDIS_HOST
  value: {{ .Values.redis.host | quote }}
- name: REDIS_PORT
  value: {{ .Values.redis.port | quote }}
- name: REDIS_PASSWORD
  valueFrom:
    secretKeyRef:
      name: {{ .Values.existingSecret }}
      key: REDIS_PASSWORD
- name: SECRET_KEY
  valueFrom:
    secretKeyRef:
      name: {{ .Values.existingSecret }}
      key: SECRET_KEY
- name: ADMIN_USERNAME
  value: "admin"
- name: ADMIN_PASSWORD
  valueFrom:
    secretKeyRef:
      name: {{ .Values.existingSecret }}
      key: ADMIN_PASSWORD
- name: WEBHOOK_API_KEY
  valueFrom:
    secretKeyRef:
      name: {{ .Values.existingSecret }}
      key: WEBHOOK_API_KEY
- name: I_DOIT_API_KEY
  valueFrom:
    secretKeyRef:
      name: {{ .Values.existingSecret }}
      key: I_DOIT_API_KEY
- name: I_DOIT_API_URL
  valueFrom:
    secretKeyRef:
      name: {{ .Values.existingSecret }}
      key: I_DOIT_API_URL
      optional: true
- name: KAFKA_ENABLED
  value: {{ .Values.kafka.enabled | quote }}
{{- if .Values.kafka.enabled }}
- name: KAFKA_BOOTSTRAP_SERVERS
  value: {{ .Values.kafka.bootstrapServers | quote }}
{{- end }}
- name: CLICKHOUSE_ENABLED
  value: {{ .Values.clickhouse.enabled | quote }}
{{- if .Values.clickhouse.enabled }}
- name: CLICKHOUSE_HOST
  value: {{ .Values.clickhouse.host | quote }}
- name: CLICKHOUSE_PORT
  value: {{ .Values.clickhouse.port | quote }}
{{- end }}
- name: LDAP_ENABLED
  value: {{ .Values.ldap.enabled | quote }}
- name: OIDC_ENABLED
  value: {{ .Values.oidc.enabled | quote }}
# Point matplotlib's config/cache at the writable /tmp emptyDir so it never tries
# to write the font cache under a read-only root filesystem (readOnlyRootFilesystem).
- name: MPLCONFIGDIR
  value: /tmp/matplotlib
{{- end }}

{{/*
Writable scratch for a read-only root filesystem: /tmp (libs, matplotlib cache,
joblib) and /app/logs (RotatingFileHandler; it already degrades to stdout if
absent, but the emptyDir keeps file logs working). Mounted by every workload.
*/}}
{{- define "sit-center.writableVolumeMounts" -}}
- name: tmp
  mountPath: /tmp
- name: logs
  mountPath: /app/logs
{{- end }}

{{- define "sit-center.writableVolumes" -}}
- name: tmp
  emptyDir: {}
- name: logs
  emptyDir: {}
{{- end }}
