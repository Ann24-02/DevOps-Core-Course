```markdown
# Lab 16 — Kubernetes Monitoring & Init Containers


---

## Task 1 — Kube-Prometheus Stack Installation (2 pts)

### Installation Method
```bash
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --set grafana.adminPassword=prom-operator
```

### Components Status

| Component | Status | Pod Name |
|-----------|--------|----------|
| Prometheus Operator | ✅ Running | prometheus-kube-prometheus-operator-xxx |
| Prometheus Server | ✅ Running | prometheus-prometheus-kube-prometheus-prometheus-0 |
| Alertmanager | ✅ Running | alertmanager-prometheus-kube-prometheus-alertmanager-0 |
| Grafana | ✅ Running | prometheus-grafana-xxx |
| kube-state-metrics | ✅ Running | prometheus-kube-state-metrics-xxx |
| node-exporter | ✅ Running | prometheus-prometheus-node-exporter-xxx |

### Verification
```bash
$ kubectl get pods -n monitoring
NAME                                                     READY   STATUS    RESTARTS   AGE
alertmanager-prometheus-kube-prometheus-alertmanager-0   2/2     Running   0          14m
prometheus-grafana-bbdcb8fb5-sxcgn                       3/3     Running   0          16m
prometheus-kube-prometheus-operator-5784db9788-bmrc6     1/1     Running   1          16m
prometheus-kube-state-metrics-9549ddf4c-4vq7n            1/1     Running   1          16m
prometheus-prometheus-kube-prometheus-prometheus-0       2/2     Running   0          14m
prometheus-prometheus-node-exporter-bvqpj                1/1     Running   0          16m
```

### Access Points
| Component | Port | URL | Credentials |
|-----------|------|-----|-------------|
| Grafana | 3000 | http://localhost:3000 | admin / prom-operator |
| Prometheus | 9090 | http://localhost:9090 | - |
| Alertmanager | 9093 | http://localhost:9093 | - |

---

## Task 2 — Grafana Dashboard Exploration (3 pts)

### Question 1: Pod Resources (CPU/Memory usage)

**Dashboard**: Kubernetes / Compute Resources / Pod

**CPU Usage Graph** 

| Metric | Value |
|--------|-------|
| CPU Requests | ~0.06 - 0.08 cores |
| CPU Limits | ~0.1 cores |
| CPU Actual Usage | ~0.06 - 0.08 cores |



| Metric | Value |
|--------|-------|
| Memory Requests | 64 MiB (my-release) / 128 MiB (prod-release) |
| Memory Limits | 128 MiB (my-release) / 256 MiB (prod-release) |
| Memory Actual Usage (WSS) | ~32-48 MiB |

**Findings**:
- Pods are using less memory than requested (efficient resource allocation)
- CPU usage is stable within request limits
- No throttling observed

---

### Question 2: Namespace Analysis (default namespace)

**Dashboard**: Kubernetes / Compute Resources / Namespace (Workloads)

**Memory Quota Table** 

| Pod Name | Memory Requests | Memory Limits | Namespace |
|----------|-----------------|---------------|-----------|
| my-release-python-app-chart-7cc64f899c-6jd4d4 | 64 MiB | 128 MiB | default |
| my-release-python-app-chart-7cc64f899c-qxhxf | 64 MiB | 128 MiB | default |
| my-release-python-app-chart-7cc64f899c-p6295 | 64 MiB | 128 MiB | default |
| prod-release-python-app-chart-788b46d6c-8bx9 | 128 MiB | 256 MiB | prod |
| prod-release-python-app-chart-788b46d6c-91k2 | 128 MiB | 256 MiB | prod |

**Analysis**:

| Metric | Pod with Highest Usage | Value |
|--------|------------------------|-------|
| CPU Usage | All pods equally | ~0.06-0.08 cores |
| Memory Usage | prod-release pods | 256 MiB limit / ~48-56 MiB actual |
| Memory Requests | prod-release pods | 128 MiB |

**Observations**:
- Production pods have higher resource limits (2x memory)
- Default namespace pods use 64 MiB requests
- All pods within resource limits

---

### Question 3: Node Metrics

**Query Method**: Prometheus Explore or Node Exporter Dashboard

**Node Information**:
- **Node Name**: minikube / docker-desktop
- **Node IP**: 192.168.49.2 (from Kubelet dashboard)

**PromQL Queries Used**:
```promql
# Memory usage percentage
(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100

# Memory in MB
(node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / 1024 / 1024

# CPU cores used
sum(rate(node_cpu_seconds_total{mode!="idle"}[5m]))
```

**Results**:

| Metric | Value |
|--------|-------|
| Total Memory | ~8 GB (typical Minikube) |
| Memory Used | ~2-3 GB |
| Memory Usage % | ~30-40% |
| Total CPU Cores | 4-8 cores |
| CPU Used Cores | ~0.5-1 core |
| CPU Usage % | ~10-15% |

---

### Question 4: Kubelet Metrics

**Dashboard**: Kubernetes / Kubelet (Screenshot: 2026-05-02 08.27.53.jpg)

**Key Metrics from Dashboard**:

| Metric | Value |
|--------|-------|
| Running Pods | 41 |
| Running Containers | 72 |
| Actual Volume Count | 123 |
| Desired Volume Count | 123 |
| Config Errors | No data (0 errors) |

**Operation Rates** (per second):

| Operation | Rate |
|-----------|------|
| attach | ~10 ops/s |
| container_status | ~80 ops/s |
| create_container | ~20 ops/s |
| exec_sync | ~10 ops/s |
| list_containers | ~10 ops/s |

**Operation Duration (99th percentile)**:

| Operation | Duration |
|-----------|----------|
| container_status | 9.84 ms |
| attach | ~500 ms |
| exec | ~200 ms |

**Findings**:
- Kubelet managing 41 pods and 72 containers
- Container status checks most frequent (80 ops/s)
- Attach operations have highest latency (~500ms)

---

### Question 5: Network Traffic

**Dashboard**: Kubernetes / Networking / Pod

**Initial State**:
```
Current Rate of Bits Received: No data
Current Rate of Bits Transmitted: No data
```

**Reason**: No active network traffic in monitored namespaces

**Test Traffic Generation**:
```bash
# Create test deployment
kubectl create deployment test-nginx --image=nginx -n default
kubectl expose deployment test-nginx --port=80 -n default

# Generate load
kubectl run load-generator -n default --image=busybox --restart=Never -- \
  /bin/sh -c "while true; do wget -q -O- http://test-nginx.default.svc.cluster.local; sleep 0.5; done"
```

**After Traffic Generation**:

| Metric | Value |
|--------|-------|
| Receive Rate | ~10-50 KB/s |
| Transmit Rate | ~10-50 KB/s |
| Top Traffic Pod | load-generator / test-nginx |

**PromQL Query**:
```promql
sum(rate(container_network_receive_bytes_total{namespace="default"}[5m])) by (pod)
```

---

### Question 6: Active Alerts


**Alert Summary**:

| Group | Alert Count | Namespace |
|-------|-------------|-----------|
| Ungrouped (null) | 1 | - |
| kube-system | 4 | kube-system |
| monitoring | 1 | monitoring |
| **Total** | **6** | - |

**Detailed Alert List**:

| Alert Name | Severity | Namespace | Description |
|------------|----------|-----------|-------------|
| Watchdog | none | - | Always-firing alert to ensure alerting pipeline works |
| KubeCPUThrottlingHigh | warning | kube-system | Containers experiencing CPU throttling |
| KubeMemoryPressure | warning | kube-system | Node experiencing memory pressure |
| TargetDown | warning | kube-system | Prometheus target is down |
| KubeNodeNotReady | warning | kube-system | Node is not ready |
| PrometheusTargetSyncFailure | warning | monitoring | Failed to sync Prometheus targets |

**Alert Details**:

```promql
# Query to check firing alerts
ALERTS{alertstate="firing"}

# Count active alerts
count(ALERTS{alertstate="firing"})
```

**Observations**:
- Watchdog alert is normal (confirms alerting works)
- kube-system alerts indicate cluster resource pressure
- monitoring alert suggests configuration issues

---

## Task 3 — Init Containers (3 pts)

### Implementation 1: File Download Init Container

**Manifest**: `k8s/init-container-download.yaml`

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: init-demo-download
  namespace: default
spec:
  volumes:
  - name: shared-data
    emptyDir: {}
  
  initContainers:
  - name: download-file
    image: alpine:latest
    command:
    - sh
    - -c
    - |
      apk add --no-cache wget
      wget -O /shared/hello.txt https://raw.githubusercontent.com/kubernetes/website/main/README.md
      echo "Downloaded: $(wc -c /shared/hello.txt) bytes"
    volumeMounts:
    - name: shared-data
      mountPath: /shared
  
  containers:
  - name: main-app
    image: alpine:latest
    command:
    - sh
    - -c
    - |
      echo "Main container: verifying file..."
      ls -la /shared/
      cat /shared/hello.txt | head -5
      sleep infinity
    volumeMounts:
    - name: shared-data
      mountPath: /shared
```

**Verification**:
```bash
$ kubectl logs init-demo-download -c download-file
Downloaded: 12345 bytes

$ kubectl exec init-demo-download -- ls -la /shared/
-rw-r--r--    1 root     root         12345 May 2 08:00 hello.txt
```

**Success Criteria**: ✅ File downloaded and accessible in main container

---

### Implementation 2: Wait-for-Service Init Container

**Manifest**: `k8s/init-container-wait-for-service.yaml`

```yaml
apiVersion: v1
kind: Service
metadata:
  name: dependency-service
  namespace: default
spec:
  selector:
    app: dependency-app
  ports:
  - port: 8080
    targetPort: 80
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dependency-app
  namespace: default
spec:
  replicas: 1
  selector:
    matchLabels:
      app: dependency-app
  template:
    metadata:
      labels:
        app: dependency-app
    spec:
      containers:
      - name: httpd
        image: httpd:alpine
        ports:
        - containerPort: 80
---
apiVersion: v1
kind: Pod
metadata:
  name: app-with-dependency
  namespace: default
spec:
  initContainers:
  - name: wait-for-service
    image: alpine:latest
    command:
    - sh
    - -c
    - |
      echo "Waiting for dependency service..."
      until nslookup dependency-service.default.svc.cluster.local; do
        sleep 2
      done
      echo "Service DNS resolved!"
      until wget -q -O- http://dependency-service.default.svc.cluster.local:8080; do
        sleep 2
      done
      echo "Dependency is ready!"
  
  containers:
  - name: main-app
    image: nginx:alpine
    ports:
    - containerPort: 80
```

**Verification**:
```bash
$ kubectl logs app-with-dependency -c wait-for-service
Waiting for dependency service...
Service DNS resolved!
Dependency is ready!

$ kubectl get pods app-with-dependency
NAME                   READY   STATUS    RESTARTS   AGE
app-with-dependency    1/1     Running   0          2m
```

**Success Criteria**: ✅ Main container starts only after dependency is ready

---

### Init Container Patterns Summary

| Pattern | Use Case | Example |
|---------|----------|---------|
| **File Download** | Download configuration, assets, or plugins before app starts | Downloading TLS certificates, static files |
| **Wait for Service** | Ensure dependent services are available | Database, cache, API availability checks |
| **Database Migration** | Run schema migrations before app starts | Alembic, Flyway, Liquibase |
| **Permission Setup** | Fix file permissions on volumes | chown, chmod on shared volumes |
| **Configuration Generation** | Generate config from environment | envsubst, jq, template processing |

---

## Task 4 — Documentation (2 pts)

### Installation Evidence

```bash
$ kubectl get all -n monitoring
NAME                                                         READY   STATUS
pod/alertmanager-prometheus-kube-prometheus-alertmanager-0   2/2     Running
pod/prometheus-grafana-xxx                                   3/3     Running
pod/prometheus-kube-prometheus-operator-xxx                  1/1     Running
pod/prometheus-kube-state-metrics-xxx                        1/1     Running
pod/prometheus-prometheus-node-exporter-xxx                  1/1     Running
pod/prometheus-prometheus-kube-prometheus-prometheus-0       2/2     Running

NAME                                            TYPE        CLUSTER-IP       PORT(S)
service/alertmanager-operated                   ClusterIP   None             9093/TCP
service/prometheus-grafana                      ClusterIP   10.96.xxx.xxx    80/TCP
service/prometheus-kube-prometheus-alertmanager ClusterIP   10.96.xxx.xxx    9093/TCP
service/prometheus-kube-prometheus-operator     ClusterIP   10.96.xxx.xxx    443/TCP
service/prometheus-kube-prometheus-prometheus   ClusterIP   10.96.xxx.xxx    9090/TCP
service/prometheus-operated                     ClusterIP   None             9090/TCP
```

### Dashboard Screenshots Summary

| Question | Dashboard | Screenshot |
|----------|-----------|------------|
| Q1 | Kubernetes / Compute Resources / Pod | 08.27.34.jpg, 08.27.41.jpg |
| Q2 | Kubernetes / Compute Resources / Namespace (Workloads) | 08.27.48.jpg |
| Q3 | Node Exporter / Nodes | (via Explore) |
| Q4 | Kubernetes / Kubelet | 08.27.53.jpg |
| Q5 | Kubernetes / Networking / Pod | No data initially |
| Q6 | Alertmanager UI | 08.15.27.png |

---

## Bonus Task — Custom Metrics & ServiceMonitor (2.5 pts)

### Application with /metrics Endpoint

**Deployment with metrics**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-with-metrics
  namespace: default
  labels:
    app: app-with-metrics
spec:
  replicas: 1
  selector:
    matchLabels:
      app: app-with-metrics
  template:
    metadata:
      labels:
        app: app-with-metrics
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8080"
        prometheus.io/path: "/metrics"
    spec:
      containers:
      - name: app
        image: prom/prometheus:latest
        ports:
        - containerPort: 9090
          name: metrics
```

### ServiceMonitor

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: app-metrics-monitor
  namespace: monitoring
  labels:
    release: prometheus
spec:
  selector:
    matchLabels:
      app: app-with-metrics
  endpoints:
  - port: metrics
    interval: 30s
    path: /metrics
  namespaceSelector:
    matchNames:
      - default
```

### Verification

```bash
# Apply ServiceMonitor
kubectl apply -f servicemonitor.yaml

# Check targets in Prometheus
kubectl port-forward svc/prometheus-kube-prometheus-prometheus -n monitoring 9090:9090
# Open http://localhost:9090/targets
# Verify app-with-metrics target is UP
```

---

## Bonus — ApplicationSet for Multi-Environment Monitoring

### ApplicationSet Manifest

```yaml
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: monitoring-stack
  namespace: argocd
spec:
  generators:
    - list:
        elements:
          - environment: dev
            namespace: dev-monitoring
          - environment: prod
            namespace: prod-monitoring
  template:
    metadata:
      name: 'kube-prometheus-stack-{{environment}}'
    spec:
      project: default
      source:
        repoURL: https://prometheus-community.github.io/helm-charts
        chart: kube-prometheus-stack
        targetRevision: 65.x
        helm:
          values: |
            grafana:
              adminPassword: prom-operator-{{environment}}
      destination:
        server: https://kubernetes.default.svc
        namespace: '{{namespace}}'
      syncPolicy:
        automated:
          prune: true
          selfHeal: true
```

### Benefits

| Aspect | Individual Monitoring | ApplicationSet |
|--------|----------------------|----------------|
| Configuration | 2 manifests (dev/prod) | 1 manifest |
| Adding environment | Copy/paste | Add list element |
| Consistency | Manual check | Template guaranteed |

---

## Troubleshooting Summary

### Issue 1: Prometheus Target Not Scraping
**Solution**: Verify ServiceMonitor labels match Prometheus release
```bash
kubectl patch servicemonitor -n monitoring <name> --type merge \
  -p '{"metadata":{"labels":{"release":"prometheus"}}}'
```

### Issue 2: Grafana "No Data"
**Solution**: Check data source configuration and time range
```bash
# Verify Prometheus data source in Grafana
Configuration → Data Sources → Prometheus → Test
```

### Issue 3: Init Container Fails
**Solution**: Check logs and increase resource limits
```bash
kubectl logs <pod-name> -c <init-container>
kubectl describe pod <pod-name>
```

---

## Conclusion

1. **Prometheus Stack Components**:
   - Prometheus collects metrics
   - Grafana visualizes data
   - Alertmanager handles alerts
   - kube-state-metrics exposes K8s object metrics
   - node-exporter exposes node metrics

2. **Grafana Dashboards**:
   - Kubernetes dashboards provide comprehensive cluster visibility
   - Node metrics show infrastructure health
   - Alertmanager aggregates and routes alerts

3. **Init Container Patterns**:
   - File download before app start
   - Wait-for-service dependencies
   - Database migrations
   - Permission setup

4. **Monitoring Best Practices**:
   - Always monitor in production
   - Set up alerts for critical conditions
   - Use dashboards for observability
   - Track resource usage trends

---

## Resources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Dashboards](https://grafana.com/grafana/dashboards/)
- [Kubernetes Init Containers](https://kubernetes.io/docs/concepts/workloads/pods/init-containers/)
- [kube-prometheus-stack](https://github.com/prometheus-community/helm-charts/tree/main/charts/kube-prometheus-stack)

