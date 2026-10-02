"""CareBridge-AI load profile. AI calls are opt-in to avoid surprise API usage."""

import json
import os
from pathlib import Path
import time

from gevent import sleep

from locust import HttpUser, between, task
from redis import Redis
from redis.exceptions import RedisError


class CareBridgeUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        self.summary_id = os.getenv("LOAD_TEST_SUMMARY_ID", "").strip()
        self.session_id = None
        self.document_queries = 0
        self.pdf_path = os.getenv("LOAD_TEST_PDF", "").strip()
        self.uploaded_this_run = False
        self.redis = Redis.from_url(os.getenv("LOAD_TEST_REDIS_URL", "redis://redis:6379/0"), socket_timeout=2)
        self.redis_key = f"carebridge:loadtest:{id(self)}"

    def on_stop(self):
        try:
            self.redis.delete(self.redis_key)
        except RedisError:
            pass
        self.redis.close()

    @task(2)
    def redis_round_trip(self):
        """Measure Redis directly; /api/health/ separately measures it through Django."""
        started = time.perf_counter()
        error = None
        try:
            self.redis.set(self.redis_key, "ok", ex=60)
            if self.redis.get(self.redis_key) != b"ok":
                raise RuntimeError("Redis SET/GET returned an unexpected value")
        except (RedisError, RuntimeError) as exc:
            error = exc
        self.environment.events.request.fire(
            request_type="REDIS",
            name="Redis SET/GET",
            response_time=(time.perf_counter() - started) * 1000,
            response_length=0,
            exception=error,
            context={},
        )

    @task(6)
    def health(self):
        self.client.get("/api/health/", name="GET /api/health/")

    @task(2)
    def usage(self):
        self.client.get("/api/agent/usage/", name="GET /api/agent/usage/")

    @task(2)
    def ask_about_document(self):
        # Requires a previously uploaded summary. Each request invokes Gemini.
        query_limit = max(0, int(os.getenv("LOAD_TEST_QUERY_LIMIT_PER_USER", "1")))
        if not self.summary_id or self.document_queries >= query_limit:
            return
        self.document_queries += 1
        query_started = time.perf_counter()
        asynchronous = os.getenv("LOAD_TEST_ASYNC", "1") == "1"
        response = self.client.post(
            "/api/agent/jobs/" if asynchronous else "/api/agent/query/",
            json={
                "summaryId": self.summary_id,
                "question": "What medicines are mentioned?",
                "language": "en",
                "sessionId": self.session_id,
            },
            name="POST /api/agent/jobs/ [Gemini]" if asynchronous else "POST /api/agent/query/ [Gemini]",
        )
        if response.ok:
            try:
                payload = response.json()
                if asynchronous:
                    job_id = payload["jobId"]
                    deadline = time.monotonic() + 210
                    while time.monotonic() < deadline:
                        sleep(1)
                        job_response = self.client.get(f"/api/agent/jobs/{job_id}/", name="GET /api/agent/jobs/:id/")
                        if not job_response.ok:
                            break
                        job = job_response.json()
                        if job["status"] == "succeeded":
                            self.session_id = (job.get("result") or {}).get("sessionId", self.session_id)
                            self.environment.events.request.fire(
                                request_type="AGENT",
                                name="Document query end-to-end",
                                response_time=(time.perf_counter() - query_started) * 1000,
                                response_length=0,
                                exception=None,
                                context={},
                            )
                            break
                        if job["status"] == "failed":
                            error = job.get("error") or "AI job failed"
                            response.failure(error)
                            self.environment.events.request.fire(
                                request_type="AGENT",
                                name="Document query end-to-end",
                                response_time=(time.perf_counter() - query_started) * 1000,
                                response_length=0,
                                exception=RuntimeError(error),
                                context={},
                            )
                            break
                    else:
                        response.failure("AI job exceeded 210 seconds")
                        self.environment.events.request.fire(
                            request_type="AGENT",
                            name="Document query end-to-end",
                            response_time=(time.perf_counter() - query_started) * 1000,
                            response_length=0,
                            exception=TimeoutError("AI job exceeded 210 seconds"),
                            context={},
                        )
                else:
                    self.session_id = payload.get("sessionId", self.session_id)
            except (ValueError, AttributeError):
                response.failure("API returned invalid JSON")

    @task(1)
    def upload_pdf(self):
        # Opt-in and only once per virtual user; each upload invokes Gemini.
        if not self.pdf_path or self.uploaded_this_run:
            return
        pdf_path = Path(self.pdf_path)
        if not pdf_path.is_file():
            self.environment.runner.quit()
            raise FileNotFoundError(
                f"LOAD_TEST_PDF={self.pdf_path!r} is not mounted in the Locust container."
            )
        asynchronous = os.getenv("LOAD_TEST_ASYNC", "1") == "1"
        with pdf_path.open("rb") as pdf_file:
            response = self.client.post(
                "/api/upload-jobs/" if asynchronous else "/api/upload/",
                files={"file": (pdf_path.name, pdf_file, "application/pdf")},
                name="POST /api/upload-jobs/ [Gemini]" if asynchronous else "POST /api/upload/ [Gemini]",
            )
        self.uploaded_this_run = True
        if response.ok:
            try:
                payload = response.json()
                if asynchronous:
                    job_id = payload["jobId"]
                    deadline = time.monotonic() + 210
                    while time.monotonic() < deadline:
                        sleep(1)
                        job_response = self.client.get(f"/api/agent/jobs/{job_id}/", name="GET /api/agent/jobs/:id/")
                        if not job_response.ok:
                            break
                        job = job_response.json()
                        if job["status"] == "succeeded":
                            self.summary_id = (job.get("result") or {}).get("summaryId", self.summary_id)
                            break
                        if job["status"] == "failed":
                            response.failure(job.get("error") or "PDF job failed")
                            break
                    else:
                        response.failure("PDF job exceeded 210 seconds")
                else:
                    self.summary_id = payload.get("summaryId", self.summary_id)
            except (ValueError, AttributeError):
                response.failure("API returned invalid JSON")

    @task(1)
    def translate_summary(self):
        # Set LOAD_TEST_TRANSLATION=1 and a summary ID to opt into paid AI calls.
        if not self.summary_id or os.getenv("LOAD_TEST_TRANSLATION", "0") != "1":
            return
        response = self.client.post(
            "/api/translation-jobs/",
            data=json.dumps({"summaryId": self.summary_id, "language": "ta"}),
            headers={"Content-Type": "application/json"},
            name="POST /api/translation-jobs/ [Gemini]",
        )
        if not response.ok:
            return
        try:
            job_id = response.json()["jobId"]
        except (ValueError, KeyError, AttributeError):
            response.failure("Translation job response had no jobId")
            return
        deadline = time.monotonic() + 210
        while time.monotonic() < deadline:
            sleep(1)
            job_response = self.client.get(
                f"/api/agent/jobs/{job_id}/", name="GET /api/agent/jobs/:id/ [translation]"
            )
            if not job_response.ok:
                response.failure("Could not poll translation job")
                return
            try:
                job = job_response.json()
            except ValueError:
                response.failure("Translation job status was invalid JSON")
                return
            if job.get("status") == "succeeded":
                return
            if job.get("status") == "failed":
                response.failure(job.get("error") or "Translation job failed")
                return
        response.failure("Translation job exceeded 210 seconds")
