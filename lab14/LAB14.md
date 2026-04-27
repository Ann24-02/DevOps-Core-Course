```markdown
# Lab 14 — Progressive Delivery with Argo Rollouts


---

## Task 1 — Argo Rollouts Fundamentals (2 pts)

### Installation

```bash
# Create namespace
kubectl create namespace argo-rollouts

# Install Argo Rollouts controller
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml
```

**CRDs Created:**
```
analysisruns.argoproj.io created
analysistemplates.argoproj.io created
clusteranalysistemplates.argoproj.io created
experiments.argoproj.io created
rollouts.argoproj.io created
```

### Verify Controller is Running

```bash
kubectl get pods -n argo-rollouts
```

**Output:**
```
NAME                            READY   STATUS    RESTARTS   AGE
argo-rollouts-5f64f8d68-7rmqf   1/1     Running   0          5m
```

### Install kubectl Plugin

```bash
brew install argoproj/tap/kubectl-argo-rollouts
kubectl argo rollouts version
```

### Rollout vs Deployment Comparison

| Feature | Deployment | Rollout |
|---------|------------|---------|
| **Strategy Types** | RollingUpdate, Recreate | Canary, Blue-Green, Experiment |
| **Traffic Control** | Based on replica count | Weight-based traffic splitting |
| **Pause/Resume** | Manual only | Automated or manual pauses |
| **Metrics Analysis** | Not available | Prometheus/Datadog integration |
| **Rollback Speed** | Gradual (revision-based) | Instant traffic switch |
| **Preview Environment** | Manual setup | Native preview service |

---

## Task 2 — Canary Deployment (3 pts)

### Canary Strategy Configuration

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: canary-demo
  namespace: canary-test
spec:
  replicas: 5
  selector:
    matchLabels:
      app: canary-demo
  template:
    metadata:
      labels:
        app: canary-demo
    spec:
      containers:
      - name: app
        image: nginx:1.20
        ports:
        - containerPort: 80
  strategy:
    canary:
      steps:
      - setWeight: 20
      - pause: {}                # manual approval
      - setWeight: 40
      - pause: {duration: 30}
      - setWeight: 60
      - pause: {duration: 30}
      - setWeight: 80
      - pause: {duration: 30}
      - setWeight: 100
```

### Create Canary Rollout

```bash
# Create namespace
kubectl create namespace canary-test

# Apply rollout configuration
kubectl apply -f canary-rollout.yaml

# Create service
kubectl apply -f canary-service.yaml
```

### Initial Healthy State

```bash
kubectl argo rollouts get rollout canary-demo -n canary-test
```

**Output:**
```
Name:            canary-demo
Namespace:       canary-test
Status:          ✔ Healthy
Strategy:        Canary
  Step:          9/9
  SetWeight:     100
  ActualWeight:  100
Images:          nginx:1.20 (stable)
Replicas:
  Desired:       5
  Current:       5
  Updated:       5
  Ready:         5
  Available:     5

NAME                                     KIND        STATUS     AGE  INFO
⟳ canary-demo                            Rollout     ✔ Healthy  35s  
└──# revision:1                                                      
   └──⧉ canary-demo-657d4f5c77           ReplicaSet  ✔ Healthy  35s  stable
      ├──□ canary-demo-657d4f5c77-bfc2k  Pod         ✔ Running  35s  ready:1/1
      ├──□ canary-demo-657d4f5c77-kt49n  Pod         ✔ Running  35s  ready:1/1
      ├──□ canary-demo-657d4f5c77-rjgb4  Pod         ✔ Running  35s  ready:1/1
      ├──□ canary-demo-657d4f5c77-sfhdt  Pod         ✔ Running  35s  ready:1/1
      └──□ canary-demo-657d4f5c77-vbffj  Pod         ✔ Running  35s  ready:1/1
```

### Trigger Canary Update

```bash
kubectl argo rollouts set image canary-demo -n canary-test app=nginx:1.21
```

### Canary in Progress (20% Traffic)

```
Name:            canary-demo
Namespace:       canary-test
Status:          ॥ Paused
Message:         CanaryPauseStep
Strategy:        Canary
  Step:          1/9
  SetWeight:     20
  ActualWeight:  20
Images:          nginx:1.20 (stable)
                 nginx:1.21 (canary)
Replicas:
  Desired:       5
  Current:       5
  Updated:       1
  Ready:         5
  Available:     5

NAME                                     KIND        STATUS     AGE    INFO
⟳ canary-demo                            Rollout     ॥ Paused   7m23s  
├──# revision:2                                                        
│  └──⧉ canary-demo-b6f594546            ReplicaSet  ✔ Healthy  6m34s  canary
│     └──□ canary-demo-b6f594546-zfmn2   Pod         ✔ Running  5s     ready:1/1
└──# revision:1                                                        
   └──⧉ canary-demo-657d4f5c77           ReplicaSet  ✔ Healthy  7m23s  stable
      ├──□ canary-demo-657d4f5c77-bfc2k  Pod         ✔ Running  7m23s  ready:1/1
      ├──□ canary-demo-657d4f5c77-rjgb4  Pod         ✔ Running  7m23s  ready:1/1
      ├──□ canary-demo-657d4f5c77-hdqcj  Pod         ✔ Running  5m23s  ready:1/1
      └──□ canary-demo-657d4f5c77-rvv6z  Pod         ✔ Running  5m23s  ready:1/1
```

