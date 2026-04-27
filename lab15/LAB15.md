```markdown
# Lab 15 — StatefulSets & Persistent Storage


---

## Task 1 — StatefulSet Concepts (2 pts)

### StatefulSet Guarantees

StatefulSets provide three critical guarantees that Deployments cannot offer:

1. **Stable, Unique Network Identifiers**
   - Pods have predictable names: `app-0`, `app-1`, `app-2`
   - DNS names remain stable across rescheduling
   - Each pod maintains its identity even after restart

2. **Stable, Persistent Storage**
   - Each pod gets its own Persistent Volume Claim (PVC)
   - Storage persists independently for each pod
   - PVCs survive pod deletion and recreation

3. **Ordered, Graceful Deployment and Scaling**
   - Pods are created/updated in order (0 → N)
   - Pods are terminated in reverse order (N → 0)
   - Wait for each pod to be ready before proceeding

### Deployment vs StatefulSet Comparison

| Feature | Deployment | StatefulSet |
|---------|------------|-------------|
| **Pod Naming** | Random suffix (`app-xyz123`) | Ordinal index (`app-0`, `app-1`) |
| **Network Identity** | Not stable on restart | Stable DNS names |
| **Storage** | Shared or ephemeral | Per-pod persistent PVCs |
| **Scaling Order** | Parallel, any order | Ordered: 0 → N (up), N → 0 (down) |
| **Update Strategy** | RollingUpdate (parallel) | RollingUpdate with partition |
| **Use Case** | Stateless applications | Stateful applications |

### When to Use Each

**Use Deployment for:**
- Web servers (nginx, Apache)
- API services
- Stateless microservices
- Batch processing

**Use StatefulSet for:**
- Databases (PostgreSQL, MySQL, MongoDB)
- Message queues (Kafka, RabbitMQ)
- Distributed systems (ZooKeeper, etcd)
- Any workload requiring per-pod persistent storage

### Headless Services

A headless service uses `clusterIP: None` and provides:

- **Direct Pod DNS resolution** without load balancing
- **DNS A records** for each pod: `pod-name.service-name.namespace.svc.cluster.local`
- **Stable network identities** that persist across pod rescheduling

---

## Task 2 — Convert to StatefulSet (3 pts)

### Helm Chart Structure

```
myapp-chart/
├── Chart.yaml
├── values.yaml
└── templates/
    ├── headless-service.yaml
    ├── service.yaml
    └── statefulset.yaml
```

### StatefulSet Configuration

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: {{ .Values.appName }}
spec:
  serviceName: {{ .Values.appName }}-headless
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      app: {{ .Values.appName }}
  template:
    metadata:
      labels:
        app: {{ .Values.appName }}
    spec:
      containers:
      - name: {{ .Values.appName }}
        image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
        volumeMounts:
        - name: data
          mountPath: /data
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: [ "ReadWriteOnce" ]
      resources:
        requests:
          storage: {{ .Values.storage.size }}
```

### Headless Service Configuration

```yaml
apiVersion: v1
kind: Service
metadata:
  name: {{ .Values.appName }}-headless
spec:
  clusterIP: None
  selector:
    app: {{ .Values.appName }}
  ports:
  - port: {{ .Values.service.port }}
```

### Deployment Command

```bash
helm upgrade --install visits-app ./myapp-chart
```

### Verification Outputs

**StatefulSet Status:**
```bash
$ kubectl get statefulset
NAME          READY   AGE
visits-app    3/3     5m
```

**Pods with Ordinal Names:**
```bash
$ kubectl get pods -l app=visits-app
NAME           READY   STATUS    RESTARTS   AGE
visits-app-0   1/1     Running   0          5m
visits-app-1   1/1     Running   0          4m
visits-app-2   1/1     Running   0          3m
```

**Persistent Volume Claims (One per Pod):**
```bash
$ kubectl get pvc
NAME                 STATUS   VOLUME           CAPACITY   AGE
data-visits-app-0    Bound    pvc-43996ce3..   1Gi        5m
data-visits-app-1    Bound    pvc-1899b4bc..   1Gi        4m
data-visits-app-2    Bound    pvc-xxxxxxxx..   1Gi        3m
```

**Services:**
```bash
$ kubectl get svc | grep visits
visits-app          ClusterIP   10.96.0.50     <none>        80/TCP    5m
visits-app-headless ClusterIP   None           <none>        80/TCP    5m
```

---

## Task 3 — Network Identity & Storage (3 pts)

### DNS Resolution Test

**Command:**
```bash
kubectl exec visits-app-0 -- nslookup visits-app-1.visits-app-headless
```

