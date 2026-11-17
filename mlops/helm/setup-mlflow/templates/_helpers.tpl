{{- define "setup-mlflow.validate" -}}
{{- $name := required "mlflow.name is required" .Values.mlflow.name -}}
{{- $namespace := required "mlflow.namespace is required" .Values.mlflow.namespace -}}
{{- $dbSecret := required "mlflow.backendStore.secretName is required" .Values.mlflow.backendStore.secretName -}}
{{- $bucket := required "mlflow.artifactStore.bucket is required" .Values.mlflow.artifactStore.bucket -}}
{{- $s3Secret := required "mlflow.artifactStore.secretName is required" .Values.mlflow.artifactStore.secretName -}}
{{- $pgName := required "postgresql.name is required" .Values.postgresql.name -}}
{{- $pgUser := required "postgresql.user is required" .Values.postgresql.user -}}
{{- $pgPassword := required "postgresql.password is required" .Values.postgresql.password -}}
{{- $pgDatabase := required "postgresql.database is required" .Values.postgresql.database -}}
{{- $pgImage := required "postgresql.image is required" .Values.postgresql.image -}}
{{- $pgStorage := required "postgresql.storage is required" .Values.postgresql.storage -}}
{{- range $label := (list $name $namespace $dbSecret $bucket $s3Secret $pgName) -}}
{{- if or (gt (len $label) 63) (not (regexMatch "^[a-z0-9]([-a-z0-9]*[a-z0-9])?$" $label)) -}}
{{- fail (printf "%q must be a DNS-1123 label" $label) -}}
{{- end -}}
{{- end -}}
{{- if ne $name "mlflow" -}}
{{- fail "mlflow.name must be \"mlflow\"" -}}
{{- end -}}
{{- if lt (.Values.mlflow.replicas | int) 1 -}}
{{- fail "mlflow.replicas must be at least 1" -}}
{{- end -}}
{{- end -}}
