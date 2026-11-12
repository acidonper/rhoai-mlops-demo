---
name: tekton-helm-pipeline
description: >-
  Creates Tekton pipelines, tasks, and triggers as Helm templates the way
  the RHOAI ops chart does. Use when the user asks to add or change a Tekton
  pipeline, task, trigger, trigger template, event listener, or PipelineRun
  in the Helm chart, or to wire a GitHub push to a pipeline.
---

# Tekton pipelines as a Helm chart

Match `researcher-project/mlops/ops`. The chart name is `tekton-pipeline`. Argo CD Application `application-ops` syncs that directory into the project namespace from `master`. Do not add a namespace to resource metadata. The Application destination is the namespace.

## Values

`values.yaml` has two keys. Use them for facts that are true for the cluster and are not on the webhook.

| Key | Use |
| --- | --- |
| `namespace` | OpenShift project. Image streams, `oc tag`, and the model URI project. |
| `cluster_domain` | Apps domain. The model registry host suffix. |

Webhook facts stay Tekton params: git URL, branch, short revision, commit author, application name. Do not copy them into `values.yaml`.

## Two languages in one file

Helm renders first. Tekton substitutes later. The shell runs last.

| Write | Who replaces it | Example |
| --- | --- | --- |
| `{{ .Values.namespace }}` | Helm | project passed into a task param |
| `{{ .Values.cluster_domain }}` | Helm, including inside a quoted heredoc | registry host |
| `$(params.NAME)` | Tekton | task and pipeline params |
| `$(tasks.<task>.results.<result>)` | Tekton | pipeline result |
| `$(results.NAME.path)` | Tekton | file path of a task result |
| `$(workspaces.NAME.path)` | Tekton | workspace mount |
| `$(tt.params.name)` | Triggers | value inside the TriggerTemplate |
| `$(extensions.key)` and `$(body....)` | Triggers | CEL overlay and webhook body |
| `$VAR` and `$?` | shell | `$HOME`, `rc=$?` |

Leave `$(...)` unescaped. `$$(params.NAME)` would stop Tekton from substituting it. Python f-string braces stay single (`{namespace}`). Helm only acts on `{{ }}`.

`cat << 'EOF'` stops the shell from expanding `$`. Tekton has already replaced `$(params...)` in the YAML, and Helm has already replaced `{{ .Values... }}`. Put runtime Python in that quoted heredoc. Put shell that must expand `$HOME` or `$?` in a `script: |` block.

## Files

```
ops/
  Chart.yaml
  values.yaml
  templates/pvc/workspace.yaml          # shared-workspace
  templates/pvc/models.yaml             # <application>-model-pvc
  templates/tekton/pipeline.yaml        # Pipeline ct-pipeline
  templates/tekton/trigger.yaml         # Trigger
  templates/tekton/trigger-template.yaml
  templates/tekton/event-listener.yaml  # EventListener and Route
  templates/tekton/tasks/<task>.yaml    # one Task per file
```

There is no `templates/_helpers.tpl`. A task with no Helm values is still a template because it lives under `templates/`.

## Pipeline

Name `ct-pipeline`, `apiVersion: tekton.dev/v1`. Workspaces `shared-workspace` and `model-workspace`. Params, each `type: string` and `default: ""`, except `GIT_SSL_VERIFY` default `"false"`:

`APPLICATION_NAME`, `PROJECT_NAME`, `GIT_URL`, `GIT_SHORT_REVISION`, `GIT_BRANCH`, `GIT_COMMIT_AUTHOR`, `GIT_SSL_VERIFY`.

Active order. Each later task sets `runAfter` to the previous one.

