{{- define "setup-mlflow.postgresHost" -}}
{{- printf "%s.%s.svc.cluster.local" .Values.postgresql.name .Values.mlflow.namespace -}}
{{- end -}}

{{- define "setup-mlflow.postgresUri" -}}
{{- printf "postgresql://%s:%s@%s:5432/%s" .Values.postgresql.user (.Values.postgresql.password | urlquery) (include "setup-mlflow.postgresHost" .) .Values.postgresql.database -}}
{{- end -}}
