# Cluster bootstrap

Manifests and a script that hand the lab to the default Argo CD instance in `openshift-gitops`.

## Run

From this directory, logged in as a cluster admin:

```bash
./setup.sh
```

The script does the following:

1. Creates the `openshift-gitops-operator` and `project01` namespaces.
2. Labels `project01` with `opendatahub.io/dashboard-enabled=true` so the project shows up in the OpenShift AI dashboard.
3. Applies [`00-GitOps-Operator.yaml`](00-GitOps-Operator.yaml), which subscribes to `openshift-gitops-operator` from `redhat-operators` on the `latest` channel, then waits 60 seconds.
4. Applies [`01-application-project.yaml`](01-application-project.yaml) and [`02-application-registry.yaml`](02-application-registry.yaml).
5. Labels `project01` and `rhoai-model-registries` with `argocd.argoproj.io/managed-by=openshift-gitops`.
6. Binds `openshift-gitops:openshift-gitops-argocd-application-controller` to `cluster-admin` so that instance can create the project Argo CD, the model registry, and the namespace-scoped objects those charts own.

Install the OpenShift AI model registry component first so the `rhoai-model-registries` namespace exists. The script labels that namespace.

## Applications

Both Applications live in `openshift-gitops`, track `master` of `https://github.com/acidonper/rhoai-mlops-demo.git`, and sync automatically with prune and self-heal.

| File | Application | Path | Destination |
| --- | --- | --- | --- |
| `01-application-project.yaml` | `ocp-setup-project` | `mlops/helm/setup-project` | `project01` (`CreateNamespace=true`) |
| `02-application-registry.yaml` | `ocp-setup-registry` | `mlops/helm/setup-registry` | `rhoai-model-registries` |

The Subscription sets `DISABLE_DEFAULT_ARGOCD_INSTANCE=false`, so the instance in `openshift-gitops` stays in place and reconciles these Applications. It sets `ARGOCD_CLUSTER_CONFIG_NAMESPACES` to `project01,rhoai-model-registries`.

What each chart installs is described in [../helm/README.md](../helm/README.md).

## Names baked into this directory

| File | What to edit |
| --- | --- |
| `setup.sh` | Namespace names `project01` and `rhoai-model-registries` |
| `00-GitOps-Operator.yaml` | `ARGOCD_CLUSTER_CONFIG_NAMESPACES` |
| `01-application-project.yaml` | `repoURL`, `targetRevision`, and the destination namespace |
| `02-application-registry.yaml` | `repoURL` and `targetRevision` |

The same project name, repository, and revision also appear in [`../helm/setup-project/values.yaml`](../helm/setup-project/values.yaml) and [`../helm/setup-registry/values.yaml`](../helm/setup-registry/values.yaml).

## Author

Asier Cidon @RedHat