### Promote Canary

```bash
kubectl argo rollouts promote canary-demo -n canary-test
```

**Result:**
```
rollout 'canary-demo' promoted
```

### Canary at 40% Traffic

```
Name:            canary-demo
Status:          ॥ Paused
Step:            3/9
SetWeight:       40
ActualWeight:    40
```

### Abort and Retry Demonstration

```bash
# Abort during canary
kubectl argo rollouts abort canary-demo -n canary-test
```

**After Abort:**
```
Name:            canary-demo
Status:          ✖ Degraded
Message:         RolloutAborted: Rollout aborted update to revision 2
Strategy:        Canary
  Step:          0/9
  SetWeight:     0
  ActualWeight:  0
Images:          nginx:1.20 (stable)
```

```bash
# Retry after abort
kubectl argo rollouts retry rollout canary-demo -n canary-test
```

**Result:**
```
rollout 'canary-demo' retried
Status:          ॥ Paused
Step:            1/9
SetWeight:       20
ActualWeight:    20
```

### Canary Steps Summary

| Step | Traffic Weight | Action |
|------|---------------|--------|
| 1 | 20% | Manual promotion required |
| 2 | 40% | Auto pause 30 seconds |
| 3 | 60% | Auto pause 30 seconds |
| 4 | 80% | Auto pause 30 seconds |
| 5 | 100% | Full deployment |

---

## Task 3 — Blue-Green Deployment (3 pts)

### Blue-Green Strategy Configuration

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: bluegreen-demo
  namespace: bluegreen-test
spec:
  replicas: 3
  selector:
    matchLabels:
      app: bluegreen-demo
  template:
    metadata:
      labels:
        app: bluegreen-demo
    spec:
      containers:
      - name: app
        image: nginx:1.20
        ports:
        - containerPort: 80
  strategy:
    blueGreen:
      activeService: bluegreen-active
      previewService: bluegreen-preview
      autoPromotionEnabled: false
      scaleDownDelaySeconds: 30
```

### Create Blue-Green Components

```bash
# Create namespace
kubectl create namespace bluegreen-test

# Apply rollout configuration
kubectl apply -f bluegreen-rollout.yaml

# Create services
kubectl apply -f bluegreen-services.yaml
```

### Services Created

```bash
kubectl get svc -n bluegreen-test
```

**Output:**
```
NAME                TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)   AGE
bluegreen-active    ClusterIP   10.105.169.9     <none>        80/TCP    62s
bluegreen-preview   ClusterIP   10.109.237.195   <none>        80/TCP    62s
```

### Initial State (Blue Active)

```bash
kubectl argo rollouts get rollout bluegreen-demo -n bluegreen-test
```

**Output:**
```
Name:            bluegreen-demo
Namespace:       bluegreen-test
Status:          ✔ Healthy
Strategy:        BlueGreen
Images:          nginx:1.20 (stable, active)
Replicas:
  Desired:       3
  Current:       3
  Ready:         3
```

### Trigger Blue-Green Update

```bash
kubectl argo rollouts set image bluegreen-demo -n bluegreen-test app=nginx:1.21
```

### Status After Green Created (Preview Active)

```
Name:            bluegreen-demo
Status:          ॥ Paused
Message:         BlueGreenPause
Images:          nginx:1.20 (stable, active)
                 nginx:1.21 (preview)
Replicas:
  Desired:       3
  Current:       6      # 3 blue + 3 green
  Updated:       3      # green replicas
```

### Promote Green to Active

```bash
kubectl argo rollouts promote bluegreen-demo -n bluegreen-test
```

**Result:**
```
rollout 'bluegreen-demo' promoted
```

### After Promotion (Green Active)

```
Name:            bluegreen-demo
Status:          ✔ Healthy
Images:          nginx:1.21 (stable, active)
                 nginx:1.20
Replicas:
  Desired:       3
  Current:       6
  Updated:       3
  Ready:         6

