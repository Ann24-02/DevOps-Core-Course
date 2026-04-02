# Lab 9 --- Kubernetes Fundamentals

## Task 1 --- Local Kubernetes Setup

### Installation

``` bash
brew install minikube
```

### Cluster Setup

``` bash
minikube start --cpus=4 --memory=7000 --driver=docker
```

### Verification Commands

``` bash
kubectl cluster-info
kubectl get nodes
kubectl get pods -A
```

### Output

    $ kubectl cluster-info
    Kubernetes control plane is running at https://127.0.0.1:62803
    CoreDNS is running at https://127.0.0.1:62803/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy

    $ kubectl get nodes
    NAME       STATUS   ROLES           AGE   VERSION
    minikube   Ready    control-plane   18s   v1.35.1

    $ kubectl get pods -A
    NAMESPACE     NAME                               READY   STATUS    RESTARTS   AGE
    kube-system   coredns-7d764666f9-vc4sl           0/1     Running   0          20s
    kube-system   etcd-minikube                      1/1     Running   0          26s
    kube-system   kube-apiserver-minikube            1/1     Running   0          26s
    kube-system   kube-controller-manager-minikube   1/1     Running   0          26s
    kube-system   kube-proxy-hpr5z                   1/1     Running   0          20s
    kube-system   kube-scheduler-minikube            1/1     Running   0          26s
    kube-system   storage-provisioner                1/1     Running   0          24s

## Configuration Details

  Parameter            Value
  -------------------- ------------------------
  CPU                  4 cores
  Memory               7GB (7000MB)
  Driver               docker
  Kubernetes Version   v1.35.1
  Minikube Version     v1.38.1
  Status               All components running

------------------------------------------------------------------------

## Tool Selection: Minikube

I chose Minikube for this lab for the following reasons:

-   Mature solution with long-term development
-   Simple cluster management commands
-   Built-in addons (Ingress, Metrics Server, Dashboard)
-   Seamless Docker integration on macOS
-   Multi-driver support (docker, qemu, virtualbox, hyperkit)
-   Strong community and documentation
-   Resource-efficient and configurable

Example:

``` bash
minikube addons enable ingress
minikube addons enable metrics-server
```

------------------------------------------------------------------------

## Architecture Overview

    ┌─────────────────────────────────────────────────────────┐
    │                  Minikube Cluster                        │
    │                                                         │
    │  ┌────────────────────────────────────────────────┐    │
    │  │         Control Plane Node                      │    │
    │  │  ┌──────────────────────────────────────────┐ │    │
    │  │  │ kube-apiserver    | etcd                 │ │    │
    │  │  │ kube-scheduler    | kube-controller-mgr │ │    │
    │  │  └──────────────────────────────────────────┘ │    │
    │  │                                                │    │
    │  │  ┌──────────────────────────────────────────┐ │    │
    │  │  │ Worker Components                        │ │    │
    │  │  │ kubelet | kube-proxy | container-runtime│ │    │
    │  │  └──────────────────────────────────────────┘ │    │
    │  └────────────────────────────────────────────────┘    │
    │                                                         │
    │  ┌────────────────────────────────────────────────┐    │
    │  │           System Pods                           │    │
    │  │  coredns | storage-provisioner                 │    │
    │  └────────────────────────────────────────────────┘    │
    └─────────────────────────────────────────────────────────┘

------------------------------------------------------------------------

## Learning Outcomes

-   Understanding Kubernetes control plane components
-   Declarative configuration model
-   Cluster architecture (control plane vs worker)
-   Namespace usage for isolation
-   Core components (CoreDNS, kube-proxy, container runtime)

------------------------------------------------------------------------

## Troubleshooting

``` bash
# Delete and recreate cluster
minikube delete
minikube start --cpus=4 --memory=7000 --driver=docker

# Check Docker memory
docker system info | grep -i memory

# Reduce resource usage if needed
minikube start --cpus=2 --memory=4096 --driver=docker
```
# 🚀 Task 2 --- Application Deployment with Custom Python App

## 📌 Overview

This task demonstrates deploying a custom Python (Flask) application
into a Kubernetes cluster using Minikube. The application is
containerized with Docker, deployed using a Kubernetes Deployment, and
exposed via a NodePort Service.

------------------------------------------------------------------------

## 🐳 Docker Image

### Build Image

``` bash
cd app
docker build -t python-app:latest .
```

### Load Image into Minikube

``` bash
minikube image load python-app:latest
```

------------------------------------------------------------------------

## ⚙️ Deployment

### Apply Deployment

``` bash
kubectl apply -f k8s/deployment.yml
```

### Verify Pods

``` bash
kubectl get pods
```

### Output Example

    NAME                          READY   STATUS    RESTARTS   AGE
    python-app-7b8c9d6f4d-2x4h   1/1     Running   0          45s
    python-app-7b8c9d6f4d-5k7j   1/1     Running   0          45s
    python-app-7b8c9d6f4d-9m2p   1/1     Running   0          45s

✔ Three replicas are running for high availability.

------------------------------------------------------------------------