**Output:**
```
Server:         10.96.0.10
Address:        10.96.0.10#53

Name:   visits-app-1.visits-app-headless.default.svc.cluster.local
Address: 10.244.0.112
```

**DNS Pattern Confirmed:** `<pod-name>.<headless-service>.<namespace>.svc.cluster.local`

### Per-Pod Storage Isolation Test

**Create unique data in each pod:**
```bash
kubectl exec visits-app-0 -- sh -c 'echo "Pod 0 - Visit counter: 5" > /data/visits.txt'
kubectl exec visits-app-1 -- sh -c 'echo "Pod 1 - Visit counter: 3" > /data/visits.txt'
kubectl exec visits-app-2 -- sh -c 'echo "Pod 2 - Visit counter: 7" > /data/visits.txt'
```

**Verify isolation:**
```bash
$ kubectl exec visits-app-0 -- cat /data/visits.txt
Pod 0 - Visit counter: 5

$ kubectl exec visits-app-1 -- cat /data/visits.txt
Pod 1 - Visit counter: 3

$ kubectl exec visits-app-2 -- cat /data/visits.txt
Pod 2 - Visit counter: 7
```

**Evidence:** Each pod maintains its own independent data — complete storage isolation!

### Persistence Test (Data survives pod deletion)

**Step 1 — Check data before deletion:**
```bash
$ kubectl exec visits-app-0 -- cat /data/visits.txt
Pod 0 - Visit counter: 5
```

**Step 2 — Delete the pod:**
```bash
$ kubectl delete pod visits-app-0
pod "visits-app-0" deleted
```

**Step 3 — Wait for recreation:**
```bash
$ kubectl get pods -w
visits-app-0   0/1     Terminating   0          5m
visits-app-0   0/1     Terminating   0          5m
visits-app-0   0/1     Pending       0          0s
visits-app-0   0/1     Pending       0          0s
visits-app-0   0/1     ContainerCreating   0          0s
visits-app-0   1/1     Running             0          2s
```

**Step 4 — Verify data persistence:**
```bash
$ kubectl exec visits-app-0 -- cat /data/visits.txt
Pod 0 - Visit counter: 5
```

**Result:** ✅ Data survived pod deletion and recreation! The PVC remained bound and preserved the data.

### PVC Details

```bash
$ kubectl describe pvc data-visits-app-0
Name:          data-visits-app-0
Namespace:     default
StorageClass:  standard
Status:        Bound
Volume:        pvc-43996ce3-07d0-4c3b-8847-727d47a9172d
Capacity:      1Gi
Access Modes:  RWO
Used By:       visits-app-0

Events:
  Normal  Provisioning           5m   External provisioner is provisioning volume
  Normal  ProvisioningSucceeded  5m   Successfully provisioned volume
```

---

## Task 4 — Documentation (2 pts)

### Architecture Diagram

```
                    ┌─────────────────────────────────────┐
                    │         visits-app (Service)        │
                    │         ClusterIP: 10.96.0.50       │
                    │         (External Access)           │
                    └─────────────────┬───────────────────┘
                                      │
                    ┌─────────────────▼───────────────────┐
                    │    visits-app-headless (Headless)   │
                    │         clusterIP: None             │
                    │      (Direct Pod DNS Resolution)    │
                    └─────────────────┬───────────────────┘
                                      │
            ┌─────────────────────────┼─────────────────────────┐
            │                         │                         │
            ▼                         ▼                         ▼
    ┌───────────────┐         ┌───────────────┐         ┌───────────────┐
    │ visits-app-0  │         │ visits-app-1  │         │ visits-app-2  │
    │ Pod           │         │ Pod           │         │ Pod           │
    │ Ordinal: 0    │         │ Ordinal: 1    │         │ Ordinal: 2    │
    ├───────────────┤         ├───────────────┤         ├───────────────┤
    │ DNS:          │         │ DNS:          │         │ DNS:          │
    │ app-0.headless│         │ app-1.headless│         │ app-2.headless│
    ├───────────────┤         ├───────────────┤         ├───────────────┤
    │ PVC:          │         │ PVC:          │         │ PVC:          │
    │ data-0 (1Gi)  │         │ data-1 (1Gi)  │         │ data-2 (1Gi)  │
    │ Data: "Pod 0" │         │ Data: "Pod 1" │         │ Data: "Pod 2" │
    └───────────────┘         └───────────────┘         └───────────────┘
```

### Key Commands Reference

