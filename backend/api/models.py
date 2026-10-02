import uuid

from django.db import models


class DischargeDocument(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    filename = models.CharField(max_length=255)
    text = models.TextField()
    chunks = models.JSONField(default=list)
    summary = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)


class AgentSession(models.Model):
    session_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(DischargeDocument, on_delete=models.CASCADE, related_name="sessions")
    history = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)


class MedicationMention(models.Model):
    """Structured medication details extracted from one uploaded document."""

    document = models.ForeignKey(DischargeDocument, on_delete=models.CASCADE, related_name="medication_mentions")
    name = models.CharField(max_length=255)
    instructions = models.TextField(blank=True)
    duration = models.CharField(max_length=255, blank=True)
    timing = models.CharField(max_length=255, blank=True)
    source_page = models.PositiveIntegerField(null=True, blank=True)


class AIJob(models.Model):
    class Status(models.TextChoices):
        QUEUED = "queued", "Queued"
        RUNNING = "running", "Running"
        SUCCEEDED = "succeeded", "Succeeded"
        FAILED = "failed", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    kind = models.CharField(max_length=32)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.QUEUED)
    request_data = models.JSONField(default=dict)
    result = models.JSONField(null=True, blank=True)
    error = models.CharField(max_length=500, blank=True)
    correlation_id = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class LLMUsageLog(models.Model):
    correlation_id = models.CharField(max_length=64, db_index=True)
    feature = models.CharField(max_length=48)
    model = models.CharField(max_length=96)
    prompt_version = models.CharField(max_length=16, default="v1")
    input_tokens = models.PositiveIntegerField(default=0)
    output_tokens = models.PositiveIntegerField(default=0)
    estimated_cost_usd = models.DecimalField(max_digits=12, decimal_places=8, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
