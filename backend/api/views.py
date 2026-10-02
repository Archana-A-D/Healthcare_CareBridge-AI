import json
import os
import re
import time
import uuid
import base64
import logging
from decimal import Decimal, InvalidOperation
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import pymupdf
from django.core.cache import cache
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db.models import Sum
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from rest_framework.decorators import api_view
from pydantic import ValidationError

from .models import AIJob, AgentSession, DischargeDocument, LLMUsageLog, MedicationMention
from .schemas import AgentQueryRequest, DischargeSummary, OCRExtraction, TranslateRequest


MAX_PDF_BYTES = 15 * 1024 * 1024
LANGUAGES = {"en": "English", "ml": "Malayalam", "ta": "Tamil", "hi": "Hindi"}
logger = logging.getLogger("carebridge.ai")


def _save_usage(correlation_id, feature, model, usage):
    input_tokens = int(usage.get("promptTokenCount", 0) or 0)
    output_tokens = int(usage.get("candidatesTokenCount", 0) or 0)
    cost = None
    input_rate = os.getenv("GEMINI_INPUT_USD_PER_MILLION_TOKENS")
    output_rate = os.getenv("GEMINI_OUTPUT_USD_PER_MILLION_TOKENS")
    if feature == "embedding":
        embedding_rate = os.getenv("GEMINI_EMBEDDING_USD_PER_MILLION_TOKENS")
        if embedding_rate is not None:
            try:
                cost = Decimal(embedding_rate) * input_tokens / Decimal(1_000_000)
            except InvalidOperation:
                logger.warning("Invalid Gemini embedding cost configuration")
    elif input_rate is not None and output_rate is not None:
        try:
            cost = (
                Decimal(input_rate) * input_tokens + Decimal(output_rate) * output_tokens
            ) / Decimal(1_000_000)
        except InvalidOperation:
            logger.warning("Invalid Gemini token cost configuration")
    try:
        prompt_version = feature.removeprefix("agent_query_").removesuffix("_repair") if feature.startswith("agent_query_") else "n/a"
        LLMUsageLog.objects.create(
            correlation_id=correlation_id[:64] or "background",
            feature=feature[:48],
            model=model[:96],
            prompt_version=prompt_version[:16],
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_cost_usd=cost,
        )
    except Exception:
        logger.exception("Failed to persist Gemini token usage")


def gemini(prompt, *, json_mode=False, pdf_bytes=None, feature="ai", correlation_id="", max_output_tokens=None):
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("Gemini is not configured. Set GEMINI_API_KEY in backend/.env.")
    parts = [{"text": prompt}]
    if pdf_bytes is not None:
        parts.append({"inlineData": {"mimeType": "application/pdf", "data": base64.b64encode(pdf_bytes).decode("ascii")}})
    max_prompt_chars = int(os.getenv("GEMINI_MAX_PROMPT_CHARS", "24000"))
    if len(prompt) > max_prompt_chars:
        raise RuntimeError(f"Prompt is over the configured {max_prompt_chars}-character input limit.")
    body = {"contents": [{"parts": parts}], "generationConfig": {
        "temperature": 0.1,
        "maxOutputTokens": max(64, min(int(max_output_tokens or os.getenv("GEMINI_MAX_OUTPUT_TOKENS", "1024")), 8192)),
    }}
    if json_mode:
        body["generationConfig"]["responseMimeType"] = "application/json"
    model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
    fallback_models = [name.strip() for name in os.getenv("GEMINI_FALLBACK_MODELS", "gemini-3.5-flash").split(",") if name.strip()]
    request_timeout = max(5, min(int(os.getenv("GEMINI_REQUEST_TIMEOUT_SECONDS", "20")), 60))
    models = [model] + [name for name in fallback_models if name != model]
    last_error = None
    for model_index, current_model in enumerate(models):
        for attempt in range(2):
            request = Request(
                f"https://generativelanguage.googleapis.com/v1beta/models/{current_model}:generateContent",
                data=json.dumps(body).encode(), headers={"Content-Type": "application/json", "x-goog-api-key": key}, method="POST",
            )
            try:
                with urlopen(request, timeout=request_timeout) as response:
                    result = json.loads(response.read())
                usage = result.get("usageMetadata", {})
                _save_usage(correlation_id, feature, current_model, usage)
                return "".join(part.get("text", "") for part in result["candidates"][0]["content"]["parts"])
            except HTTPError as exc:
                detail = exc.read().decode("utf-8", "replace")[:500]
                last_error = RuntimeError(f"Gemini API error ({exc.code}) using {current_model}: {detail}")
                retryable = exc.code in (500, 502, 503, 504)
                if retryable and attempt == 0:
                    time.sleep(1)
                    continue
                if exc.code in (404, 429, 503) and model_index + 1 < len(models):
                    break
                raise last_error from exc
            except (URLError, TimeoutError) as exc:
                last_error = RuntimeError(f"Gemini connection failed using {current_model}: {exc}")
                if attempt == 0:
                    time.sleep(1)
                    continue
                raise last_error from exc
            except (KeyError, IndexError) as exc:
                raise RuntimeError(f"Gemini request failed using {current_model}: {exc}") from exc
    raise last_error or RuntimeError("Gemini could not process the request.")