NAME                                        KIND        STATUS     AGE  INFO
⟳ bluegreen-demo                            Rollout     ✔ Healthy  53s  
├──# revision:3                                                         
│  └──⧉ bluegreen-demo-bbddd48d             ReplicaSet  ✔ Healthy  45s  stable,active
│     ├──□ bluegreen-demo-bbddd48d-6q9hf    Pod         ✔ Running  37s  ready:1/1
│     ├──□ bluegreen-demo-bbddd48d-k64t4    Pod         ✔ Running  37s  ready:1/1
│     └──□ bluegreen-demo-bbddd48d-x7fgb    Pod         ✔ Running  37s  ready:1/1
└──# revision:2                                                         
   └──⧉ bluegreen-demo-6b975dcb75           ReplicaSet  ✔ Healthy  34s  delay:12s
      ├──□ bluegreen-demo-6b975dcb75-9phqz  Pod         ✔ Running  34s  ready:1/1
      ├──□ bluegreen-demo-6b975dcb75-vrdjf  Pod         ✔ Running  34s  ready:1/1
      └──□ bluegreen-demo-6b975dcb75-wqg9f  Pod         ✔ Running  34s  ready:1/1
```

### Instant Rollback (Undo)

```bash
kubectl argo rollouts undo bluegreen-demo -n bluegreen-test
```

**Result:**
```
rollout 'bluegreen-demo' undo
```

**After Rollback:**
```
Name:            bluegreen-demo
Status:          ✔ Healthy
Images:          nginx:1.20 (stable, active)
                 nginx:1.21
```

---

## Task 4 — Strategy Comparison and Documentation

### Canary vs Blue-Green Comparison Table

| Feature | Canary | Blue-Green |
|---------|--------|------------|
| **Traffic Switching** | Gradual (20→40→60→80→100%) | Instant (0→100%) |
| **Rollback Speed** | Gradual (reverse traffic shift) | Instant (selector change) |
| **Preview Environment** | No | Yes (preview service) |
| **User Impact** | Gradual exposure | All users at once |
| **Resource Usage** | Same during update | Double during validation |
| **Setup Complexity** | Medium | Low |
| **A/B Testing Support** | Yes | Limited |
| **Best For** | Web apps, microservices | Stateful apps, compliance |

### When to Use Each Strategy

**Use Canary when:**
- You need gradual traffic shifting
- A/B testing of new features
- You want to minimize blast radius
- Real user feedback is valuable
- You have service mesh for fine-grained control

**Use Blue-Green when:**
- You need instant rollback capability
- Testing is required before production
- Compliance requires validation environment
- Zero-downtown deployments are critical
- You don't need gradual traffic exposure

### CLI Commands Reference

```bash
# Get rollout status
kubectl argo rollouts get rollout <name> -n <namespace>

# Watch rollout progress
kubectl argo rollouts get rollout <name> -n <namespace> --watch

# Promote a rollout
kubectl argo rollouts promote <name> -n <namespace>

# Abort a rollout
kubectl argo rollouts abort <name> -n <namespace>

# Retry an aborted rollout
kubectl argo rollouts retry rollout <name> -n <namespace>

# Rollback to previous version
kubectl argo rollouts undo <name> -n <namespace>

# View rollout history
kubectl argo rollouts history <name> -n <namespace>

# List all rollouts
kubectl argo rollouts list --all-namespaces

# Set image (trigger update)
kubectl argo rollouts set image <name> -n <namespace> <container>=<image>
```

### Monitoring Commands

```bash
# View events
kubectl get events -n <namespace> --sort-by='.lastTimestamp'

# Describe rollout
kubectl describe rollout <name> -n <namespace>

# View related ReplicaSets
kubectl get rs -n <namespace> -l app=<app-name>
```

---

## Conclusion

### Completed Tasks Summary

| Task | Points | Status |
|------|--------|--------|
| Task 1 — Argo Rollouts Fundamentals | 2 pts | ✅ Completed |
| Task 2 — Canary Deployment | 3 pts | ✅ Completed |
| Task 3 — Blue-Green Deployment | 3 pts | ✅ Completed |
| Task 4 — Documentation | 2 pts | ✅ Completed |
| **Total** | **10 pts** | **✅ 100%** |

### Demonstrated Capabilities

- ✅ Argo Rollouts installation and configuration
- ✅ Canary deployment with gradual traffic shifting (20% → 100%)
- ✅ Manual and automatic promotion
- ✅ Abort and retry functionality
- ✅ Blue-Green deployment with preview service
- ✅ Instant promotion and rollback
- ✅ Comprehensive comparison of deployment strategies

---

## Appendix

### Configuration Files Created

1. `canary-rollout.yaml` - Canary Rollout configuration
2. `canary-service.yaml` - Service for Canary deployment
3. `bluegreen-rollout.yaml` - Blue-Green Rollout configuration
4. `bluegreen-services.yaml` - Active and Preview services


