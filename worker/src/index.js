const JSON_HEADERS = {
  "content-type": "application/json; charset=utf-8",
  "cache-control": "no-store",
  "x-content-type-options": "nosniff",
  "x-frame-options": "DENY",
  "referrer-policy": "no-referrer",
};

function allowedOrigin(request, env) {
  const origin = request.headers.get("Origin");
  if (!origin) return true;
  const raw = (env.YASIN_ALLOWED_ORIGINS || "").split(",").map((x) => x.trim()).filter(Boolean);
  return raw.length === 0 || raw.includes(origin);
}

function headers(request, env) {
  const out = new Headers(JSON_HEADERS);
  const origin = request.headers.get("Origin");
  if (origin && allowedOrigin(request, env)) {
    out.set("access-control-allow-origin", origin);
    out.set("vary", "Origin");
  }
  return out;
}

function json(request, env, status, payload) {
  return new Response(JSON.stringify(payload), { status, headers: headers(request, env) });
}

function authorized(request, env) {
  const expected = env.YASIN_WORKER_API_KEY || "";
  if (!expected) return true;
  const supplied = (request.headers.get("Authorization") || "").replace(/^Bearer\s+/i, "").trim();
  return supplied.length > 0 && supplied === expected;
}

function limit(request, env) {
  const value = Number.parseInt(env.YASIN_MAX_BODY_BYTES || "1048576", 10);
  return Number.isFinite(value) ? Math.max(1024, Math.min(value, 16 * 1024 * 1024)) : 1048576;
}

function rateLimit(request, env) {
  const configured = Number.parseInt(env.YASIN_RATE_LIMIT_PER_MINUTE || "60", 10);
  if (!Number.isFinite(configured) || configured <= 0) return true;
  const key = request.headers.get("CF-Connecting-IP") || "anonymous";
  const bucket = Math.floor(Date.now() / 60000);
  const map = globalThis.__yasinRate || (globalThis.__yasinRate = new Map());
  const id = `${bucket}:${key}`;
  const count = (map.get(id) || 0) + 1;
  map.set(id, count);
  if (map.size > 2048) {
    for (const k of map.keys()) if (!k.startsWith(`${bucket}:`)) map.delete(k);
  }
  return count <= configured;
}

function upstream(env) {
  const base = (env.YASIN_UPSTREAM_URL || "").replace(/\/$/, "");
  if (!base) throw new Error("YASIN_UPSTREAM_URL is not configured");
  return base;
}

async function models(request, env) {
  const model = env.YASIN_MODEL || "auto";
  return json(request, env, 200, { object: "list", data: [{ id: model, name: model, provider: "remote", capabilities: ["chat"], default: true }] });
}

async function chat(request, env) {
  const max = limit(request, env);
  const length = Number.parseInt(request.headers.get("Content-Length") || "0", 10);
  if (length > max) return json(request, env, 413, { error: { code: "payload_too_large", message: "Request body is too large" } });
  const body = await request.arrayBuffer();
  if (body.byteLength > max) return json(request, env, 413, { error: { code: "payload_too_large", message: "Request body is too large" } });
  let payload;
  try { payload = JSON.parse(new TextDecoder().decode(body) || "{}"); } catch { return json(request, env, 400, { error: { code: "invalid_json", message: "Request body must be JSON" } }); }
  if (!payload || typeof payload !== "object" || Array.isArray(payload) || !Array.isArray(payload.messages)) {
    return json(request, env, 400, { error: { code: "invalid_request", message: "Request body must contain messages" } });
  }
  const target = `${upstream(env)}/v1/chat/completions`;
  const upstreamHeaders = new Headers({ "content-type": "application/json", accept: "application/json, text/event-stream" });
  if (env.YASIN_UPSTREAM_API_KEY) upstreamHeaders.set("authorization", `Bearer ${env.YASIN_UPSTREAM_API_KEY}`);
  const response = await fetch(target, { method: "POST", headers: upstreamHeaders, body: JSON.stringify(payload) });
  const out = new Response(response.body, { status: response.status, headers: new Headers(response.headers) });
  out.headers.set("cache-control", "no-store");
  out.headers.set("x-content-type-options", "nosniff");
  return out;
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (!allowedOrigin(request, env)) return json(request, env, 403, { error: { code: "origin_forbidden", message: "Origin is not allowed" } });
    if (request.method === "OPTIONS") {
      const h = headers(request, env);
      h.set("access-control-allow-headers", "Authorization, Content-Type");
      h.set("access-control-allow-methods", "GET, POST, OPTIONS");
      h.set("access-control-max-age", "600");
      return new Response(null, { status: 204, headers: h });
    }
    if (url.pathname === "/health" || url.pathname === "/api/status") return json(request, env, 200, { ok: true, service: "yasincoder-cloudflare-gateway" });
    if (!authorized(request, env)) return json(request, env, 401, { error: { code: "unauthorized", message: "Authentication required" } });
    if (!rateLimit(request, env)) return json(request, env, 429, { error: { code: "rate_limited", message: "Rate limit exceeded" } });
    try {
      if (request.method === "GET" && (url.pathname === "/v1/models" || url.pathname === "/api/models")) return models(request, env);
      if (request.method === "POST" && (url.pathname === "/v1/chat/completions" || url.pathname === "/api/chat")) return await chat(request, env);
      return json(request, env, 404, { error: { code: "not_found", message: "Route not found" } });
    } catch (error) {
      return json(request, env, 502, { error: { code: "upstream_error", message: "Configured upstream is unavailable" } });
    }
  },
};