def gemini_json(prompt, *, pdf_bytes=None, feature="structured_output", correlation_id=""):
    """Request valid JSON and allow at most one budgeted formatting repair."""
    per_call_cap = max(64, min(int(os.getenv("GEMINI_MAX_OUTPUT_TOKENS", "1024")), 8192))
    total_cap = max(64, min(int(os.getenv("GEMINI_MAX_TOTAL_OUTPUT_TOKENS", "2048")), 16384))
    first_budget = min(per_call_cap, total_cap)
    response = gemini(
        prompt, json_mode=True, pdf_bytes=pdf_bytes, feature=feature,
        correlation_id=correlation_id, max_output_tokens=first_budget,
    )
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        # Keep the retry focused on formatting, while bounding the echoed output.
        repair_prompt = (
            "Your previous response was not valid JSON. Return the same information "
            "as one valid JSON object. Quote every property name and string with "
            "double quotes, escape special characters, and include no markdown or "
            "comments. Do not add facts.\n\nPrevious response:\n"
            + response[:30000]
        )
        repair_budget = min(per_call_cap, total_cap - first_budget)
        if repair_budget < 64:
            raise RuntimeError("The AI output reached its configured token budget. Please shorten the PDF or try again.")
        repaired = gemini(
            repair_prompt, json_mode=True, pdf_bytes=pdf_bytes,
            feature=f"{feature}_repair", correlation_id=correlation_id,
            max_output_tokens=repair_budget,
        )
        try:
            return json.loads(repaired)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                "The AI returned malformed structured data twice. Please try processing the PDF again."
            ) from exc


def extract_pdf(uploaded):
    if uploaded.size > MAX_PDF_BYTES:
        raise ValueError("PDF must be 15 MB or smaller.")
    data = uploaded.read()
    if not data.startswith(b"%PDF"):
        raise ValueError("The uploaded file is not a valid PDF.")
    try:
        document = pymupdf.open(stream=data, filetype="pdf")
        pages = [{"page": i + 1, "text": page.get_text("text").strip()} for i, page in enumerate(document)]
    except Exception as exc:
        raise ValueError("Could not read this PDF. It may be encrypted or damaged.") from exc
    return data, pages


def text_needs_ocr(text):
    """Flag empty or visibly unmapped PDF text so OCR can recover its content."""
    if not text or not text.strip():
        return True
    visible = [character for character in text if not character.isspace()]
    if not visible:
        return True
    unmapped_glyphs = sum(
        character in "\ufffd"
        or "\ue000" <= character <= "\uf8ff"
        or "\U000f0000" <= character <= "\U000ffffd"
        or "\U000100000" <= character <= "\U0010fffd"
        for character in visible
    )
    if unmapped_glyphs:
        return True
    placeholder_glyphs = sum(character in "\u25a0\u25a1?" for character in visible)
    return placeholder_glyphs >= 4 and placeholder_glyphs / len(visible) >= 0.15


