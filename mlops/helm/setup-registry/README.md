# setup-registry

Chart `ocp-setup-registry`. Application `ocp-setup-registry` in `openshift-gitops` renders it with destination namespace `rhoai-model-registries`. Every template also sets that namespace explicitly.

The chart installs a single-replica MySQL 8.0.3 database and a `ModelRegistry` for the project named in `values.yaml`.

## Resources

Names use `namespace.name` (`project01` in the lab):

| Template | Resource |
| --- | --- |
| `templates/mysql-pvc.yaml` | PVC `metadata-mysql-<project>` (10Gi, `ReadWriteOnce`) |
| `templates/mysql-model-registry-db-parameters.yaml` | ConfigMap `registry-db-parameters-<project>` (`MYSQL_DATABASE=metadb`, port `3306`) |
| `templates/mysql-secret.yaml` | Secret `registry-db-<project>` with `MYSQL_ROOT_PASSWORD` and `MYSQL_USER_NAME` |
| `templates/mysql-deployment.yaml` | Deployment `registry-db-<project>` |
| `templates/mysql-service.yaml` | Service `registry-db-<project>` on port `3306` |
| `templates/model-registry-secret.yaml` | Secret `registry-db-<project>-secret` (`database-user`, `database-password`, `database-name`) consumed by the `ModelRegistry` |
| `templates/model-registry.yaml` | `ModelRegistry` `<project>-registry`, plus a `service-viewer` Role and one RoleBinding per workbench |
| `templates/model-registry-rbac.yaml` | Role `gitops-model-registry-manager` bound to `openshift-gitops:openshift-gitops-argocd-application-controller` |

In the `ModelRegistry` spec the REST `serviceRoute` is disabled, the kube-rbac-proxy route is enabled, and gRPC listens on `9090`. Notebooks and the training pipeline call `https://<project>-registry-rest.<cluster-domain>`. The database user in the registry spec is `root`, database `metadb`, on `registry-db-<project>.rhoai-model-registries.svc.cluster.local`.

Each name in `namespace.workbenches` becomes a RoleBinding in `rhoai-model-registries`. The subject is the workbench ServiceAccount of that name in the project namespace, and the role can `get`, `list`, and `watch` Services. Create the workbench before relying on that binding; the sample manifest is [`../../../researcher-project/argocd/workbench.yaml`](../../../researcher-project/argocd/workbench.yaml).

## Values

| Key | Role |
| --- | --- |
| `namespace.name` | Project name used in resource names and in the workbench RoleBinding subject namespace. |
| `namespace.workbenches[].name` | Workbench ServiceAccount that receives `service-viewer` on the registry namespace. |

`gitRepo` is present in `values.yaml` and is unused by this chart. The bootstrap Application in [`../../ocp/02-application-registry.yaml`](../../ocp/02-application-registry.yaml) carries the repository URL.

## Lab password

The MySQL Secrets in this chart use the lab password `test` and the user `root`. Replace them before using the registry outside this demo.

## Author

Asier Cidon @RedHat