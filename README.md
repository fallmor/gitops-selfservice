# GitOps Self-Service Infrastructure

Self-service infrastructure platform using **Flux CD** + **Crossplane** on OVHcloud.
Developers claim databases with a 10-line YAML. Crossplane provisions and reconciles forever.

## Stack

| Component | Role |
|-----------|------|
| Flux CD | GitOps engine — watches Git, syncs cluster |
| Crossplane | Infrastructure control plane — provisions OVHcloud resources |
| provider-ovh | Crossplane provider for OVHcloud APIs |
| function-claude | AI function — sizes infra from plain-English description |

## Repository Layout

```
├── fluxcd/                  Flux bootstrap manifests (GitRepository, HelmRelease, Kustomizations)
├── crossplane-provider/     Crossplane provider install (provider-ovh)
├── crossplane/              XRD + Composition + ProviderConfig
├── crossplane-functions/    AI-assisted compositions (Claude function + XRD + Composition)
└── apps/                    Developer claims
```

---

## Prerequisites

- A running Kubernetes cluster (OVHcloud MKS recommended)
- `kubectl` configured against it
- `flux` CLI — https://fluxcd.io/flux/installation/
- An OVHcloud account with API credentials
- A GitHub personal access token (repo scope)
- An Anthropic API key

---

## Getting Started

### 1. Create secrets

```bash
kubectl create namespace crossplane-system

# OVHcloud credentials
kubectl create secret generic ovh-secret \
  --namespace crossplane-system \
  --from-literal=credentials='{"endpoint":"ovh-eu","application_key":"<APP_KEY>","application_secret":"<APP_SECRET>","consumer_key":"<CONSUMER_KEY>"}'

# Claude API key
kubectl create secret generic claude \
  --namespace crossplane-system \
  --from-literal=ANTHROPIC_API_KEY=<YOUR_ANTHROPIC_API_KEY>
```

### 2. Bootstrap Flux

```bash
flux bootstrap github \
  --owner=<your-github-username> \
  --repository=gitops-selfservice \
  --branch=main \
  --path=./fluxcd \
  --personal
```

Flux installs Crossplane, the OVH provider, and all XRDs automatically via `dependsOn` ordering.

```bash
flux get kustomizations --watch
```

### 3. Claim a database

```bash
git add apps/database-claim.yaml apps/kustomization.yaml
git commit -m "feat: add postgres database"
git push
```

Crossplane provisions the OVHcloud resources automatically.

```bash
kubectl get databases -n default
kubectl get managed
```

---

## Useful commands

```bash
# Force immediate Flux sync
flux reconcile source git gitops-selfservice

# Check all managed resources
kubectl get managed

# See why a claim is not ready
kubectl describe database <name> -n default

# View Crossplane logs
kubectl logs -n crossplane-system -l app=crossplane
```
