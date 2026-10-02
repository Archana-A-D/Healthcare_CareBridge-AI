"""Correlation logging and Redis-backed limits for expensive AI routes."""

import hashlib
import json
import logging
import os
import time
import uuid

from django.core.cache import cache
from django.http import JsonResponse


logger = logging.getLogger("carebridge.request")
AI_PATHS = {
    "/api/upload/": "upload",
    "/api/upload-jobs/": "upload",
    "/api/agent/query/": "agent_query",
    "/api/agent/jobs/": "agent_query_async",
    "/api/translation-jobs/": "translate_async",
}


class CorrelationAndRateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.limit = max(1, int(os.getenv("AI_RATE_LIMIT_PER_MINUTE", "60")))

    def __call__(self, request):
        correlation_id = request.headers.get("X-Correlation-ID", "")[:64]
        if not correlation_id or not all(char.isalnum() or char in "-_" for char in correlation_id):
            correlation_id = str(uuid.uuid4())
        request.correlation_id = correlation_id
        started = time.perf_counter()

        scope = AI_PATHS.get(request.path)
        if request.path.startswith("/api/discharge-summaries/") and request.path.endswith("/translate/"):
            scope = "translate"
        if scope and request.method == "POST":
            client_ip = request.META.get("HTTP_X_REAL_IP") or request.META.get("REMOTE_ADDR", "unknown")
            client_hash = hashlib.sha256(client_ip.encode("utf-8")).hexdigest()[:20]
            window = int(time.time() // 60)
            key = f"carebridge:rate:{scope}:{client_hash}:{window}"
            try:
                if not cache.add(key, 1, timeout=65):
                    count = cache.incr(key)
                else:
                    count = 1
                if count > self.limit:
                    response = JsonResponse(
                        {"error": "AI request limit reached. Wait a minute and try again.", "correlationId": correlation_id},
                        status=429,
                    )
                    response["Retry-After"] = str(60 - int(time.time() % 60))
                    return self._finish(request, response, started)
            except Exception:
                # Preserve local development availability if Redis is offline.
                logger.warning(json.dumps({"event": "rate_limit_cache_unavailable", "correlation_id": correlation_id}))

        response = self.get_response(request)
        return self._finish(request, response, started)

    @staticmethod
    def _finish(request, response, started):
        response["X-Correlation-ID"] = request.correlation_id
        logger.info(json.dumps({
            "event": "http_request",
            "correlation_id": request.correlation_id,
            "method": request.method,
            "path": request.path,
            "status": response.status_code,
            "duration_ms": round((time.perf_counter() - started) * 1000, 2),
        }))
        return response
