const API_BASE = import.meta.env.VITE_API_BASE_URL || "/api";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, options);
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.error || `Request failed (${response.status})`);
  return data;
}

export async function uploadDischargeSummary(file) {
  const form = new FormData();
  form.append("file", file);
  const job = await request("/upload-jobs/", { method: "POST", body: form });
  return pollAIJob(job.jobId);
}

async function pollAIJob(jobId) {
  const deadline = Date.now() + 210_000;
  while (Date.now() < deadline) {
    await new Promise((resolve) => window.setTimeout(resolve, 1000));
    const job = await request(`/agent/jobs/${jobId}/`);
    if (job.status === "succeeded") return { ...job.result, usage: job.usage };
    if (job.status === "failed") throw new Error(job.error || `AI job failed (${job.correlationId || jobId})`);
  }
  throw new Error(`AI job is taking too long. Reference: ${jobId}`);
}

export async function askQuestion(summaryId, question, language = "en", sessionId = null) {
  const job = await request("/agent/jobs/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ summaryId, question, language, sessionId }),
  });
  return pollAIJob(job.jobId);
}

export async function translateSummary(summaryId, language) {
  const job = await request("/translation-jobs/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ summaryId, language }),
  });
  return pollAIJob(job.jobId);
}
