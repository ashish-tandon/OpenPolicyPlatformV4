{{/*
Expand the name of the chart.
*/}}
{{- define "open-policy-platform.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "open-policy-platform.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "open-policy-platform.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "open-policy-platform.labels" -}}
helm.sh/chart: {{ include "open-policy-platform.chart" . }}
{{ include "open-policy-platform.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "open-policy-platform.selectorLabels" -}}
app.kubernetes.io/name: {{ include "open-policy-platform.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "open-policy-platform.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "open-policy-platform.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Database URL helper
*/}}
{{- define "open-policy-platform.databaseUrl" -}}
postgresql://{{ .Values.postgres.auth.username }}:{{ .Values.postgres.auth.password }}@{{ include "open-policy-platform.fullname" . }}-postgres:5432/{{ .Values.postgres.auth.database }}
{{- end }}

{{/*
Test Database URL helper
*/}}
{{- define "open-policy-platform.testDatabaseUrl" -}}
postgresql://{{ .Values.postgresTest.auth.username }}:{{ .Values.postgresTest.auth.password }}@{{ include "open-policy-platform.fullname" . }}-postgres-test:5432/{{ .Values.postgresTest.auth.database }}
{{- end }}

{{/*
Redis URL helper
*/}}
{{- define "open-policy-platform.redisUrl" -}}
redis://{{ include "open-policy-platform.fullname" . }}-redis:6379
{{- end }}

{{/*
Elasticsearch URL helper
*/}}
{{- define "open-policy-platform.elasticsearchUrl" -}}
http://{{ include "open-policy-platform.fullname" . }}-elasticsearch:9200
{{- end }}