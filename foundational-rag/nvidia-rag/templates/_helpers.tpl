{{/*
Expand the name of the chart.
*/}}
{{- define "nvidia-rag.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "nvidia-rag.fullname" -}}
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
{{- define "nvidia-rag.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "nvidia-rag.labels" -}}
helm.sh/chart: {{ include "nvidia-rag.chart" . }}
{{ include "nvidia-rag.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "nvidia-rag.selectorLabels" -}}
app.kubernetes.io/name: {{ include "nvidia-rag.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
RAG Server name
*/}}
{{- define "nvidia-rag.ragServerName" -}}
{{- printf "%s-rag-server" (include "nvidia-rag.fullname" .) }}
{{- end }}

{{/*
RAG Playground name
*/}}
{{- define "nvidia-rag.ragPlaygroundName" -}}
{{- printf "%s-rag-playground" (include "nvidia-rag.fullname" .) }}
{{- end }}

{{/*
Canvas API name
*/}}
{{- define "nvidia-rag.canvasApiName" -}}
{{- printf "%s-canvas-api" (include "nvidia-rag.fullname" .) }}
{{- end }}

{{/*
Enterprise features helper
*/}}
{{- define "nvidia-rag.enterprise" -}}
{{- if .Values.global.enterprise.enabled }}true{{ else }}false{{ end }}
{{- end }}

{{/*
High Availability helper
*/}}
{{- define "nvidia-rag.highAvailability" -}}
{{- if and .Values.global.enterprise.enabled .Values.global.enterprise.highAvailability }}true{{ else }}false{{ end }}
{{- end }}

{{/*
Monitoring enabled helper
*/}}
{{- define "nvidia-rag.monitoringEnabled" -}}
{{- if and .Values.global.enterprise.enabled .Values.global.enterprise.monitoring.enabled }}true{{ else }}false{{ end }}
{{- end }}