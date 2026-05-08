export interface Env {
  // Variables from wrangler.jsonc
  APP_NAME: string;
  APP_VERSION: string;
  API_VERSION: string;
  DEFAULT_LANG: string;
  
  // Secrets (encrypted)
  API_SECRET: string;
  ADMIN_TOKEN: string;
  
  // KV Namespace
  MY_KV: KVNamespace;
}

export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);
    const method = request.method;
    const path = url.pathname;
    
    // Log all requests for observability
    console.log(`[REQUEST] ${method} ${path} - ${new Date().toISOString()}`);
    
    // CORS headers for all responses
    const corsHeaders = {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type, Authorization",
      "Content-Type": "application/json",
    };
    
    // Handle preflight CORS
    if (method === "OPTIONS") {
      return new Response(null, { headers: corsHeaders, status: 204 });
    }
    
    try {
      // ========== ROUTE: GET /health ==========
      if (path === "/health" && method === "GET") {
        return new Response(
          JSON.stringify({
            status: "healthy",
            timestamp: new Date().toISOString(),
            version: env.APP_VERSION,
            uptime: "running",
          }),
          { headers: corsHeaders, status: 200 }
        );
      }
      
      // ========== ROUTE: GET /metadata ==========
      if (path === "/metadata" && method === "GET") {
        return new Response(
          JSON.stringify({
            appName: env.APP_NAME,
            version: env.APP_VERSION,
            apiVersion: env.API_VERSION,
            defaultLanguage: env.DEFAULT_LANG,
            runtime: "Cloudflare Workers",
            deployedAt: new Date().toISOString(),
            region: "global-edge",
            endpoints: [
              "GET /health",
              "GET /metadata",
              "GET /edge",
              "GET /api/hello?name=X",
              "POST /api/echo",
              "GET /api/kv?key=X",
              "POST /api/kv",
              "GET /api/admin",
            ],
          }),
          { headers: corsHeaders, status: 200 }
        );
      }
      
      // ========== ROUTE: GET /edge (Edge Metadata) ==========
      if (path === "/edge" && method === "GET") {
        const cf = request.cf;
        
        return new Response(
          JSON.stringify({
            colo: cf?.colo || "unknown",
            country: cf?.country || "unknown",
            asn: cf?.asn || "unknown",
            city: cf?.city || "unknown",
            httpProtocol: cf?.httpProtocol || "unknown",
            tlsVersion: cf?.tlsVersion || "unknown",
            region: cf?.region || "unknown",
            timezone: cf?.timezone || "unknown",
            longitude: cf?.longitude || "unknown",
            latitude: cf?.latitude || "unknown",
            requestId: cf?.requestId || "unknown",
          }),
          { headers: corsHeaders, status: 200 }
        );
      }
      
      // ========== ROUTE: GET /api/hello ==========
      if (path === "/api/hello" && method === "GET") {
        const name = url.searchParams.get("name") || "World";
        return new Response(
          JSON.stringify({
            message: `Hello, ${name}!`,
            timestamp: new Date().toISOString(),
            language: env.DEFAULT_LANG,
          }),
          { headers: corsHeaders, status: 200 }
        );
      }
      
      // ========== ROUTE: POST /api/echo ==========
      if (path === "/api/echo" && method === "POST") {
        const body = await request.json();
        return new Response(
          JSON.stringify({
            echo: body,
            receivedAt: new Date().toISOString(),
          }),
          { headers: corsHeaders, status: 200 }
        );
      }
      
      // ========== ROUTE: KV Operations ==========
      // GET /api/kv?key=xxx - Retrieve value
      if (path === "/api/kv" && method === "GET") {
        const key = url.searchParams.get("key");
        if (!key) {
          return new Response(
            JSON.stringify({ error: "Missing 'key' parameter" }),
            { headers: corsHeaders, status: 400 }
          );
        }
        
        const value = await env.MY_KV.get(key);
        console.log(`[KV] GET ${key} -> ${value ? "found" : "not found"}`);
        
        return new Response(
          JSON.stringify({ key, value }),
          { headers: corsHeaders, status: 200 }
        );
      }
      
      // POST /api/kv - Store key-value pair
      if (path === "/api/kv" && method === "POST") {
        const body = await request.json() as { key: string; value: string };
        if (!body.key || !body.value) {
          return new Response(
            JSON.stringify({ error: "Missing 'key' or 'value'" }),
            { headers: corsHeaders, status: 400 }
          );
        }
        
        await env.MY_KV.put(body.key, body.value);
        console.log(`[KV] PUT ${body.key} = ${body.value}`);
        
        return new Response(
          JSON.stringify({ success: true, key: body.key }),
          { headers: corsHeaders, status: 200 }
        );
      }
      
      // ========== ROUTE: GET /api/admin (requires auth) ==========
      if (path === "/api/admin" && method === "GET") {
        const authHeader = request.headers.get("Authorization");
        
        if (authHeader !== `Bearer ${env.ADMIN_TOKEN}`) {
          console.log(`[AUTH] Failed attempt to access /api/admin`);
          return new Response(
            JSON.stringify({ error: "Unauthorized" }),
            { headers: corsHeaders, status: 401 }
          );
        }
        
        return new Response(
          JSON.stringify({
            message: "Admin access granted",
            secretAvailable: env.API_SECRET ? true : false,
            timestamp: new Date().toISOString(),
          }),
          { headers: corsHeaders, status: 200 }
        );
      }
      
      // ========== 404 Not Found ==========
      return new Response(
        JSON.stringify({
          error: "Not Found",
          path: path,
          method: method,
          availableEndpoints: [
            "GET /health",
            "GET /metadata", 
            "GET /edge",
            "GET /api/hello?name=YourName",
            "POST /api/echo",
            "GET /api/kv?key=mykey",
            "POST /api/kv (body: {key, value})",
            "GET /api/admin (with Bearer token)",
          ],
        }),
        { headers: corsHeaders, status: 404 }
      );
      
    } catch (error) {
      console.error(`[ERROR] ${path}: ${error.message}`);
      return new Response(
        JSON.stringify({ error: "Internal Server Error", details: error.message }),
        { headers: corsHeaders, status: 500 }
      );
    }
  },
} satisfies ExportedHandler<Env>;
