# Lab 6: Advanced Ansible & CI/CD - Submission


---

## Task 1: Blocks & Tags 

### Tags available:
```bash
$ ansible-playbook playbooks/provision.yml --list-tags
TASK TAGS: [common, docker, docker_config, docker_install, packages, users]# Lab 6: Advanced Ansible & CI/CD - Submission



------------------------------------------------------------------------

## Task 1: Blocks & Tags (2 pts)

### Tags available:

``` bash
$ ansible-playbook playbooks/provision.yml --list-tags
TASK TAGS: [common, docker, docker_config, docker_install, packages, users]
```

**Evidence of selective execution:**

\[Вставьте скриншот или вывод команды с `--tags docker`\]

------------------------------------------------------------------------

## Task 2: Docker Compose (3 pts)

### Successful deployment:

``` bash
$ ansible-playbook -i inventory playbooks/deploy.yml --ask-vault-pass
PLAY RECAP ********************************************************************************************************************************
vm1                        : ok=8    changed=2    unreachable=0    failed=0
```

### Idempotency proof (second run):

``` bash
$ ansible-playbook -i inventory playbooks/deploy.yml --ask-vault-pass
PLAY RECAP ********************************************************************************************************************************
vm1                        : ok=8    changed=0    unreachable=0    failed=0
```

### Application running:

``` bash
$ curl http://89.169.140.142:8080/health
{"status":"healthy","timestamp":"2026-03-05T02:32:50.308619+00:00","uptime_seconds":38}

$ ssh -i ~/.ssh/id_rsa ubuntu@89.169.140.142 "docker ps"
CONTAINER ID   IMAGE                COMMAND           PORTS                    NAMES
758e7621d5f7   nayaya0/devops-app   "python app.py"   0.0.0.0:8080->8080/tcp   devops-app
```

------------------------------------------------------------------------

## Task 3: Wipe Logic (1 pt)

### Test Results:

**Scenario 1: Normal deployment (wipe should NOT run)**\
Wipe tasks skipped, deployment successful

**Scenario 2: Wipe only**

``` text
PLAY RECAP: ok=5 changed=1
```

Result after wipe: No containers running

**Scenario 3: Clean reinstallation**

``` text
PLAY RECAP: ok=12 changed=4
```

Result after reinstall: Application healthy, container running

**Scenario 4: Safety check**

``` text
PLAY RECAP: ok=1 changed=0 skipped=1
```

Result: Container still running (wipe blocked)

### Full wipe test results:

``` text
=== LAB 6 - WIPE LOGIC TEST RESULTS ===

SCENARIO 2 - Wipe only:
PLAY RECAP ********************************************************************************************************************************
vm1                        : ok=5    changed=1    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0

Result after wipe:
CONTAINER ID   IMAGE     COMMAND   CREATED   STATUS    PORTS     NAMES

---

SCENARIO 3 - Clean reinstall:
PLAY RECAP ********************************************************************************************************************************
vm1                        : ok=12   changed=4    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0

Result after reinstall:
{"status":"healthy","timestamp":"2026-03-05T02:32:50.308619+00:00","uptime_seconds":38}
CONTAINER ID   IMAGE                COMMAND           CREATED          STATUS          PORTS                    NAMES
758e7621d5f7   nayaya0/devops-app   "python app.py"   46 seconds ago   Up 43 seconds   0.0.0.0:8080->8080/tcp   devops-app

---

SCENARIO 4 - Safety check:
PLAY RECAP ********************************************************************************************************************************
vm1                        : ok=1    changed=0    unreachable=0    failed=0    skipped=1    rescued=0    ignored=0

Result after safety check:
CONTAINER ID   IMAGE                COMMAND           CREATED              STATUS              PORTS                    NAMES
758e7621d5f7   nayaya0/devops-app   "python app.py"   About a minute ago   Up About a minute   0.0.0.0:8080->8080/tcp   devops-app
```

------------------------------------------------------------------------

## Task 4: CI/CD (3 pts)

### GitHub Actions Workflow:

``` yaml
name: Ansible Deployment

on:
  push:
    branches: [ main ]
    paths:
      - 'ansible/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install Ansible
        run: pip install ansible
      - name: Deploy
        env:
          VAULT_PASS: ${{ secrets.ANSIBLE_VAULT_PASSWORD }}
        run: |
          cd ansible
          echo "$VAULT_PASS" > /tmp/vault_pass
          ansible-playbook -i inventory playbooks/deploy.yml \
            --vault-password-file /tmp/vault_pass
```

### Secrets configured in GitHub:

-   `ANSIBLE_VAULT_PASSWORD`

### Status Badge:

    https://github.com/your-username/your-repo/actions/workflows/ansible-deploy.yml/badge.svg

------------------------------------------------------------------------

## Task 5: Documentation

This file serves as the documentation for Lab 6.

------------------------------------------------------------------------

## Research Questions Answers

### Task 1:

**What happens if rescue block also fails?**\
Ansible will report a failure for the entire task.

**Can you have nested blocks?**\
Yes, blocks can be nested for hierarchical error handling.

**How do tags inherit?**\
Tags at block level are inherited by all tasks within the block.

------------------------------------------------------------------------

### Task 2:

**restart: always vs unless-stopped?**\
`always` restarts regardless of exit status, `unless-stopped` respects
manual stops.

**Docker Compose networks vs bridge?**\
Compose provides service discovery, bridge requires manual linking.

**Vault variables in templates?**\
Yes, they're decrypted at runtime.

------------------------------------------------------------------------

### Task 3:

**Why both variable AND tag?**\
Double safety --- requires explicit enablement.

**Why wipe before deployment?**\
Enables clean reinstallation in one run.

**Extending to wipe volumes?**\
Add parameters like `remove_volumes: true`.

------------------------------------------------------------------------

### Task 4:

**Security of SSH keys in GitHub Secrets?**\
Encrypted but use limited-permission keys.

**Staging → production pipeline?**\
Use environments with approval gates.

**Rollbacks?**\
Tag deployments, keep previous configs, create rollback playbook.

------------------------------------------------------------------------

## Summary

**Total time spent:** \[3 hours\]

**Key learnings:**\
Blocks, tags, wipe logic, idempotency, CI/CD integration

**Challenges:**\
Vault editing, wipe logic implementation, port configuration

------------------------------------------------------------------------



