# setup-mlflow

Chart `setup-mlflow`. It installs a single-replica PostgreSQL database and one `MLflow` custom resource for the OpenShift AI MLflow operator.

The lab Applications do not sync this chart. Install it into `redhat-ods-applications` after the `DataScienceCluster` component `mlflowoperator` is `Managed`.

```bash
helm upgrade --install setup-mlflow ./setup-mlflow \
  --namespace redhat-ods-applications
```

PostgreSQL and the `MLflow` object are created in `mlflow.namespace`. The `ObjectBucketClaim` is created in the Helm release namespace. Keep that release namespace equal to `mlflow.namespace`.

## Resources

| Template | Resource |
| --- | --- |
| `templates/postgresql-pvc.yaml` | PVC `mlflow-postgres` (10Gi, `ReadWriteOnce`) |
| `templates/postgresql-configmap.yaml` | ConfigMap `mlflow-postgres-parameters` (`POSTGRES_DB=mlflow`, `PGDATA` under the volume) |
| `templates/postgresql-secret.yaml` | Secret `mlflow-postgres` with `POSTGRES_USER` and `POSTGRES_PASSWORD` |
| `templates/postgresql-deployment.yaml` | Deployment `mlflow-postgres`, image `postgres:16`, `Recreate` strategy |
| `templates/postgresql-service.yaml` | Service `mlflow-postgres` on port `5432` |
| `templates/mlflow-db-secret.yaml` | Secret `mlflow-db-credentials` consumed by the `MLflow` backend store |
| `templates/mlflow.yaml` | `MLflow` `default-mlflow` in `redhat-ods-applications` |
| `templates/objectbucketclaim.yaml` | `ObjectBucketClaim` `mlflow-artifacts` |

`spec.replicas` is `1`. The backend store Secret is `mlflow-db-credentials` (`backendStore.databaseConnection.secretRef`). That Secret's `backend-store-uri` and `registry-store-uri` are `postgresql://mlflow:<password>@mlflow-postgres.redhat-ods-applications.svc.cluster.local:5432/mlflow`. It also stores `username`, `password`, `database`, `host`, and `port`.

Artifact storage is the S3 bucket `mlflow-artifacts`. The claim uses `objectStorage.storageClassName`. The `MLflow` object still reads S3 credentials from the Secret `mlflow-s3-credentials`. This chart does not create that Secret. The claim creates a Secret of the same name as the claim.

## Values

| Key | Role |
| --- | --- |
| `mlflow.name` | Name of the `MLflow` object. DNS-1123 label. |
| `mlflow.namespace` | Namespace of the `MLflow` object, PostgreSQL, and the database Secret. |
| `mlflow.replicas` | Tracking server replicas. Integer of at least 1. |
| `mlflow.backendStore.secretName` | Secret that holds the PostgreSQL connection. |
| `mlflow.artifactStore.bucket` | S3 bucket name and `ObjectBucketClaim` name. |
| `mlflow.artifactStore.secretName` | Secret name the `MLflow` object uses for S3 credentials. |
| `postgresql.name` | Deployment, Service, PVC, and database Secret name. DNS-1123 label. |
| `postgresql.image` | PostgreSQL image. |
| `postgresql.user` | Database user. Also `POSTGRES_USER`. |
| `postgresql.password` | Database password. Also `POSTGRES_PASSWORD`. |
| `postgresql.database` | Database name. Also `POSTGRES_DB`. |
| `postgresql.storage` | PVC request size. |
| `objectStorage.storageClassName` | Storage class on the `ObjectBucketClaim`. |
| `objectStorage.host` | Present for the NooBaa endpoint. Unused by the templates. |
| `objectStorage.port` | Present for the NooBaa endpoint. Unused by the templates. |
| `objectStorage.region` | Present for the NooBaa endpoint. Unused by the templates. |

The chart rejects a missing value, a name that is not a DNS-1123 label, and a replica count below 1.

## Lab password

The PostgreSQL Secrets in this chart use the lab password `test` and the user `mlflow`. Replace them before using the database outside this demo. The password is URL-encoded in `backend-store-uri` and `registry-store-uri`.

## Author

Asier Cidon @RedHat
