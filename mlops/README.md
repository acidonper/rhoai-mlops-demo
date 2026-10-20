# Platform setup

GitOps manifests that prepare one OpenShift AI project for the jukebox lab. The bootstrap lives in [`ocp`](ocp/README.md). Helm charts live in [`helm`](helm/README.md). The pipeline that publishes S3 connections lives in [`tekton`](tekton/README.md).

`mlops/ocp/setup.sh` is the entry point. It registers two Applications with the default Argo CD instance in `openshift-gitops`:

| Application | Chart | Destination |
| --- | --- | --- |
| `ocp-setup-project` | [`helm/setup-project`](helm/setup-project/README.md) | `project01` |
| `ocp-setup-registry` | [`helm/setup-registry`](helm/setup-registry/README.md) | `rhoai-model-registries` |

`setup-project` then installs a second Argo CD in the project. That instance syncs [`tekton/s3`](tekton/s3/README.md) and [`helm/data-science-onboarding`](helm/data-science-onboarding/README.md).

Researcher notebooks and the training pipeline are in [`../researcher-project`](../researcher-project/README.md). Those files stay out of this sync.


## Author

Asier Cidon @RedHat