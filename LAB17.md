```markdown
# Lab 17 — Cloudflare Workers Edge Deployment
## Worker URL: https://lab17-worker.ak-lab17-worker.workers.dev

---

## Task 1 — Cloudflare Setup (3 pts)

### Account & Tooling
- Cloudflare account successfully created
- Wrangler CLI v4.90.0 installed and authenticated
- workers.dev subdomain: `ak-lab17-worker.workers.dev`

### Project Initialization
```bash
npm create cloudflare@latest lab17-worker -- --type=typescript
```

### Project Structure
```
lab17-worker/
├── src/index.ts              # Worker code with all endpoints
├── wrangler.jsonc            # Configuration (vars, kv_namespaces, secrets)
├── package.json              # Dependencies
├── tsconfig.json             # TypeScript configuration
└── worker-configuration.d.ts # Auto-generated types
```

---

## Task 2 — Build and Deploy Worker API (4 pts)

### Implemented Endpoints

| Endpoint | Method | Description | Status |
|----------|--------|-------------|--------|
| `/health` | GET | Health check with version and uptime | ✅ |
| `/metadata` | GET | Deployment metadata (version, language, endpoints) | ✅ |
| `/edge` | GET | Edge request metadata (colo, country, city, TLS) | ✅ |
| `/api/hello` | GET | Greeting endpoint with name parameter | ✅ |
| `/api/echo` | POST | Echo request body back to client | ✅ |
| `/api/kv` | POST | Store key-value pair in Workers KV | ✅ |
| `/api/kv` | GET | Retrieve value from KV by key | ✅ |
| `/api/admin` | GET | Protected endpoint requiring Bearer token | ✅ |

### Example Responses

#### GET /health
```json
{
  "status": "healthy",
  "timestamp": "2026-05-08T01:28:15.623Z",
  "version": "v1.0.0",
  "uptime": "running"
}
```

#### GET /metadata
```json
{
  "appName": "lab17-worker-api",
  "version": "v1.0.0",
  "apiVersion": "2024.01",
  "defaultLanguage": "en",
  "runtime": "Cloudflare Workers",
  "deployedAt": "2026-05-08T01:28:15.799Z",
  "region": "global-edge",
  "endpoints": [
    "GET /health",
    "GET /metadata",
    "GET /edge",
    "GET /api/hello?name=X",
    "POST /api/echo",
    "GET /api/kv?key=X",
    "POST /api/kv",
    "GET /api/admin"
  ]
}
```

#### GET /api/hello?name=Cloudflare
```json
{
  "message": "Hello, Cloudflare!",
  "timestamp": "2026-05-08T01:28:16.151Z",
  "language": "en"
}
```

---

## Task 3 — Global Edge Behavior (4 pts)

### Edge Metadata Endpoint Response

**GET /edge** (requested from Russia):

```json
{
  "colo": "HEL",
  "country": "RU",
  "asn": 203509,
  "city": "Innopolis",
  "httpProtocol": "HTTP/2",
  "tlsVersion": "TLSv1.3",
  "region": "Tatarstan Republic",
  "timezone": "Europe/Moscow",
  "longitude": "48.74754",
  "latitude": "55.74982",
  "requestId": "unknown"
}
```

### Fields Implemented (Requirements)

| Required | Implemented | Value Example |
|----------|-------------|---------------|
| `colo` | ✅ | "HEL" (Helsinki data center) |
| `country` | ✅ | "RU" (Russia) |
| Additional field | ✅ | `city`, `asn`, `httpProtocol`, `tlsVersion` |

### How Cloudflare Workers Achieves Global Distribution

1. **Single Deployment to Central Registry**
   - `wrangler deploy` uploads code once to Cloudflare's central system
   - No need to select regions or deploy multiple times

2. **Automatic Propagation**
   - Code is automatically distributed to all 300+ Cloudflare edge locations worldwide
   - Takes 30-90 seconds for global propagation

3. **Anycast Routing**
   - User requests are automatically routed to the nearest edge location
   - Based on BGP routing and network latency
   - No configuration required

4. **Comparison with Traditional Platforms**

| Aspect | Cloudflare Workers | AWS Lambda (Multi-Region) |
|--------|-------------------|--------------------------|
| Deployment | 1 deploy → global | 1 deploy per region |
| Region selection | Automatic | Manual (us-east-1, eu-west-1, etc.) |
| Latency | 10-50ms worldwide | Region-dependent (100-300ms cross-region) |
| Cold starts | 5-10ms | 100-1000ms |
| Operational overhead | None | Multiple region management |

### workers.dev vs Routes vs Custom Domains

| Feature | workers.dev | Routes | Custom Domains |
|---------|-------------|--------|----------------|
| URL Format | `*.workers.dev` | `*.yourdomain.com` | `yourdomain.com` |
| SSL/TLS | Automatic, free | Automatic, free | Automatic (with Cloudflare DNS) |
| Setup Time | Immediate | 5 minutes | 10 minutes (DNS propagation) |
| Cost | Free | Free (with domain) | Free (with Cloudflare DNS) |
| Use Case | Development, testing, demos | Production subdomains (api., admin.) | Production main domain |
| Limitation | Public, no custom branding | Requires domain in Cloudflare | Requires full DNS management |

**Why no "deploy to 3 regions" step in Workers?**
- Workers are globally distributed by default because Cloudflare's network IS the platform
- The runtime is lightweight (no container startup overhead)
- Anycast networking handles routing automatically
- You write code once, it runs everywhere without additional configuration

---

## Task 4 — Configuration, Secrets & Persistence (3 pts)

### Environment Variables (wrangler.jsonc)

```json
{
  "vars": {
    "APP_NAME": "lab17-worker-api",
    "APP_VERSION": "v1.0.0",
    "API_VERSION": "2024.01",
    "DEFAULT_LANG": "en"
  }
}
```

### Secrets (Encrypted)

```bash
# Created with wrangler secret put
API_SECRET=super-secret-key-12345
ADMIN_TOKEN=admin-token-67890
```

**Why plaintext vars are not suitable for secrets:**
- Plaintext vars appear in Cloudflare Dashboard
- They are visible in `wrangler.jsonc` (could be committed to Git)
- Secrets are encrypted at rest and never exposed in logs or dashboard
- Secrets are only decrypted at runtime inside the Worker

### KV Namespace

```yaml
# Created with:
npx wrangler kv namespace create MY_KV

