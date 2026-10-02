"""Pydantic schemas for validating Gemini's structured PDF responses."""

from typing import Annotated, Any, Literal
from uuid import UUID

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field


def _text_or_blank(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, (str, int, float, bool)):
        return str(value)
    return value


def _list_or_empty(value: Any) -> Any:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value else []
    return value


Text = Annotated[str, BeforeValidator(_text_or_blank)]
TextList = Annotated[list[Text], BeforeValidator(_list_or_empty)]


class ResponseSchema(BaseModel):
    model_config = ConfigDict(extra="ignore")


class SourcePage(ResponseSchema):
    page: int = Field(default=1, ge=1)


class PatientDetails(ResponseSchema):
    name: Text = ""
    patientId: Text = ""
    age: Text = ""
    gender: Text = ""


class HospitalDetails(ResponseSchema):
    name: Text = ""
    department: Text = ""


class MedicationDetails(ResponseSchema):
    name: Text = ""
    instructions: Text = ""
    duration: Text = ""
    timing: Text = ""
    source: SourcePage | None = None


class FollowUpDetails(ResponseSchema):
    date: Text = ""
    department: Text = ""
    instructions: TextList = Field(default_factory=list)
    tests: TextList = Field(default_factory=list)
    source: SourcePage | None = None


class DischargeSummary(ResponseSchema):
    patient: PatientDetails = Field(default_factory=PatientDetails)
    hospital: HospitalDetails = Field(default_factory=HospitalDetails)
    admissionDate: Text = ""
    dischargeDate: Text = ""
    summary: Text
    importantInformation: TextList = Field(default_factory=list)
    medications: list[MedicationDetails] = Field(default_factory=list)
    followUp: FollowUpDetails = Field(default_factory=FollowUpDetails)
    instructions: TextList = Field(default_factory=list)
    missingInformation: TextList = Field(default_factory=list)


class OCRPage(ResponseSchema):
    page: int = Field(ge=1)
    text: Text = ""


class OCRExtraction(ResponseSchema):
    pages: list[OCRPage] = Field(default_factory=list)
    summary: DischargeSummary


class AgentCitation(ResponseSchema):
    page: int = Field(ge=1)


class AgentAnswer(ResponseSchema):
    answer: Text
    citations: list[AgentCitation] = Field(default_factory=list)
    requiresHumanReview: bool = False


class AgentQueryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    summaryId: UUID
    question: str = Field(min_length=1, max_length=2000)
    language: Literal["en", "ml", "ta", "hi"] = "en"
    sessionId: UUID | None = None


class TranslateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    summaryId: UUID
    language: Literal["en", "ml", "ta", "hi"]