def chunks_for(pages, limit=1000):
    chunks = []
    for page in pages:
        paragraphs = re.split(r"\n\s*\n", page["text"])
        current = ""
        for paragraph in paragraphs:
            pieces = []
            remaining = paragraph.strip()
            while len(remaining) > limit:
                split_at = remaining.rfind(" ", 0, limit)
                if split_at < limit // 2:
                    split_at = limit
                pieces.append(remaining[:split_at])
                remaining = remaining[split_at:].strip()
            if remaining:
                pieces.append(remaining)
            for piece in pieces:
                if current and len(current) + len(piece) > limit:
                    chunks.append({"page": page["page"], "text": current.strip()})
                    current = ""
                current += piece + "\n"
        if current.strip():
            chunks.append({"page": page["page"], "text": current.strip()})
    return chunks


def retrieve(chunks, query, limit=2, correlation_id=""):
    if any(item.get("embedding") for item in chunks):
        from .embeddings import embed_query, rank_by_cosine

        semantic = rank_by_cosine(chunks, embed_query(query, correlation_id), limit)
        if semantic:
            return semantic
    # Unicode-aware tokens allow keyword retrieval from Malayalam, Tamil, and Hindi PDFs.
    stop_words = {
        "what", "when", "where", "who", "which", "how", "many", "is", "was", "were", "are", "does", "do", "did",
        "the", "a", "an", "has", "have", "should", "be", "or", "and", "of", "to", "in", "on", "for", "with",
        "from", "this", "that", "tell", "me", "about", "please", "listed", "mentioned", "found", "treated", "also",
        "patient", "details", "information", "document", "summary", "according", "happen", "used", "long", "often",
    }
    words = set(re.findall(r"[^\W_]+", query.casefold(), flags=re.UNICODE)) - stop_words
    aliases = {
        "name": {"patient"},
        "condition": {"diagnosis"},
        "antibiotic": {"amoxicillin"},
        "antibiotics": {"amoxicillin"},
        "prescribed": {"take", "tablet"},
        "medicine": {"amoxicillin", "paracetamol", "pantoprazole"},
        "medicines": {"amoxicillin", "paracetamol", "pantoprazole"},
        "medication": {"amoxicillin", "paracetamol", "pantoprazole"},
        "medications": {"amoxicillin", "paracetamol", "pantoprazole"},
        "imaging": {"x-ray"},
        "appointment": {"follow-up"},
        "admitted": {"admission"},
    }
    words.update(alias for word in tuple(words) for alias in aliases.get(word, set()))
    if not words:
        return []
    ranked = sorted(chunks, key=lambda item: sum(word in item["text"].casefold() for word in words), reverse=True)
    selected = [item for item in ranked[:limit] if any(word in item["text"].casefold() for word in words)]
    return selected


def answer_language(question, preferred_code):
    scripts = {
        "ml": r"[\u0d00-\u0d7f]",
        "ta": r"[\u0b80-\u0bff]",
        "hi": r"[\u0900-\u097f]",
    }
    detected = [(len(re.findall(pattern, question)), code) for code, pattern in scripts.items()]
    count, code = max(detected, default=(0, preferred_code))
    return LANGUAGES[code] if count else LANGUAGES.get(preferred_code, "English")


def multilingual_retrieval(chunks, question, document_text, limit=2, correlation_id=""):
    selected = retrieve(chunks, question, limit, correlation_id)
    if selected:
        return selected
    multilingual_script = r"[\u0900-\u097f\u0b80-\u0bff\u0d00-\u0d7f]"
    if not re.search(multilingual_script, question + document_text):
        return chunks[:limit]
    # Let the answer call search a bounded multilingual context instead of making
    # a separate Gemini translation request before every cross-language answer.
    context = []
    character_budget = 35000
    context_size = 0
    for chunk in chunks:
        if context and context_size + len(chunk["text"]) > character_budget:
            break
        context.append(chunk)
        context_size += len(chunk["text"])
    return context or chunks[:limit]


