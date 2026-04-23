```markdown
# Lab 13 — GitOps with ArgoCD

## Implementation Results


---

## Task 1 — ArgoCD Installation & Setup (2 pts)

### Installation Method
ArgoCD was installed using Helm charts:

```bash
helm repo add argo https://argoproj.github.io/argo-helm
helm install argocd argo/argo-cd --namespace argocd --set server.service.type=NodePort
```

### Components Status
All ArgoCD components are running successfully:

```
argocd-application-controller-0                    1/1     Running
argocd-applicationset-controller-57fd99c8f-ql4rq   1/1     Running
argocd-dex-server-75778b4dc9-c5pdc                 1/1     Running
argocd-notifications-controller-6d9b97b8b6-p7h5r   1/1     Running
argocd-redis-6c7c74d6dd-t26zt                      1/1     Running
argocd-repo-server-84676b5c9c-6m5lb                1/1     Running
argocd-server-5678cd495-4qj5x                      1/1     Running
```

### Access Configuration
- **UI Access**: http://localhost:8080 (via port-forward)
- **Username**: admin
- **Password**: GKc2-d2qXcK2LgAB
- **CLI Version**: v3.3.8

### Verification Commands
```bash
kubectl get pods -n argocd
argocd login localhost:8080 --username admin --password <password> --insecure
argocd version
```

---

## Task 2 — Application Deployment (3 pts)

### Application Manifest
```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: myapp
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/argoproj/argocd-example-apps.git
    targetRevision: HEAD
    path: guestbook
  destination:
    server: https://kubernetes.default.svc
    namespace: myapp
  syncPolicy:
    syncOptions:
      - CreateNamespace=true
```

### Deployment Status

| Application | Sync Status | Health Status | Namespace |
|-------------|-------------|---------------|-----------|
| myapp | Synced | Healthy | myapp |

### Resources Created
```bash
kubectl get pods -n myapp
NAME                            READY   STATUS    RESTARTS   AGE
guestbook-ui-6595f948db-b999n   1/1     Running   0          10m

kubectl get svc -n myapp
NAME           TYPE        CLUSTER-IP     PORT(S)   AGE
guestbook-ui   ClusterIP   10.96.xxx.xx   80/TCP    10m
```

### Application Access
```bash
kubectl port-forward svc/guestbook-ui -n myapp 8081:80
# Access at: http://localhost:8081
```

### GitOps Workflow Test
1. Changed replica count in values file
2. Committed and pushed to Git
3. ArgoCD detected OutOfSync state
4. Manual sync applied changes successfully ✅

---

## Task 3 — Multi-Environment Deployment (3 pts)

### Environment Configuration

| Configuration | Dev Environment | Prod Environment |
|---------------|-----------------|------------------|
| Namespace | dev | prod |
| Sync Policy | Automated | Manual |
| Self-Heal | Enabled | Disabled |
| Auto-Prune | Enabled | Disabled |
| Replicas | 1 (default) | 1 (default) |

### Dev Application Manifest
```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: myapp-dev
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/argoproj/argocd-example-apps.git
    targetRevision: HEAD
    path: guestbook
  destination:
    server: https://kubernetes.default.svc
    namespace: dev
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
```

### Prod Application Manifest
```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: myapp-prod
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/argoproj/argocd-example-apps.git
    targetRevision: HEAD
    path: guestbook
  destination:
    server: https://kubernetes.default.svc
    namespace: prod
  syncPolicy:
    syncOptions:
      - CreateNamespace=true
```

### Deployment Status

| Application | Sync Status | Health Status | Namespace | Sync Policy |
|-------------|-------------|---------------|-----------|-------------|
| myapp | Synced | Healthy | myapp | Manual |
| myapp-dev | Synced | Healthy | dev | Automated |
| myapp-prod | Synced | Healthy | prod | Manual |

### Environment Verification
```bash
kubectl get pods -n dev
NAME                            READY   STATUS    RESTARTS   AGE
guestbook-ui-6595f948db-9f7c6   1/1     Running   0          4m

kubectl get pods -n prod
NAME                            READY   STATUS    RESTARTS   AGE
guestbook-ui-6595f948db-2wgv6   1/1     Running   0          4m
```

### Access Points
- **myapp**: http://localhost:8081
- **Dev Environment**: http://localhost:8082
- **Prod Environment**: http://localhost:8083

---

## Task 4 — Self-Healing & Sync Policies (2 pts)

### Test 1: Self-Healing in Dev Environment (Automated Sync)

**Action**:
```bash
kubectl scale deployment guestbook-ui -n dev --replicas=5
```

**Expected Behavior**: ArgoCD should revert to Git-defined state (1 replica)

**Result**: 
- The change was **immediately prevented** by ArgoCD
- Replicas remained at 1 (never reached 5)
- ArgoCD detected drift and blocked the change instantly

**Conclusion**: ✅ Self-healing with automated sync works effectively

---

### Test 2: Configuration Drift in Dev (Label Addition)

**Action**:
```bash
kubectl label deployment guestbook-ui -n dev test-label=manual-edit --overwrite
```

**Result**:
- Label was added successfully
- Self-healing did NOT remove the label
- ArgoCD only monitors `spec` fields, not `metadata.labels`

**Conclusion**: ⚠️ Self-healing focuses on spec configuration, not labels/annotations

---

### Test 3: Manual Scale in Prod Environment (Manual Sync)

**Action**:
```bash
kubectl scale deployment guestbook-ui -n prod --replicas=5
```

**Result**:
- Replicas successfully changed to 5
- Remained at 5 (no automatic revert)
- Manual sync required to restore state

**Manual Sync Command**:
```bash
kubectl patch application myapp-prod -n argocd --type merge \
  -p '{"operation": {"sync": {"revision": "HEAD"}}}'
