# Helm charts

Three charts. The default Argo CD instance in `openshift-gitops` syncs the first two. The Argo CD installed by `setup-project` syncs the third, together with [`../tekton/s3`](../tekton/s3/README.md).

| Chart | Synced by | What it creates |
| --- | --- | --- |
| [`setup-project`](setup-project/README.md) | Application `ocp-setup-project` | An Argo CD instance in the data science project, and the Application `data-science-onboarding` |
| [`setup-registry`](setup-registry/README.md) | Application `ocp-setup-registry` | MySQL and a `ModelRegistry` in `rhoai-model-registries` |
| [`data-science-onboarding`](data-science-onboarding/README.md) | Application `data-science-onboarding` | ObjectBucketClaims, the Jobs that publish OpenShift AI connections, and the `dspa` pipeline server |

`setup-project` and `setup-registry` both read a `namespace.name` of `project01`. Keep those two values files, [`../ocp/setup.sh`](../ocp/setup.sh), and [`../ocp/01-application-project.yaml`](../ocp/01-application-project.yaml) on the same project name.