1. `fetch-ds-pipeline-repository`. Cluster resolver, not a local Task. `kind: task`, `name: git-clone`, `namespace: openshift-pipelines`. Workspace `output` is `shared-workspace`. Params: `URL` `$(params.GIT_URL)`, `REVISION` the literal `master`, `SUBDIRECTORY` `$(params.APPLICATION_NAME)/$(params.GIT_BRANCH)`, `DELETE_EXISTING` `"true"`, `SSL_VERIFY` `$(params.GIT_SSL_VERIFY)`.
2. `execute-ds-pipeline`. Local `taskRef` `name` / `kind: Task`. Workspace `output` is `shared-workspace`. `WORK_DIRECTORY` is `$(params.APPLICATION_NAME)/$(params.GIT_BRANCH)/researcher-project/pipelines`.
3. `build-modelcar`. Workspace `output` is `model-workspace`. `PROJECT_NAME` value is `{{ .Values.namespace }}`, not `$(params.PROJECT_NAME)`.
4. `update-model-metadata`. No workspace. `PROJECT_NAME` is `{{ .Values.namespace }}`. `KFP_RUN_ID` is `$(tasks.execute-ds-pipeline.results.KFP_RUN_ID)`.

The pipeline `results` entry republishes that same `KFP_RUN_ID`.

`deploy-or-raise-pr` stays commented. The comment in the pipeline says the Git model version is updated manually. Leave it commented unless the user asks to enable it. The task writes `version`, while `ml/values.yaml` and the inference template read `model_version`. Align those keys before enabling it.

`PROJECT_NAME` on the pipeline is unused by the active tasks. The trigger template does not pass it. Pass `{{ .Values.namespace }}` for the OpenShift project.

Reference a local task by name:

```yaml
- name: execute-ds-pipeline
  taskRef:
    name: execute-ds-pipeline
    kind: Task
  runAfter:
    - fetch-ds-pipeline-repository
  params:
    - name: APPLICATION_NAME
      value: "$(params.APPLICATION_NAME)"
```

## Tasks

One task, one file, under `templates/tekton/tasks/`. New tasks use `tekton.dev/v1`. Keep `tekton.dev/v1beta1` on `build-modelcar` and `update-model-metadata` when editing those files.

| Task | Image | What it does |
| --- | --- | --- |
| `execute-ds-pipeline` | `registry.redhat.io/ubi9/python-311` digest in the file | Install `kfp==2.9.0` and `kfp-kubernetes==1.3.0`. Import `training_pipeline` from `prod_train_save_pipeline`. Client host `https://ds-pipeline-dspa.<pod namespace>.svc:8443` with the service-account token and `service-ca.crt`. Load `default_parameters.json`, then set `version` to `$(params.GIT_SHORT_REVISION)`, `model_name` to `$(params.APPLICATION_NAME)`, `model_storage_pvc` to `$(params.APPLICATION_NAME)-model-pvc`, `cluster_domain` to `{{ .Values.cluster_domain }}`, `prod_flag` to `False`. Experiment `$(params.APPLICATION_NAME)-model-training`, caching on. Wait up to 7200 seconds. Write the run id to `$(results.KFP_RUN_ID.path)`. |
| `build-modelcar` | `quay.io/openshift/origin-cli:4.14` | Working dir is the model workspace root. Dockerfile `FROM registry.access.redhat.com/ubi9/ubi-minimal:9.4`, `WORKDIR /models/1`, copy `$(params.APPLICATION_NAME).onnx` and `artifacts/`, `USER 1001`. `oc new-build --binary` with `\|\| rc=$?` so an existing BuildConfig continues. `oc start-build --from-dir=. --follow --wait`. Tag `:latest` to `:$(params.VERSION)` in `$(params.PROJECT_NAME)`. |
| `update-model-metadata` | same python image | Install `model-registry==0.2.10`. Set `KF_PIPELINES_SA_TOKEN_PATH`. Registry `https://<pod namespace>-registry-rest.{{ .Values.cluster_domain }}`, port 443, `is_secure=False`, author `$(params.GIT_COMMIT_AUTHOR)`. Set `pipeline_run_id`. On every other version, remove custom property `production` when it is present. On this version set `production` to `""`, `labels` to `deployable-latest, production`, and the author. Set the artifact URI to `oci://image-registry.openshift-image-registry.svc:5000/$(params.PROJECT_NAME)/$(params.APPLICATION_NAME):$(params.VERSION)`. |
| `deploy-or-raise-pr` | `quay.io/redhat-cop/tekton-task-helm:3.6.3`, then `quay.io/redhat-cop/ubi8-git:latest` | `yq eval -i` on `values.yaml` in `WORK_DIRECTORY`. Commit as `tekton@mlops.bot.com` / `🐈 Tekton 🐈`, `safe.directory '*'`, push `HEAD:master` using `$HOME/.git-credentials` and `$(params.PROJECT_NAME)/mlops-gitops.git`. |

