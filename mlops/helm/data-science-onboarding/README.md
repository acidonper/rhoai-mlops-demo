# data-science-onboarding

Helm chart for one data science project. Application `data-science-onboarding` sets the release namespace, and that namespace is the project name. The chart release name is the same namespace (`project01` in the lab).

For each entry in `buckets` the chart creates:

- an `ObjectBucketClaim` named `<namespace>-<name>`, with the same `bucketName`
- a PostSync Job `start-connection-<name>` that starts a `create-kubernetes-object` PipelineRun

The pipeline copies the claim's NooBaa credentials into an OpenShift AI connection Secret. The Secret name is `connectionName`, or `aws-connection-<obc-name>` when `connectionName` is empty. The claim name is `<namespace>-<name>`, so an empty `connectionName` on the `models` bucket in `project01` becomes `aws-connection-project01-models`. The lab values set `aws-connection-models` and `aws-connection-pipelines` explicitly. The pipeline then writes `opendatahub.io/connections` on each Notebook in `workbenchName`, appending `<namespace>/<connection-name>` to the existing annotation.

`templates/dspa.yaml` runs the project pipeline server. Artifacts go to the bucket `<namespace>-pipelines`. The server reads `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` from the Secret `aws-connection-pipelines`. Host, port, and scheme come from `objectStorage` (`s3.openshift-storage.svc`, `443`, and `https`). That Secret appears after the `pipelines` bucket's PipelineRun finishes, so the `dspa` object can be unhealthy until that run succeeds.

`namespace.create` is false. [`../../ocp/setup.sh`](../../ocp/setup.sh) creates `project01`, and Application `ocp-setup-project` also sets `CreateNamespace=true`.

## Values

| Key | Role |
| --- | --- |
| `namespace.create` | Create a Namespace for `.Release.Namespace` when true. |
| `namespace.labels` | Extra labels on that Namespace. |
| `objectStorage.host` | S3 host on the pipeline server. |
| `objectStorage.port` | S3 port on the pipeline server. |
| `objectStorage.storageClassName` | Storage class on every `ObjectBucketClaim`. |
| `objectStorage.region` | Unused by the templates. Set `buckets[].region` for a bucket-specific region. |
| `pipeline.application` | Label `argocd.argoproj.io/application` on the generated PipelineRun. |
| `pipeline.name` | Pipeline the Job starts (`create-kubernetes-object`). |
| `pipeline.serviceAccountName` | Service account on the PipelineRun (`pipeline-object-creator`). |
| `pipeline.runCreatorServiceAccount` | Service account on the Job (`pipeline-run-creator`). |
| `pipeline.image` | OpenShift CLI image the Job uses to `oc create` the PipelineRun. |
| `pipeline.backoffLimit` | Job `backoffLimit`. |
| `pipeline.activeDeadlineSeconds` | Job deadline. |
| `pipeline.ttlSecondsAfterFinished` | How long a finished Job is kept. |
| `buckets[].name` | DNS-1123 label. Claim, bucket, and Job names are derived from it. |
| `buckets[].connectionName` | Connection Secret name. Empty selects `aws-connection-<namespace>-<name>`. |
| `buckets[].workbenchName` | Notebook names that receive the connection annotation. Empty publishes the Secret only. |
| `buckets[].region` | Region used when the claim ConfigMap has no `BUCKET_REGION`. Empty reaches the pipeline as an empty parameter, and the task then uses `us-east-1`. |

The Job is an Argo CD PostSync hook and a Helm post-install/post-upgrade hook. It is deleted before the next creation and after it succeeds.

## Add a bucket

Add a list entry and let `data-science-onboarding` sync again:

```yaml
buckets:
  - name: features
    connectionName: aws-connection-features
    workbenchName:
      - test-workbench
    region: ""
```

The chart rejects a missing `name`, a `name` that is not a DNS-1123 label, a `name` that makes `start-connection-<name>` longer than 63 characters, a duplicate `name`, a `workbenchName` that is not a list, a workbench name that is not a DNS-1123 label, and a duplicate workbench name on the same bucket.

## Pipeline server bucket

Keep a bucket entry that publishes `aws-connection-pipelines` for `<namespace>-pipelines`. The `dspa` manifest references that Secret and that bucket by those names.

## Author

Asier Cidon @RedHat