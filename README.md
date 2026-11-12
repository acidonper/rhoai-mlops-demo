# 🚀 Red Hat OpenShift AI: End-to-End AI/ML Lifecycle Demo

[![Red Hat OpenShift AI](https://img.shields.io/badge/Red_Hat-OpenShift_AI-EE0000?logo=redhat&logoColor=white)](#)
[![KServe](https://img.shields.io/badge/Serving-KServe-blue?logo=kubernetes)](#)
[![Jupyter](https://img.shields.io/badge/Jupyter-F37626.svg?style=for-the-badge&logo=Jupyter&logoColor=white)](#)
[![Kubeflow](https://img.shields.io/badge/Kubeflow-0088CC.svg?style=for-the-badge&logo=Kubeflow&logoColor=white)](#)
[![ArgoCD](https://img.shields.io/badge/ArgoCD-EF7B4D.svg?style=for-the-badge&logo=Argo&logoColor=white)](#)
[![Status](https://img.shields.io/badge/Status-Active_Demo-success)](#)

Welcome to the **End-to-End MLOps Demo Repository**. This project showcases how to overcome common data science workflow challenges by bridging the gap between isolated notebook experimentation and robust, scalable production handoffs.

## 📖 Overview

Transitioning machine learning models from a data scientist's local notebook into a reliable production environment is notoriously difficult. This demo provides a comprehensive, hands-on walkthrough of a modern MLOps architecture using **Red Hat OpenShift AI**. 

Here, we explore the complete lifecycle—from initial infrastructure setup and pipeline orchestration to model serving and real-time observability.

## 🌟 Why MLOps?

By implementing the practices demonstrated in this repository, organizations can:

- ⚡ **Accelerate Delivery:** Streamline the path from model creation to deployment.
- 🛡️ **Maintain Governance & Trust:** Ensure models are fair, explainable, and compliant.
- 🏗️ **Achieve Reliability at Scale:** Standardize deployments to handle production-level traffic and data drift securely.

## 👥 Core Personas & Roles

A successful MLOps platform requires collaboration across multiple disciplines. This demo highlights the specific platform roles of three core personas:

| Persona | Role in the Platform |
| :--- | :--- |
| **Data Scientists** | Focus on data exploration, model training, and experimentation in Jupyter/VSCode notebooks without worrying about underlying infrastructure. |
| **MLOps Engineers** | Automate workflows, manage model registries, orchestrate training pipelines, and ensure smooth CI/CD integration. |
| **Infrastructure Engineers** | Provision clusters, manage GPU/CPU resources, ensure platform security, and maintain the underlying Red Hat OpenShift ecosystem. |


## 🛠️ Operational Phases & Demo Architecture

This repository is structured around several critical operational phases:

### 1. Infrastructure Setting Up

Create Namespaces, install ArgoCD operators and instances, enable Model Registries basement and setup MLOps  main components.

### 2. Implement AI/ML Operation

Setting up data science projects including registry, pipelines server, s3 buckets, storage connections and integrate tekton/ML pipelines.

### 3. Data Scientist Evolution

Emulate data scientist day to day and the respective evolution to a MLOps strategy for production

## 🛡️ Operational Challenges 

Operation phases demonstrate a key capability of Red Hat OpenShift AI:

### 1. Data Science Pipelines
Automate and orchestrate complex ML workflows. We transition from manual notebook execution to repeatable, version-controlled pipelines that handle data processing, training, and evaluation.

### 2. Model Registries
Centralize model artifact management. Track model versions, metadata, and lineage to ensure a clean handoff between the data science and MLOps teams.

### 3. Model Serving (KServe)
Deploy models to production with high availability. We utilize **KServe** for highly scalable, serverless model inferencing, complete with advanced routing and auto-scaling capabilities.

### 4. Observability & Monitoring 
Maintain model integrity post-deployment. We incorporate the capacity to integrate data drift monitoring, track model fairness, provide explainability metrics, and ensure ongoing governance.

## 🚀 Getting Started

*(Add instructions here for users cloning the repository)*

### Prerequisites

* Red Hat OpenShift
* Red Hat OpenShift AI, with the model registry component so the `rhoai-model-registries` namespace exists
* OpenShift Data Foundation, with the storage class set in `values.yaml` (`openshift-storage.noobaa.io` by default)
* OpenShift Pipelines
* OpenShift GitOps
* Red Hat build of Kueue operator

### Installation

1. Log in with `oc` as a cluster admin and execute the following commands:

```bash
cd mlops/ocp
./setup.sh
```

2. Set up a fresh workbench within the OpenShift AI dashboard under the `project01` namespace, ensuring it integrates the `aws-connection-models` data connection (you can log in via your Openshift AI environment route, e.g., https://rh-ai.apps.ocp.b5frx.sandbox1967.opentlc.com/projects/project01).

3. Follow [researcher-project/README.md](researcher-project/README.md)

Apply the workbench yourself, then follow [researcher-project/README.md](researcher-project/README.md). 

### Verification

The script creates the `openshift-gitops-operator` and `project01` namespaces, subscribes to the GitOps operator, and applies two Applications.

Following completion of the setup phase, you can log into these ArgoCD deployments for verification:

* Target namespace `openshift-gitops` featuring the `openshift-gitops` instance (e.g. https://openshift-gitops-server-openshift-gitops.apps.ocp.b5frx.sandbox1967.opentlc.com/).
* Target namespace `project01` featuring the `argocd` instance (e.g. https://argocd-server-project01.apps.ocp.b5frx.sandbox1967.opentlc.com/)

IMPORTANT: Authenticate using the administrative credentials from the `ArgoCDInstance`-cluster secret.

## Layout

| Path | Role |
| --- | --- |
| [`mlops/ocp`](mlops/ocp/README.md) | GitOps operator subscription and the two bootstrap Applications |
| [`mlops/helm/setup-project`](mlops/helm/setup-project/README.md) | Project Argo CD and the onboarding Application |
| [`mlops/helm/setup-registry`](mlops/helm/setup-registry/README.md) | Model registry and its MySQL database |
| [`mlops/helm/data-science-onboarding`](mlops/helm/data-science-onboarding/README.md) | Buckets, connection Jobs, and the pipeline server |
| [`mlops/tekton/s3`](mlops/tekton/s3/README.md) | Pipeline, tasks, and service accounts |
| `mlops/tekton/s3/run-examples` | PipelineRuns to create by hand |
| [`researcher-project`](researcher-project/README.md) | Notebooks, training pipeline, and sample workbench manifests |
| `skills` | Agent skills for the researcher-project KFP pipeline and the Tekton Helm chart |

## 🤝 Contributing

We welcome contributions! If you have ideas for improving the pipelines or adding new TrustyAI metrics, please open an issue or submit a pull request.

## 🥷🏻 Author

Asier Cidon @RedHat
