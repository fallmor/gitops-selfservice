# GitOps Self-Service Infrastructure

Self-service infrastructure platform using **Flux CD** + **Crossplane** on OVHcloud.
Developers claim databases with a 10-line YAML. Crossplane provisions and reconciles forever.

## Stack

| Component | Role |
|-----------|------|
| Flux CD | GitOps engine — watches Git, syncs cluster |
| Crossplane | Infrastructure control plane — provisions OVHcloud resources |
| provider-ovh | Crossplane provider for OVHcloud APIs |
| Vault + ESO | Secret management |
| function-claude-recommender | AI function — sizes infra from plain-English description |

## Repository Layout

```
├── fluxcd/                  Flux bootstrap manifests (GitRepository, HelmRelease, Kustomizations)
├── crossplane-provider/     Crossplane provider install (provider-ovh)
├── crossplane/              XRD + Composition + ProviderConfig
├── apps/                    Developer claims (database-claim.yaml)
├── crossplane-functions/    AI-assisted compositions (Claude function)
└── vault-eso/               Vault SecretStore + ExternalSecret
```

---

## Prerequisites

- A running Kubernetes cluster
- `kubectl` configured against it
- `flux` CLI — https://fluxcd.io/flux/installation/
- An OVHcloud account with API credentials
- This repository forked and pushed to your own GitHub

---

## 1. Bootstrap Flux

Connect Flux to your Git repository. Everything after this step is managed via Git.

```bash
flux bootstrap github \
  --owner=<your-github-username> \
  --repository=gitops-selfservice \
  --branch=main \
  --path=./fluxcd \
  --personal
```

Flux installs its controllers and starts watching the repo immediately.

```bash
flux get kustomizations
flux get sources git
```

---

## 2. Create the OVHcloud credentials secret

```bash
kubectl create namespace crossplane-system

kubectl create secret generic ovh-secret \
  --namespace crossplane-system \
  --from-literal=credentials='{"endpoint":"ovh-eu","appKey":"<APP_KEY>","appSecret":"<APP_SECRET>","consumerKey":"<CONSUMER_KEY>"}'
```

Get your OVHcloud API credentials at https://www.ovh.com/auth/api/createToken

---

## 3. Crossplane installs itself via Flux

Flux picks up `fluxcd/helmrelease.yaml` and installs Crossplane automatically.
It then applies `crossplane-provider/` and `crossplane/` in order via `dependsOn`.

```bash
# Watch Crossplane come up
kubectl get pods -n crossplane-system -w

# Verify the OVH provider and XRD are ready
kubectl get providers
kubectl get crds | grep selfservice.ovh
```

---

## 4. Claim a database

```bash
kubectl apply -f apps/database-claim.yaml
```

Watch Crossplane provision the real OVHcloud resources:

```bash
kubectl get databases -n default
kubectl get databaseinstance -A
kubectl get databaseuser -A
```

The claim is ready when `READY=True` and `SYNCED=True`.

---

## 5. Demo — Reconciliation

Delete the managed resource to simulate drift:

```bash
kubectl delete databaseinstance <name> --wait=false
```

Watch Crossplane detect and fix the drift automatically:

```bash
watch kubectl get databaseinstance -A
```

It comes back within ~30 seconds.

---

## 6. AI-assisted claim (Claude function)

The developer describes their workload in plain English — no need to know `storageGB` or `plan`.
The `function-claude-recommender` calls the Claude API and recommends optimal sizing automatically.

Create the Anthropic API key secret:

```bash
kubectl create secret generic claude \
  --namespace crossplane-system \
  --from-literal=credentials=<YOUR_ANTHROPIC_API_KEY>
```

Install the function, XRD and Composition:

```bash
kubectl apply -f crossplane-functions/function-claude-recommender.yaml
kubectl apply -f crossplane-functions/ai-database-xrd.yaml
kubectl apply -f crossplane-functions/ai-composition.yaml
```

Submit the AI claim:

```bash
kubectl apply -f crossplane-functions/ai-database-claim.yaml
```

Inspect the Claude recommendation in the events:

```bash
kubectl describe aidatabase shop-postgres
```

---

## 7. Vault + External Secrets (optional)

```bash
kubectl apply -f vault-eso/secretstore.yaml
kubectl apply -f vault-eso/external-secret-ovh.yaml
```

The `ExternalSecret` syncs credentials from Vault into a Kubernetes Secret that Crossplane reads.

---

## Useful commands

```bash
# Watch all Flux reconciliations
flux get all

# Force a reconciliation without waiting for the Git poll interval
flux reconcile kustomization apps-resources

# Check all Crossplane managed resources
kubectl get managed

# See why a claim is not ready
kubectl describe database demo-postgres-db -n default

# View Crossplane logs
kubectl logs -n crossplane-system -l app=crossplane
```