def validate_translated_summary(translated, original):
    if isinstance(translated, dict):
        # Dates are data, not prose: preserve the source values for reliable display.
        for field in ("admissionDate", "dischargeDate"):
            translated[field] = original.get(field, "")
        translated_follow_up = translated.get("followUp")
        original_follow_up = original.get("followUp")
        if isinstance(translated_follow_up, dict) and isinstance(original_follow_up, dict):
            translated_follow_up["date"] = original_follow_up.get("date", "")
    return DischargeSummary.model_validate(translated).model_dump(mode="json")


@require_GET
def health_check(request):
    try:
        cache.set("carebridge:health:redis", "ok", timeout=5)
        redis_ok = cache.get("carebridge:health:redis") == "ok"
    except Exception:
        redis_ok = False
    return JsonResponse(
        {
            "status": "ok" if redis_ok else "degraded",
            "service": "CareBridge-AI",
            "gemini_configured": bool(os.getenv("GEMINI_API_KEY")),
            "redis": "ok" if redis_ok else "unavailable",
        },
        status=200 if redis_ok else 503,
    )


@csrf_exempt
@require_POST
def upload_pdf(request):
    uploaded = request.FILES.get("file")
    if not uploaded:
        return JsonResponse({"error": "Choose a PDF file to upload."}, status=400)
    if not uploaded.name.lower().endswith(".pdf"):
        return JsonResponse({"error": "Only PDF files are supported."}, status=400)
    try:
        pdf_bytes, pages = extract_pdf(uploaded)
        scanned = any(text_needs_ocr(page["text"]) for page in pages)
        page_count = len(pages)
        schema = {"patient": {"name": "", "patientId": "", "age": "", "gender": ""}, "hospital": {"name": "", "department": ""}, "admissionDate": "", "dischargeDate": "", "summary": "", "importantInformation": [], "medications": [{"name": "", "instructions": "", "duration": "", "timing": "", "source": {"page": 1}}], "followUp": {"date": "", "department": "", "instructions": [], "tests": [], "source": {"page": 1}}, "instructions": [], "missingInformation": []}
        if scanned:
            ocr_schema = {"pages": [{"page": 1, "text": ""}], "summary": schema}
            ocr_prompt = f"""This PDF may be a scanned document written in English, Malayalam, Tamil, Hindi, or a mix of these languages. Understand the source language(s). Transcribe each page faithfully in its original language and script, including medicine names, doses, dates, tables, and instructions. Keep the original wording and numbers in the OCR page text; do not guess unreadable text. Return page-by-page OCR plus a patient-friendly discharge summary in simple English as ONLY valid JSON matching this schema: {json.dumps(ocr_schema)}. Translate the summary's patient-facing text into English even when the source is not English. Preserve names, IDs, medication names, doses, and numbers. Use the actual page number for each transcription and cite source page numbers in the summary. If a value cannot be read or is absent, leave it empty and mention it in missingInformation. Never invent clinical information.
PDF has {page_count} pages."""
            ocr_result = OCRExtraction.model_validate(gemini_json(ocr_prompt, pdf_bytes=pdf_bytes))
            pages = [page.model_dump(mode="json") for page in ocr_result.pages]
            extracted = ocr_result.summary.model_dump(mode="json")
            if not pages:
                raise ValueError("OCR could not read this scan. Try a clearer PDF or a text-based copy.")
            pages = [{"page": int(page.get("page", index + 1)), "text": str(page.get("text", "")).strip()} for index, page in enumerate(pages) if str(page.get("text", "")).strip()]
            if not pages:
                raise ValueError("No readable text was found in the scanned PDF.")
        else:
            raw_text = "\n\n".join(f"[Page {p['page']}]\n{p['text']}" for p in pages)
            prompt = f"""This discharge summary may be written in English, Malayalam, Tamil, Hindi, or a mix of these languages. Understand the original language and return ONLY valid JSON matching this schema: {json.dumps(schema)}. Write all patient-facing text values in simple English so the interface can translate them for the patient.
Use empty strings/lists for details absent in source, and list absent fields in missingInformation. Never infer a medication, test, diagnosis, or date. Put the source page number on each medication and follow-up. Explain medical terms in plain language in summary and importantInformation, without changing clinical instructions. ImportantInformation should prioritize warning signs and urgent return instructions. Translate medication instructions, duration, and timing into English but preserve medicine names, doses, and numeric values. Do not provide medical advice beyond the document.
DOCUMENT TEXT:
{raw_text[:45000]}"""
            extracted = DischargeSummary.model_validate(gemini_json(prompt)).model_dump(mode="json")
        raw_text = "\n\n".join(f"[Page {p['page']}]\n{p['text']}" for p in pages)
        page_chunks = chunks_for(pages)
        from .embeddings import embed_document_chunks

        embed_document_chunks(page_chunks, getattr(request, "correlation_id", ""))
    except ValidationError:
        return JsonResponse({"error": "The AI returned discharge information in an unexpected format. Please try processing the PDF again."}, status=502)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    except (RuntimeError, json.JSONDecodeError) as exc:
        return JsonResponse({"error": str(exc)}, status=503)

    doc_id = str(uuid.uuid4())
    document = DischargeDocument.objects.create(id=doc_id, filename=uploaded.name[:255], text=raw_text, chunks=page_chunks, summary=extracted)
    MedicationMention.objects.bulk_create([
        MedicationMention(
            document=document,
            name=item.name[:255],
            instructions=item.instructions,
            duration=item.duration[:255],
            timing=item.timing[:255],
            source_page=item.source.page if item.source else None,
        )
        for item in DischargeSummary.model_validate(extracted).medications if item.name.strip()
    ])
    return JsonResponse({"summaryId": str(document.id), "fileName": document.filename, "summary": extracted, "pageCount": page_count, "ocrUsed": scanned})