## 🌐 Service

### Apply Service

``` bash
kubectl apply -f k8s/service.yml
```

### Verify Service

``` bash
kubectl get svc
```

### Output Example

    NAME                 TYPE       CLUSTER-IP      PORT(S)        AGE
    python-app-service   NodePort   10.96.123.45    80:30080/TCP   10s

✔ The application is exposed via NodePort on port **30080**.

------------------------------------------------------------------------

## 🧪 Testing the Application

### Root Endpoint

``` bash
curl http://localhost:8080/
```

### Example Response

``` json
{
  "service": {
    "name": "devops-info-service",
    "version": "1.0.0",
    "description": "DevOps course info service",
    "framework": "Flask"
  },
  "system": {
    "hostname": "python-app-7b8c9d6f4d-2x4h",
    "platform": "Linux"
  }
}
```

------------------------------------------------------------------------

### Health Check

``` bash
curl http://localhost:8080/health
```

``` json
{
  "status": "healthy",
  "timestamp": "2024-03-26T15:30:00Z",
  "uptime_seconds": 45
}
```

------------------------------------------------------------------------

### Metrics Endpoint

``` bash
curl http://localhost:8080/metrics
```

    # HELP http_requests_total Total HTTP requests
    # TYPE http_requests_total counter
    ...

------------------------------------------------------------------------

## 📚 Summary

-   Built a Docker image for a Python Flask app
-   Loaded the image into Minikube
-   Deployed the app using Kubernetes Deployment
-   Exposed the app using a NodePort Service
-   Verified functionality via HTTP endpoints

------------------------------------------------------------------------

## ⚠️ Notes

-   Ensure Minikube is running before deployment
-   If localhost:8080 is not accessible, run:

``` bash
minikube service python-app-service
```

-   Port-forward alternative:

``` bash
kubectl port-forward service/python-app-service 8080:80
```
# 🚀 Task 3 & 4 --- Service Configuration, Scaling and Updates

## 📌 Task 3 --- Service Configuration

### Service Status

``` bash
kubectl get svc
```

    NAME                 TYPE       CLUSTER-IP    PORT(S)        AGE
    python-app-service   NodePort   10.99.14.70   80:30080/TCP   14m

``` bash
kubectl get endpoints python-app-service
```

    NAME                 ENDPOINTS
    python-app-service   10.244.0.6:8080,10.244.0.7:8080,10.244.0.8:8080

✔ Service correctly routes traffic to 3 running pods.

------------------------------------------------------------------------

## 🌐 Access the Application

``` bash
kubectl port-forward service/python-app-service 8080:80
```

``` bash
curl http://localhost:8080/health
```

``` json
{
  "status": "healthy",
  "timestamp": "2024-03-26T...",
  "uptime_seconds": 120
}
```

------------------------------------------------------------------------

## 📈 Task 4 --- Scaling and Updates

### Scaling to 5 Replicas

``` bash
kubectl scale deployment python-app --replicas=5
```

``` bash
kubectl get pods | wc -l
```

✔ Application successfully scaled to 5 pods.

------------------------------------------------------------------------

### 🔄 Rolling Update

``` bash
kubectl set image deployment/python-app python-app=python-app:v2
```

``` bash
kubectl rollout status deployment/python-app
```

✔ Deployment updated with zero downtime.

------------------------------------------------------------------------

### ⏪ Rollback

``` bash
kubectl rollout history deployment/python-app
```

    REVISION  CHANGE-CAUSE
    1         <none>
    2         <none>

``` bash
kubectl rollout undo deployment/python-app
```

✔ Successfully rolled back to previous version.

------------------------------------------------------------------------

## ⚙️ Production Considerations

### Health Checks

-   Liveness Probe: `/health`, 30s delay, 10s interval
-   Readiness Probe: `/health`, 5s delay, 5s interval

### Resource Management

-   CPU: requests 100m, limits 200m
-   Memory: requests 64Mi, limits 128Mi

### Security

-   Non-root user (UID 1000)
-   Read-only root filesystem
-   All Linux capabilities dropped

------------------------------------------------------------------------

## 🚀 Improvements for Production

-   Horizontal Pod Autoscaler (HPA)
-   Pod Disruption Budgets (PDB)
-   Network Policies (zero-trust model)
-   Monitoring: Prometheus + Grafana
-   Logging: EFK / ELK stack

------------------------------------------------------------------------

## 🛠 Challenges & Solutions

### Challenge 1: ImagePullBackOff

**Solution:** Loaded local image using:

``` bash
minikube image load python-app:latest
```

------------------------------------------------------------------------

### Challenge 2: Probe Configuration

**Solution:** Adjusted `initialDelaySeconds` to allow proper startup
time.

------------------------------------------------------------------------

### Challenge 3: Service Connectivity

**Solution:** Verified labels match between Deployment and Service.

------------------------------------------------------------------------

## ✅ Final Verification

``` bash
kubectl get all
```

``` bash
curl http://localhost:8080/health
```

### Open in Browser

``` bash
minikube service python-app-service
```
