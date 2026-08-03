const API_BASE = window.STATUTA_API_BASE || "http://localhost:8000";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: options.body instanceof FormData ? {} : { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      detail = body.detail || JSON.stringify(body);
    } catch (_) {
      /* ignore */
    }
    throw new Error(`${response.status}: ${detail}`);
  }
  return response;
}

export async function sendChatMessage(userId, message, language) {
  const res = await request("/api/chat", {
    method: "POST",
    body: JSON.stringify({ user_id: userId, message, language }),
  });
  return res.json();
}

export async function uploadDocument(userId, docType, file) {
  const form = new FormData();
  form.append("file", file);
  const res = await request(
    `/api/documents/upload?user_id=${encodeURIComponent(userId)}&doc_type=${encodeURIComponent(docType)}`,
    { method: "POST", body: form }
  );
  return res.json();
}

export async function createGapReport(userId, companyProfile) {
  const res = await request("/api/reports/gap-report", {
    method: "POST",
    body: JSON.stringify({ user_id: userId, company_profile: companyProfile }),
  });
  return res.json();
}

export async function getDraftSections(reportId) {
  const res = await request(`/api/reports/gap-report/${reportId}/draft-annex-iv/sections`);
  return res.json();
}

export function downloadAnnexIvUrl(reportId) {
  return `${API_BASE}/api/reports/gap-report/${reportId}/draft-annex-iv`;
}

export async function checkHealth() {
  try {
    const res = await fetch(`${API_BASE}/health`);
    return res.ok;
  } catch (_) {
    return false;
  }
}
