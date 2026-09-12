// api.client
// Thin fetch wrapper around the CyberSift backend. Same-origin in
// production; the Vite dev server proxies /api to localhost:8000.

async function request(path, options) {
  let res;
  try {
    res = await fetch(path, options);
  } catch {
    throw new Error("Could not reach the CyberSift API. Check your connection and try again.");
  }
  let body = null;
  try {
    body = await res.json();
  } catch {
    // non-JSON error body (e.g. a gateway timeout page)
  }
  if (!res.ok) {
    const detail = body && body.detail;
    throw new Error(
      typeof detail === "string"
        ? detail
        : res.status === 504
          ? "The extraction timed out — try a smaller document or fewer categories."
          : `Request failed (${res.status}).`
    );
  }
  return body;
}

export function getHealth() {
  return request("/api/health");
}

// Runs extraction over pasted text and/or an attached File.
export function extract({ text, file, categories, format }) {
  const form = new FormData();
  if (file) form.append("file", file);
  form.append("text", text || "");
  form.append("categories", categories.join(","));
  form.append("format", format || "auto");
  return request("/api/extract", { method: "POST", body: form });
}