`workingDir` for a git checkout is `$(workspaces.output.path)/$(params.WORK_DIRECTORY)`. The model-car task uses `$(workspaces.output.path)` with the model PVC, not the git workspace.

A failure path that calls `sys.exit` must `import sys`. The checked-in execute step calls `sys.exit(1)` and does not import `sys`.

## Trigger path

Names stay aligned: pipeline `ct-pipeline`, PipelineRun `generateName: ct-pipeline-`, trigger `ct-gitea-trigger`, template `ct-gitea-trigger-template`, listener `ct-listener`, route `el-ct-listener`. Tekton creates the Service `el-<listener name>`.

`triggers.tekton.dev/v1beta1` on the Trigger, TriggerTemplate, and EventListener.

CEL interceptor:

- Filter: `header.match('X-GitHub-Event', 'push') && body.ref.split('/')[2] == 'master'`. `refs/heads/master` makes index 2 the branch.
- Overlays: `body.head_commit.id.truncate(10)` onto `truncated_sha`, and `body.ref.split('/')[2]` onto `branch_name`.

Bindings map those onto template params: `git-branch`, `git-short-revision`, `gitrepositoryurl` from `$(body.repository.clone_url)`, `git-repo-name` from `$(body.repository.name)`, `git-commit-author` from `$(body.pusher.username)`. The template `ref` is `ct-gitea-trigger-template`.

The TriggerTemplate renders a `PipelineRun` of `ct-pipeline`. `APPLICATION_NAME` is the literal `jukebox`. Git params use `$(tt.params.<name>)`. It does not pass `PROJECT_NAME` or `GIT_SSL_VERIFY`. Workspaces:

- `shared-workspace` claim `shared-workspace`
- `model-workspace` claim `jukebox-model-pvc`

The EventListener lists `triggerRef: ct-gitea-trigger`. The Route targets Service `el-ct-listener` port `http-listener`, TLS edge, insecure redirected.

## PVCs

Both claims are 3Gi, `Filesystem`, `ReadWriteOnce`, annotation `volume.beta.kubernetes.io/storage-provisioner: kubernetes.io/aws-ebs`. `shared-workspace` is the clone volume. The model claim name is `<APPLICATION_NAME>-model-pvc` and matches `model_storage_pvc` in the KFP task and `claimName` on the PipelineRun. The checked-in claim is `jukebox-model-pvc`.

## Add a step

1. Add `templates/tekton/tasks/<name>.yaml`.
2. Insert the task in `pipeline.yaml` with `kind: Task`, params, workspace if it has one, and `runAfter` the task it must follow.
3. Publish a new result on the task and read it as `$(tasks.<task>.results.<name>)`.
4. A value from the webhook gets a pipeline param, a TriggerTemplate param, and a binding or CEL overlay.
5. A value that is fixed for the cluster goes in `values.yaml` and is passed with `{{ .Values.<key> }}`.
6. A new workspace needs a PVC template and a `claimName` on the TriggerTemplate PipelineRun.
7. Do not add a hand-written PipelineRun. This chart starts runs from the TriggerTemplate.
