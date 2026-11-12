# setup-project

Chart `ocp-setup-project`. Application `ocp-setup-project` in `openshift-gitops` renders it into the namespace in `values.yaml` (`project01`).

## Resources

| Template | Resource |
| --- | --- |
| `templates/argocd.yaml` | `ArgoCD` named `argocd` in the project namespace. The route is enabled, Dex uses OpenShift OAuth, and cluster admins map to the Argo CD `admin` role. `TaskRun` and `PipelineRun` objects are excluded from the resource tracking. |
| `templates/application.yaml` | Application `data-science-onboarding` in the project namespace. It syncs `mlops/tekton/s3` and this repo's `mlops/helm/data-science-onboarding` chart into the same namespace. |
| `templates/kueue-rbac.yaml` | RoleBinding `argocd-kueue-localqueue-editor`. It grants `argocd-argocd-application-controller` the Kueue `kueue-localqueue-editor-role` in the project namespace, so that controller can create the onboarding `LocalQueue`. Sync wave `-1` creates the binding before Application `data-science-onboarding`. |
| `templates/namespace.yaml` | Commented out. [`../../ocp/setup.sh`](../../ocp/setup.sh) creates `project01`, and `ocp-setup-project` also sets `CreateNamespace=true`. |

The project-local Argo CD reconciles `data-science-onboarding` because that Application is created in the project namespace.

The tekton source syncs YAML in `mlops/tekton/s3` and sets `directory.exclude` to `example-*.yaml`. Samples under `mlops/tekton/s3/run-examples/` are for `oc create`. See [../../tekton/s3/README.md](../../tekton/s3/README.md).

## Values

| Key | Role |
| --- | --- |
| `namespace.name` | Namespace of the `ArgoCD` instance and of Application `data-science-onboarding`. Also the Helm release name for the onboarding chart. |
| `gitRepo.url` | Repository both sources of `data-science-onboarding` track. |
| `gitRepo.revision` | Revision both sources track (`master`). |

`namespace.workbenches` is present in `values.yaml` and is unused by this chart. The registry chart reads the same list; see [../setup-registry/README.md](../setup-registry/README.md). Workbench attachment for S3 connections is `buckets[].workbenchName` in the [onboarding chart](../data-science-onboarding/README.md).

## Author

Asier Cidon @RedHat