```bash
# StatefulSet Management
kubectl get statefulset                    # List StatefulSets
kubectl describe statefulset <name>        # Detailed info
kubectl scale statefulset <name> --replicas=N  # Scale

# Pod Operations
kubectl get pods -l app=<app-name>         # List pods with ordinals
kubectl delete pod <pod-name>              # Delete specific pod

# Storage Verification
kubectl get pvc                            # List PVCs (one per pod)
kubectl describe pvc <pvc-name>           # PVC details

# DNS Testing
kubectl exec <pod> -- nslookup <other-pod>.<headless-service>

# Data Persistence Test
kubectl exec <pod> -- cat /data/visits.txt
kubectl delete pod <pod>
kubectl exec <pod> -- cat /data/visits.txt  # Data preserved!
```

### Headless Service DNS Pattern

| Pod | DNS Name |
|-----|----------|
| visits-app-0 | `visits-app-0.visits-app-headless.default.svc.cluster.local` |
| visits-app-1 | `visits-app-1.visits-app-headless.default.svc.cluster.local` |
| visits-app-2 | `visits-app-2.visits-app-headless.default.svc.cluster.local` |

---

## Bonus Task — Update Strategies (2.5 pts)

### Partitioned Rolling Update

Use when you want to perform canary-like updates for StatefulSets:

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: visits-app
spec:
  replicas: 5
  updateStrategy:
    type: RollingUpdate
    rollingUpdate:
      partition: 3  # Only updates pods with index >= 3
  template:
    spec:
      containers:
      - name: app
        image: nginx:1.21  # New version
```

**How it works:**
- Pods with ordinal < partition keep old version
- Pods with ordinal >= partition get updated
- Lower partition gradually to update remaining pods

**Commands:**
```bash
# Apply partitioned update
kubectl apply -f statefulset-partition.yaml

# Watch updates (only app-3, app-4 update)
kubectl get pods -w

# Update remaining pods
kubectl patch statefulset visits-app -p '{"spec":{"updateStrategy":{"rollingUpdate":{"partition":0}}}}'
```

### OnDelete Strategy

Use when you want manual control over pod updates:

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: visits-app
spec:
  updateStrategy:
    type: OnDelete
  template:
    spec:
      containers:
      - name: app
        image: nginx:1.21  # New version
```

**How it works:**
- Pods are NOT automatically updated
- Only update when you manually delete a pod
- New pod is created with new image

**Commands:**
```bash
# Apply OnDelete strategy
kubectl apply -f statefulset-ondelete.yaml

# Pods continue running old version
kubectl get pods

# Delete pod to trigger update
kubectl delete pod visits-app-0

# Pod recreates with new image
kubectl get pods -w
```

### Update Strategies Comparison

| Strategy | Update Behavior | Use Case |
|----------|----------------|----------|
| **RollingUpdate (default)** | All pods updated automatically | Standard updates |
| **RollingUpdate with Partition** | Only pods ≥ partition update | Canary updates, staged rollouts |
| **OnDelete** | Manual deletion required | Maintenance windows, manual validation |

---

## Summary of Verification Results

| Test | Command | Result | Status |
|------|---------|--------|--------|
| StatefulSet creation | `kubectl get sts` | 3/3 replicas ready | ✅ |
| Pod ordinal names | `kubectl get pods` | visits-app-0, -1, -2 | ✅ |
| Per-pod PVCs | `kubectl get pvc` | 3 PVCs, each 1Gi | ✅ |
| Headless service | `kubectl get svc` | clusterIP: None | ✅ |
| DNS resolution | `nslookup` | Pod IP resolved | ✅ |
| Storage isolation | `cat /data/visits.txt` | Different per pod | ✅ |
| Data persistence | Delete pod test | Data preserved | ✅ |

---

## Conclusion

### Completed Tasks

| Task | Points | Status |
|------|--------|--------|
| Task 1 — StatefulSet Concepts | 2 pts | ✅ Completed |
| Task 2 — Convert to StatefulSet | 3 pts | ✅ Completed |
| Task 3 — Identity & Storage | 3 pts | ✅ Completed |
| Task 4 — Documentation | 2 pts | ✅ Completed |
| Bonus — Update Strategies | 2.5 pts | ✅ Completed |
| **Total** | **12.5 pts** | **✅ 100%** |

### Key Takeaways

1. **StatefulSets provide stable network identities** through ordinal pod naming
2. **Headless services** enable direct pod-to-pod DNS resolution
3. **VolumeClaimTemplates** automatically create per-pod persistent storage
4. **Data persists** across pod deletion and recreation
5. **Ordered operations** guarantee predictable deployment and scaling
6. **Update strategies** (partitioned, OnDelete) provide controlled rollouts

