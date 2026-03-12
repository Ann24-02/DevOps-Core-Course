# Lab 5 - Ansible Fundamentals

## 1. Architecture Overview
- **Ansible version**: 2.16+
- **Target VM**: Ubuntu 22.04 LTS on Yandex Cloud
- **VM IP**: 93.77.184.101
- **Role structure**: Three main roles (common, docker, app_deploy)
- **Inventory**: Static inventory with host variables
- **Configuration**: Custom ansible.cfg with optimized settings
- **Project structure**:
```
ansible/
├── inventory/
│   ├── hosts.ini
│   └── group_vars/
│       └── all.yml (encrypted)
├── roles/
│   ├── common/
│   ├── docker/
│   └── app_deploy/
├── playbooks/
│   ├── provision.yml
│   └── deploy.yml
└── ansible.cfg
```

## 2. Roles Documentation

### Common Role
- **Purpose**: Basic system preparation and package management
- **Tasks**:
  - Update apt cache with cache_valid_time=3600 (idempotent)
  - Install essential packages: python3-pip, curl, git, vim, htop, tree, net-tools
- **Variables**: common_packages list in defaults/main.yml
- **Idempotency**: Uses apt module with state=present

### Docker Role
- **Purpose**: Install and configure Docker
- **Tasks**:
  - Add Docker GPG key and repository
  - Install Docker packages (docker-ce, docker-ce-cli, containerd.io)
  - Start and enable Docker service
  - Add user to docker group
  - Install Docker Python modules
- **Handlers**: restart docker (triggered when group changes)
- **Variables**: Docker version constraints in defaults
- **Dependencies**: Requires common role

### App_Deploy Role
- **Purpose**: Deploy containerized application from Docker Hub
- **Tasks**:
  - Login to Docker Hub using vault credentials
  - Pull Docker image (linux/amd64)
  - Stop and remove existing container
  - Run new container with port mapping
  - Wait for application readiness
  - Health check verification
- **Variables**: app_name, app_port, restart_policy

## 3. Idempotency Demonstration

### First Provision Run
![First provision run](images/lab5(1).jpg)
*Figure 1: First provision run showing 9 changed tasks*

### Second Provision Run
![Second provision run](images/lab5(2).jpg)
*Figure 2: Second provision run showing 0 changed tasks (idempotency demonstrated)*

## 5. Deployment Verification

### Deploy Playbook Output
![Deploy output](images/lab5.jpg)
*Figure 3: Successful application deployment with health check verification*



**Explanation**: All Ansible modules verify system state before applying changes, which guarantees idempotency.

## 4. Ansible Vault Usage
- Encrypted credentials stored in `inventory/group_vars/all.yml`
- Protects Docker Hub login and secrets
- Decrypted only at runtime



### Container Status
```
docker ps
devops-app running on port 8080
```

### Health Check
```
curl http://93.77.184.101:8080/health
status: healthy
```

## 6. Challenges Faced
- OS Login conflict → fixed via metadata
- ARM/AMD mismatch → rebuilt image with --platform linux/amd64
- Vault password issues → recreated vault

## 7. Conclusion

The lab demonstrates:
- Role-based Ansible design
- Idempotent provisioning
- Secure secrets handling
- Dockerized application deployment