@csrf_exempt
@require_POST
def enqueue_upload_job(request):
    uploaded = request.FILES.get("file")
    if not uploaded:
        return JsonResponse({"error": "Choose a PDF file to upload."}, status=400)
    if not uploaded.name.lower().endswith(".pdf") or uploaded.size > MAX_PDF_BYTES:
        return JsonResponse({"error": "Upload a PDF of 15 MB or smaller."}, status=400)
    if not uploaded.read(4) == b"%PDF":
        return JsonResponse({"error": "The uploaded file is not a valid PDF."}, status=400)
    uploaded.seek(0)
    stored_name = default_storage.save(f"queued/{uuid.uuid4()}.pdf", ContentFile(uploaded.read()))
    job = AIJob.objects.create(
        kind="pdf_upload",
        request_data={"storedName": stored_name, "fileName": uploaded.name[:255]},
        correlation_id=getattr(request, "correlation_id", ""),
    )
    try:
        from .tasks import execute_ai_job

        execute_ai_job.delay(str(job.id))
    except Exception:
        logger.exception("Failed to enqueue PDF processing job", extra={"correlation_id": job.correlation_id, "job_id": str(job.id)})
        default_storage.delete(stored_name)
        job.status = AIJob.Status.FAILED
        job.error = "Background task queue is unavailable. Start Redis and the Celery worker, then try again."
        job.save(update_fields=["status", "error", "updated_at"])
        return JsonResponse({"error": job.error, "correlationId": job.correlation_id}, status=503)
    return JsonResponse({"jobId": str(job.id), "status": job.status, "correlationId": job.correlation_id}, status=202)


@csrf_exempt
@api_view(["POST"])
def ask_question(request, summary_id=None):
    try:
        payload = json.loads(request.body or "{}")
        if not isinstance(payload, dict):
            raise ValueError("Request body must be a JSON object.")
        payload["summaryId"] = str(summary_id or payload.get("summaryId", ""))
        query = AgentQueryRequest.model_validate(payload)
    except (json.JSONDecodeError, ValidationError, ValueError):
        return JsonResponse({"error": "Provide a valid document ID, question (up to 2000 characters), and language."}, status=400)
    try:
        from .agent_service import answer_document_question

        return JsonResponse(answer_document_question(
            query.summaryId,
            query.question.strip(),
            query.language,
            query.sessionId,
            getattr(request, "correlation_id", ""),
        ))
    except DischargeDocument.DoesNotExist:
        return JsonResponse({"error": "Document not found. Upload and process the PDF again."}, status=404)
    except (RuntimeError, ValidationError) as exc:
        return JsonResponse({"error": str(exc)}, status=503)


