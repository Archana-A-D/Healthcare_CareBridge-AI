"""Small, deterministic tools used by the document-grounded discharge agent."""

import re

from .models import MedicationMention
def search_uploaded_document(document, question, correlation_id=""):
    if document.chunks and not any(chunk.get("embedding") for chunk in document.chunks):
        from .embeddings import embed_document_chunks

        if embed_document_chunks(document.chunks, correlation_id):
            document.save(update_fields=["chunks"])
    from .views import multilingual_retrieval

    chunks = multilingual_retrieval(document.chunks, question, document.text, correlation_id=correlation_id)
    return [
        {"page": int(chunk["page"]), "text": chunk["text"][:4000]}
        for chunk in chunks
    ]


def lookup_document_medications(document):
    """Read the parsed medication table; never derive or recommend a dose."""
    return list(
        MedicationMention.objects.filter(document=document)
        .order_by("source_page", "id")
        .values("name", "instructions", "duration", "timing", "source_page")
    )


def lookup_follow_up_tests(document):
    details = document.summary.get("followUp", {})
    return [str(item) for item in details.get("tests", []) if str(item).strip()]


RED_FLAG_PATTERNS = (
    r"\b(chest pain|cannot breathe|can't breathe|trouble breathing|severe bleeding|unconscious|fainted|stroke symptoms|suicid\w*)\b",
    r"(\u0d28\u0d46\u0d1e\u0d4d\u0d1a\u0d4d\u0d1a\u0d41\s*\u0d35\u0d47\u0d26\u0d28|\u0d36\u0d4d\u0d35\u0d3e\u0d38\u0d02\s*\u0d2e\u0d41\u0d1f\u0d4d\u0d1f\u0d32\u0d4d|\u0d2c\u0d4b\u0d27\u0d02\s*\u0d15\u0d46\u0d1f\u0d4d\u0d1f|\u0d30\u0d15\u0d4d\u0d24\u0d38\u0d4d\u0d30\u0d3e\u0d35)",
    r"(\u0ba8\u0bc6\u0b9e\u0bcd\u0b9a\u0bc1\s*\u0bb5\u0bb2\u0bbf|\u0bae\u0bc2\u0b9a\u0bcd\u0b9a\u0bc1\u0ba4\u0bcd\u0ba4\u0bbf\u0ba3\u0bb1\u0bb2|\u0bae\u0baf\u0b95\u0bcd\u0b95\u0bae|\u0b87\u0bb0\u0ba4\u0bcd\u0ba4\u0baa\u0bcd\u0baa\u0bcb\u0b95\u0bcd\u0b95\u0bc1)",
    r"(\u0938\u0940\u0928\u0947\s*\u092e\u0947\u0902\s*\u0926\u0930\u094d\u0926|\u0938\u093e\u0902\u0938\s*\u0932\u0947\u0928\u0947\s*\u092e\u0947\u0902\s*\u0915\u0920\u093f\u0928\u093e\u0908|\u092c\u0947\u0939\u094b\u0936|\u0916\u0942\u0928\s*\u092c\u0939\u0928\u093e)",
)

HIGH_FEVER_PATTERNS = (
    r"\b104\s*[\W_]?\s*f\b",
    r"\b40\s*[\W_]?\s*c\b",
)
DOSE_ADVICE_PATTERNS = (
    r"\b(?:how much|what dose|what dosage|how many (?:tablets|pills|ml)|how often should (?:i|my child))\b.{0,100}\b(?:paracetamol|acetaminophen|medicine|medication|antibiotic|drug)\b",
    r"\b(?:paracetamol|acetaminophen|medicine|medication|antibiotic|drug)\b.{0,100}\b(?:how much|what dose|what dosage|how many (?:tablets|pills|ml)|should (?:i|my child) take)\b",
)


def flag_for_human_review(question):
    """Escalate red flags and requests for individualized dosing before calling an LLM."""
    text = question.casefold()
    if any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in DOSE_ADVICE_PATTERNS):
        return {
            "requiresHumanReview": True,
            "type": "dose_advice",
            "reason": "Individualized medication dosing request",
        }
    if any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in HIGH_FEVER_PATTERNS):
        return {
            "requiresHumanReview": True,
            "type": "high_fever",
            "reason": "High fever wording requires clinician review",
        }
    matches = [pattern for pattern in RED_FLAG_PATTERNS if re.search(pattern, text, flags=re.IGNORECASE)]
    return {
        "requiresHumanReview": bool(matches),
        "type": "urgent_symptom" if matches else "",
        "reason": "Potential urgent symptom wording" if matches else "",
    }


def plan_document_tools(question):
    """Plan no more than three deterministic tool steps for one agent turn."""
    text = question.casefold()
    plan = ["search_uploaded_document"]
    medication_terms = r"(medic|drug|dose|tablet|pill|prescri|\u0d2e\u0d30\u0d41\u0d28\u0d4d\u0d28\u0d4d|\u0d17\u0d41\u0d33\u0d3f\u0d15|\u0bae\u0bb0\u0bc1\u0ba8\u0bcd\u0ba4\u0bc1|\u0bae\u0bbe\u0ba4\u0bcd\u0ba4\u0bbf\u0bb0\u0bc8|\u0926\u0935\u093e|\u0917\u094b\u0932\u0940)"
    follow_up_terms = r"(follow|appointment|test|x-ray|blood|review|\u0d2a\u0d30\u0d3f\u0d36\u0d4b\u0d27\u0d28|\u0ba4\u0bca\u0b9f\u0bb0\u0bcd\u0baa\u0bb0\u0bbf\u0b9a\u0bcb\u0ba4\u0ba9\u0bc8|\u092b\u0949\u0932\u094b|\u091c\u093e\u0902\u091a|\u092a\u0930\u0940\u0915\u094d\u0937\u0923)"
    if re.search(medication_terms, text) or re.search(follow_up_terms, text):
        plan.append("lookup_structured_records")
    plan.append("flag_for_human_review")
    return plan


def run_document_tools(document, question, correlation_id=""):
    # Escalate risky input before retrieval/embedding and before any model call.
    escalation = flag_for_human_review(question)
    if escalation["requiresHumanReview"]:
        return {
            "retrievedExcerpts": [], "medicationTable": [], "followUpTests": [],
            "escalation": escalation, "executionPlan": ["flag_for_human_review"],
        }
    plan = plan_document_tools(question)
    result = {"retrievedExcerpts": [], "medicationTable": [], "followUpTests": [], "escalation": {"requiresHumanReview": False, "reason": ""}}
    for tool in plan:
        if tool == "search_uploaded_document":
            result["retrievedExcerpts"] = search_uploaded_document(document, question, correlation_id)
        elif tool == "lookup_structured_records":
            result["medicationTable"] = lookup_document_medications(document)
            result["followUpTests"] = lookup_follow_up_tests(document)
        elif tool == "flag_for_human_review":
            result["escalation"] = escalation
    if len(plan) > 3:
        raise RuntimeError("Agent tool plan exceeded the three-step limit.")
    result["executionPlan"] = plan
    return result
