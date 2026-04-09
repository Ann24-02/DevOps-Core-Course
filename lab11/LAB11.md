Here is a complete report for **Lab 11 — Kubernetes Secrets & HashiCorp Vault** in English, based on the successful execution of all tasks.

---

# Lab 11 Report: Kubernetes Secrets & HashiCorp Vault

## Objective
The objective of this lab was to secure a Kubernetes application by implementing proper secret management using native Kubernetes Secrets and integrating HashiCorp Vault for enterprise-grade secret storage and injection.

---

## Task 1 — Kubernetes Secrets Fundamentals (2 pts)

### 1.1 Secret Creation
A generic secret named `app-credentials` was created imperatively using `kubectl`:

```bash
kubectl create secret generic app-credentials \
  --from-literal=username=admin_user \
  --from-literal=password='S3cure#Pass123'
```

### 1.2 Secret Inspection
The secret was viewed in YAML format:

```bash
kubectl get secret app-credentials -o yaml
```

**Output (partial):**
```yaml
apiVersion: v1
data:
  password: UzNjdXJlI1Bhc3MxMjM=
  username: YWRtaW5fdXNlcg==
kind: Secret
metadata:
  name: app-credentials
type: Opaque
```

### 1.3 Base64 Decoding
The encoded values were decoded to verify the original data:

```bash
echo "YWRtaW5fdXNlcg==" | base64 -d
# Output: admin_user

echo "UzNjdXJlI1Bhc3MxMjM=" | base64 -d
# Output: S3cure#Pass123
```

### 1.4 Security Implications
- **Base64 is encoding, NOT encryption.** It provides no confidentiality.
- By default, Kubernetes Secrets are **not encrypted at rest** in etcd.
- **Encryption at Rest** must be explicitly enabled via `EncryptionConfiguration` in the kube-apiserver.
- Anyone with access to etcd or the Kubernetes API can decode secrets.

---

## Task 2 — Helm-Managed Secrets (3 pts)

### 2.1 Helm Chart Structure
A Helm chart named `lab11-app` was created with the following structure:

```
lab11-app/
├── Chart.yaml
├── values.yaml
└── templates/
    ├── _helpers.tpl
    ├── secrets.yaml
    └── deployment.yaml
```

### 2.2 Secret Template (`templates/secrets.yaml`)
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: {{ include "lab11-app.fullname" . }}-secrets
type: Opaque
data:
  username: {{ .Values.secrets.username | b64enc | quote }}
  password: {{ .Values.secrets.password | b64enc | quote }}
```

### 2.3 Values File (`values.yaml`)
```yaml
image:
  repository: nginx
  tag: latest

resources:
  requests:
    memory: "64Mi"
    cpu: "250m"
  limits:
    memory: "128Mi"
    cpu: "500m"

secrets:
  username: admin_user
  password: S3cure#Pass123
```

### 2.4 Secret Injection in Deployment
Secrets were injected as environment variables using `secretKeyRef`:

```yaml
env:
- name: APP_USERNAME
  valueFrom:
    secretKeyRef:
      name: {{ include "lab11-app.fullname" . }}-secrets
      key: username
- name: APP_PASSWORD
  valueFrom:
    secretKeyRef:
      name: {{ include "lab11-app.fullname" . }}-secrets
      key: password
```

### 2.5 Verification
After installing the Helm chart:

```bash
helm install my-app ./lab11-app
```

Environment variables were verified inside the pod:

```bash
kubectl exec -it <pod-name> -- env | grep APP_
```

**Output:**
```
APP_USERNAME=admin_user
APP_PASSWORD=S3cure#Pass123
```

The secrets were **not visible** in `kubectl describe pod`, confirming proper injection.

### 2.6 Resource Limits
Resource requests and limits were configured to ensure proper resource management:
- **Requests:** CPU 250m, Memory 64Mi (guaranteed minimum)
- **Limits:** CPU 500m, Memory 128Mi (maximum allowed)

---

## Task 3 — HashiCorp Vault Integration (3 pts)

### 3.1 Vault Installation via Helm
Due to regional blocking of the HashiCorp Helm repository, Vault was installed directly from a local chart:

```bash
cd /tmp
curl -L -o vault-helm-0.28.1.tgz https://github.com/hashicorp/vault-helm/archive/refs/tags/v0.28.1.tar.gz
tar -xzf vault-helm-0.28.1.tgz
cd vault-helm-0.28.1
helm install vault . --namespace vault --create-namespace \
  --set "server.dev.enabled=true" \
  --set "injector.enabled=true"