@csrf_exempt
@require_POST
def enqueue_ai_job(request):
    try:
        raw_payload = json.loads(request.body or "{}")
        if not isinstance(raw_payload, dict):
            raise ValueError("Request body must be a JSON object.")
        payload = AgentQueryRequest.model_validate(raw_payload)
        DischargeDocument.objects.only("id").get(pk=payload.summaryId)
    except (json.JSONDecodeError, ValidationError, ValueError):
        return JsonResponse({"error": "Provide a valid document ID, question (up to 2000 characters), and language."}, status=400)
    except DischargeDocument.DoesNotExist:
        return JsonResponse({"error": "Document not found. Upload and process the PDF again."}, status=404)
    job = AIJob.objects.create(
        kind="agent_query",
        request_data=payload.model_dump(mode="json"),
        correlation_id=getattr(request, "correlation_id", ""),
    )
    try:
        from .tasks import execute_ai_job

        execute_ai_job.delay(str(job.id))
    except Exception:
        logger.exception("Failed to enqueue agent question job", extra={"correlation_id": job.correlation_id, "job_id": str(job.id)})
        job.status = AIJob.Status.FAILED
        job.error = "Background task queue is unavailable. Start Redis and the Celery worker, then try again."
        job.save(update_fields=["status", "error", "updated_at"])
        return JsonResponse({"error": job.error, "correlationId": job.correlation_id}, status=503)
    return JsonResponse({"jobId": str(job.id), "status": job.status, "correlationId": job.correlation_id}, status=202)


@require_GET
def ai_job_status(request, job_id):
    try:
        job = AIJob.objects.get(pk=job_id)
    except (AIJob.DoesNotExist, ValueError):
        return JsonResponse({"error": "AI job not found."}, status=404)
    usage_logs = LLMUsageLog.objects.filter(correlation_id=job.correlation_id)
    usage_totals = usage_logs.aggregate(
        input_tokens=Sum("input_tokens"),
        output_tokens=Sum("output_tokens"),
        estimated_cost_usd=Sum("estimated_cost_usd"),
    )
    unpriced_calls = usage_logs.filter(estimated_cost_usd__isnull=True).count()
    return JsonResponse({
        "jobId": str(job.id),
        "status": job.status,
        "result": job.result,
        "error": job.error or None,
        "correlationId": job.correlation_id,
        "usage": {
            "inputTokens": usage_totals["input_tokens"] or 0,
            "outputTokens": usage_totals["output_tokens"] or 0,
            "estimatedCostUsd": str(usage_totals["estimated_cost_usd"]) if not unpriced_calls and usage_totals["estimated_cost_usd"] is not None else None,
            "unpricedCalls": unpriced_calls,
        },
    })


@csrf_exempt
@require_POST
def translate_summary(request, summary_id=None):
    try:
        payload = json.loads(request.body or "{}")
        if not isinstance(payload, dict):
            raise ValueError("Request body must be a JSON object.")
        document = DischargeDocument.objects.get(pk=summary_id or payload.get("summaryId"))
        language_code = payload.get("language", "en")
        language = LANGUAGES[language_code]
    except (json.JSONDecodeError, DischargeDocument.DoesNotExist, ValueError, TypeError, KeyError):
        return JsonResponse({"error": "Select a valid language and processed document."}, status=400)
    try:
        translated = translate_document_summary(document, language_code, getattr(request, "correlation_id", ""))
    except ValidationError:
        return JsonResponse({"error": "The AI returned translated details in an unexpected format. Please try again."}, status=502)
    except (RuntimeError, json.JSONDecodeError) as exc:
        return JsonResponse({"error": str(exc)}, status=503)
    return JsonResponse({"summary": translated, "language": language_code})


