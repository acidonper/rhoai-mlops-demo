{{- define "project01.labels" -}}
app.kubernetes.io/name: {{ .Chart.Name }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/part-of: create-kubernetes-object
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{- define "project01.validate" -}}
{{- $seen := dict -}}
{{- range .Values.buckets -}}
{{- $name := required "each bucket needs a name" .name -}}
{{- if not (regexMatch "^[a-z0-9]([-a-z0-9]*[a-z0-9])?$" $name) -}}
{{- fail (printf "bucket name %q must be a DNS-1123 label" $name) -}}
{{- end -}}
{{- if gt (len (printf "start-connection-%s" $name)) 63 -}}
{{- fail (printf "bucket name %q is too long for a Job name" $name) -}}
{{- end -}}
{{- if hasKey $seen $name -}}
{{- fail (printf "duplicate bucket name %q" $name) -}}
{{- end -}}
{{- $_ := set $seen $name true -}}
{{- end -}}
{{- end -}}
