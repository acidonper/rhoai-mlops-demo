# data-science-onboarding

Helm chart for one data science project. Argo CD sets the release namespace, which is also the project name.

For each entry in `values.yaml` `buckets` the chart creates:

- an `ObjectBucketClaim` named `<namespace>-<name>`, with the same `bucketName`
- a PostSync Job `start-connection-<name>` that starts the `create-kubernetes-object` PipelineRun

The pipeline copies the claim's NooBaa credentials into the OpenShift AI connection Secret (`connectionName`, or `aws-connection-<obc-name>` when that field is empty) and annotates each Notebook in `workbenchName`.

`templates/dspa.yaml` runs the project pipeline server on the `<namespace>-pipelines` bucket. Credentials come from `aws-connection-pipelines`. Host and port come from `objectStorage` in `values.yaml` (`s3.openshift-storage.svc` and `443` by default).

`namespace.create` stays false because `ocp/setup` already creates the project.
