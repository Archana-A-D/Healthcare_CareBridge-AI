# Five-minute demo plan

## Named user and problem

The primary user is a ward nurse preparing a patient-friendly discharge handoff. Discharge documents often combine abbreviations, medication instructions, follow-up tests, and warning signs across several pages. CareBridge-AI organizes the document so the nurse can explain it clearly with the source page visible.

## Timed walkthrough

| Time | Demo |
| --- | --- |
| 0:00–0:40 | State the user and problem. The system explains one uploaded discharge document; it is not a diagnosis or prescribing service. |
| 0:40–1:25 | Upload the repository's synthetic discharge PDF. Show the queued job and extracted patient overview. |
| 1:25–2:15 | Review medication schedule, follow-up tests, instructions, important alerts, and missing details. Compare each item with its cited source page. |
| 2:15–3:00 | Ask a question grounded in the document. Show the answer and citation, then ask about a fact that is absent and show that the agent says it is not stated. |
| 3:00–3:35 | Ask the adversarial high-fever dosing question. Show that the deterministic escalation returns a localized human-review message without calling Gemini. |
| 3:35–4:20 | Explain the architecture: Django/DRF, Pydantic schemas, MySQL document/session/job data, Redis/Celery async work, page-aware RAG, and deterministic tools. |
| 4:20–5:00 | State evidence and limits: the synthetic 20-question retrieval result and the 20-user health/usage baseline are documented separately. AI answer scores, AI-workload load, clinical validation, authentication, and cloud deployment are not claimed. |

## Q&A evidence

- **Where did this fact come from?** Use the answer's page citation and compare it to the original PDF pane.
- **What if the answer is missing from the PDF?** The prompt requires the agent to say the document is silent; retrieved-page validation prevents citations to pages that were not retrieved.
- **Can the agent give a dose or diagnosis?** No. The shared prompt guardrails and deterministic high-risk escalation prohibit that behavior.
- **What did the load test prove?** A five-minute, 20-user baseline for health and usage endpoints only. It did not exercise Gemini, upload, or Celery AI jobs.
- **What is the answer evaluation score?** The offline run measures retrieval only. Generated-answer and citation evaluation is implemented in the opt-in harness but must be run with Gemini before quoting those scores.

Use synthetic documents in the demo. Do not present this prototype as clinically validated or use it to make treatment decisions.