# Result:
id: 080422d484ee44cc86c4baeb59c1f060
binding: MY_KV
```

### KV Persistence Test

**Store value:**
```bash
curl -X POST $WORKER_URL/api/kv \
  -H "Content-Type: application/json" \
  -d '{"key": "testKey", "value": "persistent-value"}'
```

**Response:**
```json
{"success":true,"key":"testKey"}
```

**Retrieve value:**
```bash
curl "$WORKER_URL/api/kv?key=testKey"
```

**Response:**
```json
{"key":"testKey","value":"persistent-value"}
```

**Persistence Verification:**
After deploying a new version of the Worker, the KV value remained accessible. KV is a separate storage service that persists across Worker deployments.

---

## Task 5 — Observability & Operations (3 pts)

### Logging Implementation

Console logs added to key operations:
```typescript
console.log(`[REQUEST] ${method} ${path} - ${new Date().toISOString()}`);
console.log(`[KV] GET ${key} -> ${value ? "found" : "not found"}`);
console.log(`[AUTH] Failed attempt to access /api/admin`);
```

### Viewing Logs

```bash
npx wrangler tail
```

**Example log output:**
```
[REQUEST] GET /health - 2026-05-08T01:28:15.623Z
[REQUEST] GET /edge - 2026-05-08T01:28:15.799Z
[KV] PUT testKey = persistent-value
[KV] GET testKey -> found
[AUTH] Failed attempt to access /api/admin
```

### Cloudflare Dashboard Metrics

**Access:**
1. Login to Cloudflare Dashboard
2. Navigate to **Workers & Pages** → **lab17-worker**
3. Click **Analytics** tab

**Available Metrics:**
| Metric | Description |
|--------|-------------|
| Requests | Total request count over time |
| Request Duration | P50, P90, P99 latency percentiles |
| CPU Time | Execution time per request |
| Errors | 5xx status codes count |
| Throttling | Rate limiting events |

### Deployment History & Rollback

**List deployments:**
```bash
npx wrangler versions list
```

**Version history:**
| Version ID | Created | Status |
|------------|---------|--------|
| c455e1d3-5713-402f-89aa-86602973d751 | May 8, 2026 | Current |
| 2892d2af-5dcf-4d48-8ebb-cb82bd5896f0 | May 8, 2026 | Previous |

**Rollback command:**
```bash
npx wrangler rollback --version-id 2892d2af-5dcf-4d48-8ebb-cb82bd5896f0
```

**Or via Dashboard:**
- Workers & Pages → lab17-worker → Deployments
- Click "..." next to version → Rollback

---

## Task 6 — Documentation & Comparison (3 pts)

### Kubernetes vs Cloudflare Workers Comparison

| Aspect | Kubernetes | Cloudflare Workers |
|--------|------------|--------------------|
| **Setup Complexity** | High - cluster provisioning, kubectl, Helm, ingress controllers | Low - `npm create cloudflare`, one command |
| **Deployment Speed** | 30-120 seconds (image build + push + rollout) | 5-10 seconds (direct upload) |
| **Global Distribution** | Manual - must deploy to each region separately | Automatic - 300+ edge locations instantly |
| **Cost (small apps)** | $10-50/month (cluster overhead) | Free tier (100k requests/day) |
| **State Management** | Persistent Volumes, StatefulSets, external DBs | KV, D1, R2, external via fetch |
| **Runtime Flexibility** | Any container, any language, any binary | JS, TS, Python, Rust, Go (WASM) |
| **Cold Starts** | 100-1000ms (container start) | 5-10ms (kept warm) |
| **Execution Limit** | Unlimited (as long as pod runs) | 30 seconds (15 min for Queues) |
| **Memory Limit** | Node limit (~16-64GB typical) | 128MB (1GB on paid plan) |
| **Debugging** | kubectl logs, exec, port-forward | wrangler tail, dashboard logs |
| **Control** | Full OS, network, kernel control | Limited to Workers runtime |

### When to Use Kubernetes

✅ **Good candidates:**
- Long-running container workloads (web servers, APIs)
- Machine learning inference with GPU requirements
- Legacy applications in existing Docker images
- Complex stateful applications (distributed databases, Kafka)
- Regulatory requirements for specific geographic region
- Need for custom networking or kernel modules

❌ **Overkill for:**
- Simple APIs with variable traffic
- Static site backends
- A/B testing infrastructure

### When to Use Cloudflare Workers

✅ **Good candidates:**
- Globally distributed APIs needing low latency worldwide
- Serverless backends with spiky or unpredictable traffic
- JAMstack applications (form handling, auth, API routes)
- A/B testing and edge routing
- Rate limiting and request transformation at edge
- Image optimization and CDN logic

❌ **Not suitable for:**
- Long-running compute (over 30 seconds)
- Large memory workloads (>128MB on free tier)
- Applications requiring native binaries or system packages

### My Recommendation

**Choose Workers when:**
- Your users are distributed globally
- You want minimal operational overhead
- You're building a new API from scratch
- Traffic patterns are spiky or unpredictable
- You can keep execution under 30 seconds

**Choose Kubernetes when:**
- You have existing Docker containers
- Need full runtime flexibility
- Running stateful workloads
- Need GPU or specialized hardware
- Team already has Kubernetes expertise

### Reflection

**What felt easier than Kubernetes?**
1. **Deployment**: One command vs building images, pushing to registry, updating manifests
2. **Global distribution**: No region selection, no replication across zones
3. **Configuration**: Simple JSON vs complex Helm charts with dozens of YAML files
4. **Local development**: `wrangler dev` with hot reload vs `minikube` or `kind`
5. **Secrets management**: `wrangler secret put` vs Kubernetes Secrets with encryption setup
6. **Logs**: `wrangler tail` gives instant logs without EFK stack

**What felt more constrained?**
1. **Runtime limitations**: Only JS/TS/Python/Rust/WASM, no arbitrary binaries
2. **Execution time**: Hard 30-second limit (15 minutes for Queues)
3. **Memory**: Max 128MB requires careful optimization
4. **No local filesystem**: Must use KV, R2, or external services for persistence
5. **npm modules**: Only Workers-compatible modules work (no Node.js fs, net, etc.)
6. **Debugging**: Harder to attach debuggers or profile CPU performance

**What changed because Workers is not a Docker host?**
- **No Dockerfile**: Skipped writing image definitions and managing base images
- **No container registry**: Didn't push to Docker Hub, GHCR, or ECR
- **Different storage**: Used KV instead of persistent volumes or hostPath
- **Different logging**: `console.log()` goes to `wrangler tail`, not container logs
- **Different deployment**: Atomic global rollout vs rolling update across nodes
- **No orchestration**: No replica management, auto-scaling is built-in and automatic
- **Cold starts**: Significantly faster (5-10ms vs 100-1000ms)

## Deployment Commands Summary

```bash
# Initial setup
npm create cloudflare@latest lab17-worker -- --type=typescript
cd lab17-worker

