import logging
import json

from celery import shared_task
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory

from .agent_service import answer_document_question
from .models import AIJob, DischargeDocument


logger = logging.getLogger("carebridge.ai")


@shared_task(name="api.execute_ai_job", ignore_result=True)
def execute_ai_job(job_id):
    try:
        job = AIJob.objects.get(pk=job_id)
    except AIJob.DoesNotExist:
        logger.error("AI job does not exist", extra={"correlation_id": str(job_id)})
        return

    job.status = AIJob.Status.RUNNING
    job.save(update_fields=["status", "updated_at"])
    try:
        payload = job.request_data
        if job.kind == "agent_query":
            result = answer_document_question(
                payload["summaryId"],
                payload["question"],
                payload.get("language", "en"),
                payload.get("sessionId"),
                job.correlation_id,
            )
        elif job.kind == "translation":
            from .views import translate_document_summary

            document = DischargeDocument.objects.get(pk=payload["summaryId"])
            translated = translate_document_summary(document, payload["language"], job.correlation_id)
            result = {"summaryId": payload["summaryId"], "language": payload["language"], "summary": translated}
        elif job.kind == "pdf_upload":
            try:
                with default_storage.open(payload["storedName"], "rb") as pdf_file:
                    uploaded = SimpleUploadedFile(payload["fileName"], pdf_file.read(), content_type="application/pdf")
                internal_request = RequestFactory().post("/api/upload/", {"file": uploaded})
                internal_request.correlation_id = job.correlation_id
                from .views import upload_pdf

                response = upload_pdf(internal_request)
                if response.status_code >= 400:
                    details = json.loads(response.content.decode("utf-8"))
                    raise RuntimeError(details.get("error", "PDF processing failed."))
                result = json.loads(response.content.decode("utf-8"))
            finally:
                default_storage.delete(payload["storedName"])
        else:
            raise ValueError("Unsupported background AI job type.")
        job.result = result
        job.status = AIJob.Status.SUCCEEDED
        job.error = ""
    except Exception as exc:
        job.status = AIJob.Status.FAILED
        job.error = str(exc)[:500]
        logger.exception("Background AI job failed", extra={"correlation_id": job.correlation_id, "job_id": str(job.id)})
    job.save(update_fields=["result", "status", "error", "updated_at"])