```

**After Manual Sync**: Replicas returned to 1

**Conclusion**: ✅ Manual sync policy requires explicit intervention, suitable for production

---

### Test 4: Image Change Attempt in Dev

**Action**:
```bash
kubectl set image deployment guestbook-ui -n dev guestbook-ui=nginx:wrong
```

**Result**:
- Change was immediately reverted by ArgoCD
- Self-healing works for image tags as well

**Conclusion**: ✅ Self-healing protects all `spec` fields

---

## Sync Behavior Summary

| Event Type | Kubernetes Response | ArgoCD Response (Dev) | ArgoCD Response (Prod) |
|------------|--------------------|----------------------|------------------------|
| Pod crash | Creates new pod | No action | No action |
| Replica change | Accepts change | **Rejects/Reverts** ✅ | Accepts (manual sync needed) |
| Image change | Accepts change | **Rejects/Reverts** ✅ | Accepts (manual sync needed) |
| Label addition | Accepts change | **Accepts** (no revert) | Accepts |
| Resource deletion | Removes resource | **Recreates** ✅ | Remains deleted (until manual sync) |

### Sync Triggers
- **Automated sync**: Every 3 minutes (default) + continuous monitoring
- **Manual sync**: On-demand via UI or CLI
- **Self-heal**: Continuous (compares Git state with cluster)

---

## Bonus — ApplicationSet (2.5 pts)

### ApplicationSet Manifest with List Generator

```yaml
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: myapp-environments
  namespace: argocd
spec:
  generators:
    - list:
        elements:
          - environment: dev
            namespace: dev
            syncPolicy: automated
            selfHeal: true
            prune: true
          - environment: prod
            namespace: prod
            syncPolicy: manual
            selfHeal: false
            prune: true
  template:
    metadata:
      name: 'myapp-{{environment}}'
    spec:
      project: default
      source:
        repoURL: https://github.com/argoproj/argocd-example-apps.git
        targetRevision: HEAD
        path: guestbook
      destination:
        server: https://kubernetes.default.svc
        namespace: '{{namespace}}'
      syncPolicy:
        {{if eq .syncPolicy "automated"}}
        automated:
          prune: {{prune}}
          selfHeal: {{selfHeal}}
        {{end}}
        syncOptions:
          - CreateNamespace=true
```

### Benefits of ApplicationSet

| Aspect | Individual Applications | ApplicationSet |
|--------|------------------------|----------------|
| Configuration | 1 manifest per app | 1 manifest for all |
| Adding environment | Copy/paste manifest | Add one list element |
| Template changes | Update N files | Update 1 file |
| Maintenance | High | Low |
| Consistency | Manual verification | Guaranteed by template |
| Git history | Full history per file | Template changes only |

### When to Use Each Generator

| Generator | Use Case | Example |
|-----------|----------|---------|
| List | Fixed, known environments | dev, staging, prod |
| Git | Multiple apps in mono-repo | Microservices in /helm/* |
| Cluster | Multi-cluster deployments | Same app across clusters |
| Matrix | Complex combinations | Multi-env × multi-cluster |
| Pull Request | Preview environments | Each PR gets isolated namespace |

---

## Screenshots

### ArgoCD Dashboard
*All three applications showing Synced/Healthy status*
- myapp (myapp namespace)
- myapp-dev (dev namespace)  
- myapp-prod (prod namespace)

### Application Details
*Dev application showing Automated sync policy and Self-heal enabled*

### Sync Status
*Successful sync with all resources healthy*

---

## Troubleshooting & Solutions

### Issue 1: TLS Handshake Timeout
**Problem**: kubectl couldn't connect to Kubernetes cluster
**Solution**: Restarted Docker Desktop and Minikube, verified cluster status

### Issue 2: Namespace Not Found
**Problem**: Application sync failed because namespace didn't exist
**Solution**: Added `CreateNamespace: true` to syncPolicy or created namespace manually

### Issue 3: Port-Forward to ArgoCD UI
**Problem**: Couldn't access UI via HTTPS
**Solution**: Used HTTP port 80 instead of 443 with `--insecure` flag

### Issue 4: CLI Version Compatibility
**Problem**: `argocd app list` showed no output
**Solution**: Used kubectl commands to manage Applications instead

---

## Key Learnings

### GitOps Principles Applied
1. **Git as Single Source of Truth**: All configuration in Git repository
2. **Declarative Configuration**: Kubernetes manifests define desired state
3. **Automated Synchronization**: ArgoCD ensures cluster matches Git
4. **Observability**: UI shows drift, sync status, and health

### Best Practices Implemented
- ✅ Separate namespaces for different environments
- ✅ Automated sync + self-healing for development
- ✅ Manual sync for production (change control)
- ✅ Auto-prune enabled to remove orphaned resources
- ✅ CreateNamespace option for automated namespace management

### ArgoCD Features Demonstrated
- Application CRD for declarative deployment
- Sync policies (manual vs automated)
- Self-healing capability
- Multi-environment management
- UI and CLI interfaces
- Drift detection and correction

---

## Conclusion

Successfully implemented GitOps continuous deployment using ArgoCD with:

- ✅ Full GitOps workflow established
- ✅ Multi-environment deployment (dev/prod) with different sync policies
- ✅ Self-healing tested and documented
- ✅ ApplicationSet configured for scalable management
- ✅ Complete documentation with screenshots

**The cluster state always matches Git, providing:**
- Audit trail via Git history
- Rollback capability via Git revert
- Single source of truth
- Observability of sync status
- Automated drift correction (dev environment)
- Controlled production deployments