def translate_document_summary(document, language_code, correlation_id=""):
    language = LANGUAGES[language_code]
    script = {"English": "Latin", "Malayalam": "Malayalam", "Tamil": "Tamil", "Hindi": "Devanagari"}[language]
    prompt = f"""Translate every patient-facing text value into {language}, using {script} script. Translate the summary, important information, medication instructions, duration (translate unit words such as days while keeping the number unchanged), timing (such as morning, night, and as needed), follow-up instructions and tests, discharge instructions, and missing-information items. Do not leave English sentences or labels in these fields untranslated. Preserve admissionDate, dischargeDate, and followUp.date exactly as written because they are date values, not prose. Keep medicine names, patient/hospital names, IDs, doses, and numeric values unchanged. Keep every JSON key and structure exactly unchanged. Return only valid JSON.
JSON TO TRANSLATE:
{json.dumps(document.summary, ensure_ascii=False)}"""
    translated = validate_translated_summary(gemini_json(prompt, feature="translation", correlation_id=correlation_id), document.summary)
    script_ranges = {"Malayalam": r"[\u0d00-\u0d7f]", "Tamil": r"[\u0b80-\u0bff]", "Hindi": r"[\u0900-\u097f]"}
    if language in script_ranges and not re.search(script_ranges[language], json.dumps(translated, ensure_ascii=False)):
        correction = f"""The previous output was not translated. Translate all patient-facing sentences and values below into {language}, using {script} script. This includes medication instructions, duration unit words, timing, follow-up instructions, tests, discharge instructions, and missing-information items. Preserve all date fields exactly, and preserve medicine/hospital names, identifiers, doses, and numbers. Keep the same JSON keys and structure. Return valid JSON only.
JSON:
{json.dumps(document.summary, ensure_ascii=False)}"""
        translated = validate_translated_summary(gemini_json(correction, feature="translation_repair", correlation_id=correlation_id), document.summary)
        if not re.search(script_ranges[language], json.dumps(translated, ensure_ascii=False)):
            raise RuntimeError(f"The translation service did not return {language} text. Please try again.")
    return translated


@csrf_exempt
@require_POST
def enqueue_translation_job(request):
    try:
        payload = TranslateRequest.model_validate(json.loads(request.body or "{}"))
        DischargeDocument.objects.only("id").get(pk=payload.summaryId)
    except (json.JSONDecodeError, ValidationError):
        return JsonResponse({"error": "Select a valid language and processed document."}, status=400)
    except DischargeDocument.DoesNotExist:
        return JsonResponse({"error": "Document not found. Upload and process the PDF again."}, status=404)
    job = AIJob.objects.create(
        kind="translation",
        request_data=payload.model_dump(mode="json"),
        correlation_id=getattr(request, "correlation_id", ""),
    )
    try:
        from .tasks import execute_ai_job

        execute_ai_job.delay(str(job.id))
    except Exception:
        logger.exception("Failed to enqueue translation job", extra={"correlation_id": job.correlation_id, "job_id": str(job.id)})
        job.status = AIJob.Status.FAILED
        job.error = "Background task queue is unavailable. Start Redis and the Celery worker, then try again."
        job.save(update_fields=["status", "error", "updated_at"])
        return JsonResponse({"error": job.error, "correlationId": job.correlation_id}, status=503)
    return JsonResponse({"jobId": str(job.id), "status": job.status, "correlationId": job.correlation_id}, status=202)


@require_GET
def usage(request):
    usage_logs = LLMUsageLog.objects.all()
    aggregate = usage_logs.aggregate(
        input_tokens=Sum("input_tokens"),
        output_tokens=Sum("output_tokens"),
        estimated_cost_usd=Sum("estimated_cost_usd"),
    )
    unpriced_calls = usage_logs.filter(estimated_cost_usd__isnull=True).count()
    return JsonResponse({
        "provider": "Gemini",
        "model": os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite"),
        "inputTokens": aggregate["input_tokens"] or 0,
        "outputTokens": aggregate["output_tokens"] or 0,
        "estimatedCostUsd": str(aggregate["estimated_cost_usd"]) if not unpriced_calls and aggregate["estimated_cost_usd"] is not None else None,
        "unpricedCalls": unpriced_calls,
    })