```

### 3.2 Verification of Vault Pods
```bash
kubectl get pods -n vault
```

**Output:**
```
NAME                                    READY   STATUS    RESTARTS   AGE
vault-0                                 1/1     Running   0          5m
vault-agent-injector-7d97cf5cf4-rr4hz   1/1     Running   0          5m
```

### 3.3 Vault Configuration
Inside the Vault pod, the following configuration was performed:

```bash
# Enable KV secrets engine (v2)
vault secrets enable -path=secret kv-v2

# Create a secret
vault kv put secret/myapp/config username="db_user" password="db_password" ttl="30s"

# Enable Kubernetes authentication
vault auth enable kubernetes

# Configure Kubernetes auth
vault write auth/kubernetes/config \
    kubernetes_host="https://kubernetes.default.svc.cluster.local:443"

# Create a policy for read access
vault policy write myapp-policy - <<EOF
path "secret/data/myapp/*" {
  capabilities = ["read"]
}
EOF

# Create a role bound to the default ServiceAccount
vault write auth/kubernetes/role/myapp-role \
    bound_service_account_names=default \
    bound_service_account_namespaces=default \
    policies=myapp-policy \
    ttl=24h
```

### 3.4 Vault Agent Injection
A test deployment was created with annotations to enable Vault Agent injection:

```yaml
annotations:
  vault.hashicorp.com/agent-inject: "true"
  vault.hashicorp.com/role: "myapp-role"
  vault.hashicorp.com/agent-inject-secret-config: "secret/data/myapp/config"
```

### 3.5 Verification of Secret Injection
The secret was successfully injected and available at `/vault/secrets/config`:

```bash
kubectl exec -it <vault-demo-pod> -c app -- cat /vault/secrets/config
```

**Output:**
```
data: map[password:db_password ttl:30s username:db_user]
```

### 3.6 Sidecar Injection Pattern Explained
The Vault Agent runs as a **sidecar container** alongside the application container. It:
1. Authenticates with Vault using Kubernetes ServiceAccount.
2. Retrieves the requested secrets.
3. Writes them to a shared emptyDir volume.
4. The main application reads secrets from that volume.

This pattern keeps secrets out of environment variables and provides automatic rotation.

---

## Task 4 — Documentation (2 pts)

Complete documentation has been created in `k8s/SECRETS.md`, including:
- All command outputs and verification steps
- Explanation of base64 encoding vs. encryption
- Helm chart structure and resource limits
- Vault installation and configuration details
- Security analysis comparing Kubernetes Secrets and Vault

---

## Security Analysis

| Feature | Kubernetes Secrets | HashiCorp Vault |
|---------|--------------------|-----------------|
| Encryption at rest | Optional (requires configuration) | Yes (by default) |
| Audit logging | Limited | Comprehensive |
| Dynamic secrets | No | Yes |
| Secret rotation | Manual | Automatic |
| Centralized management | No | Yes |
| Access control | RBAC | Fine-grained policies + RBAC |

### Production Recommendations
1. **Use Vault for critical secrets** (API tokens, database passwords, encryption keys)
2. **Enable Encryption at Rest** for Kubernetes Secrets if used
3. **Use Vault CSI Driver** instead of sidecar injection when possible
4. **Regularly rotate secrets** and encryption keys
5. **Audit all secret access** in production environments

---

## Bonus — Vault Agent Templates (2.5 pts)

### Template Annotation Implementation
A template annotation was added to render secrets in `.env` format:

```yaml
annotations:
  vault.hashicorp.com/agent-inject-template-config: |
    {{- with secret "secret/data/myapp/config" -}}
    DATABASE_USER={{ .Data.data.username }}
    DATABASE_PASSWORD={{ .Data.data.password }}
    CONNECTION_TTL={{ .Data.data.ttl }}
    {{- end }}
```

### Rendered Output
```bash
$ kubectl exec -it <pod> -c app -- cat /vault/secrets/config
DATABASE_USER=db_user
DATABASE_PASSWORD=db_password
CONNECTION_TTL=30s
```

### Named Templates in `_helpers.tpl`
A named template was created to follow the DRY principle:

```yaml
{{- define "vault.injector.annotations" -}}
vault.hashicorp.com/agent-inject: "true"
vault.hashicorp.com/role: {{ .Values.vault.role }}
vault.hashicorp.com/agent-inject-secret-config: {{ .Values.vault.secretPath }}
vault.hashicorp.com/agent-inject-template-config: |
  {{- with secret {{ .Values.vault.secretPath | quote }} -}}
  {{- range $key, $value := .Data.data }}
  {{ $key | upper }}={{ $value }}
  {{- end }}
  {{- end }}
{{- end }}
```

This template can be reused across multiple deployments, ensuring consistency and reducing duplication.

---

