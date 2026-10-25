// API_BASE can be overridden before this script loads, e.g. for a split
// deployment where the frontend is static (Cloudflare Pages) and the
// Python backend runs elsewhere:
//   <script>window.PHARMACY_API_BASE = "https://api.example.com/api";</script>
const DEFAULT_API_BASE = window.location.hostname.endsWith(".github.io") ? "./api" : "/api";
const API_BASE = (window.PHARMACY_API_BASE || DEFAULT_API_BASE).replace(/\/$/, "");

function apiError(body, status) {
  if (!window.PHARMACY_API_BASE && window.location.hostname.endsWith(".github.io")) {
    return new Error("واجهة GitHub Pages لا تشغّل الـBackend. انشر Flask على خدمة منفصلة واضبط PHARMACY_API_BASE.");
  }
  return new Error(body.error || `Request failed (${status})`);
}

async function apiGet(path) {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw apiError(body, res.status);
  }
  return res.json();
}

async function apiPost(path, body) {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: body instanceof FormData ? undefined : { "Content-Type": "application/json" },
    body: body instanceof FormData ? body : JSON.stringify(body || {}),
  });
  if (!res.ok) {
    const errBody = await res.json().catch(() => ({}));
    throw apiError(errBody, res.status);
  }
  return res.json();
}

async function apiUpload(path, formData) {
  const res = await fetch(`${API_BASE}${path}`, { method: "POST", body: formData });
  const json = await res.json().catch(() => ({}));
  if (!res.ok) throw apiError(json, res.status);
  return json;
}