# Authentication
npx wrangler login

# KV namespace creation
npx wrangler kv namespace create MY_KV

# Secrets
npx wrangler secret put API_SECRET
npx wrangler secret put ADMIN_TOKEN

# Local development
npx wrangler dev

# Deploy
npx wrangler deploy

# Logs
npx wrangler tail

# Rollback
npx wrangler rollback
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `wrangler login` doesn't open browser | Manually open https://dash.cloudflare.com and copy API token |
| KV namespace already exists | Use `wrangler kv namespace list` to get existing ID |
| Secret not working | Re-run `wrangler secret put` and redeploy |
| 404 on root path | Normal - Worker only handles specific endpoints |
| Edge metadata shows "unknown" | Request.cf requires HTTPS, some fields may be unavailable |

### Key Achievements
- Deployed globally distributed API on Cloudflare's edge network
- Implemented 8 HTTP endpoints including health, metadata, and KV operations
- Demonstrated edge metadata showing colo, country, city, and TLS information
- Configured secrets and environment variables for configuration management
- Used Workers KV for persistent storage across deployments
- Implemented logging and observed metrics in Cloudflare dashboard
- Performed versioned deployments with rollback capability
- Completed comprehensive comparison of Kubernetes vs Cloudflare Workers

**Worker URL:** https://lab17-worker.ak-lab17-worker.workers.dev

