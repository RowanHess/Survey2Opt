from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Literal

from pydantic import BaseModel, Field, model_validator


class SurveyQuestion(BaseModel):
    id: str
    text: str


class SurveyDefinition(BaseModel):
    id: str
    respondent_type: str
    questions: list[SurveyQuestion]


class SurveyResponse(BaseModel):
    entity_id: str
    entity_type: str
    survey_id: str
    answers: dict[str, Any]


class DecisionGuidance(BaseModel):
    user_prompt: str


DecisionFunction = Callable[[dict[str, Any]], dict[str, Any]]


@dataclass(frozen=True)
class DecisionProblem:
    name: str
    function: DecisionFunction = field(repr=False)
    documentation: str


class JsonAgentTask(BaseModel):
    """
    One unified task type for:
    - meta orchestrator,
    - orchestrator,
    - question agents,
    - auditor.
    """

    task_id: str

    kind: Literal[
        "meta_orchestrator",
        "orchestrator",
        "calibrator",
        "question",
        "auditor",
    ]

    system_prompt: str
    instructions: str

    input_payload: dict[str, Any] = Field(default_factory=dict)
    output_schema: dict[str, Any]

    model_profile: Literal["standard", "smart"] = "standard"

    target_entity_type: str | None = None
    target_question_id: str | None = None

    @model_validator(mode="after")
    def validate_question_target(self) -> "JsonAgentTask":
        if self.kind == "question":
            if not self.target_entity_type:
                raise ValueError(
                    "Question tasks must provide target_entity_type."
                )

            if not self.target_question_id:
                raise ValueError(
                    "Question tasks must provide target_question_id."
                )

        return self


class GeneratedAggregation(BaseModel):
    code: str
    rationale: str = ""


class OrchestrationPlan(BaseModel):
    question_tasks: list[JsonAgentTask]
    aggregation: GeneratedAggregation
    assumptions: list[str] = Field(default_factory=list)



class QuestionAgentPlan(BaseModel):
    """
    First orchestration stage.

    Contains only the question-agent task formats: prompts, JSON schemas,
    and target survey questions. It does not contain aggregation code.
    """

    question_tasks: list[JsonAgentTask]
    assumptions: list[str] = Field(default_factory=list)
    representation_summary: str = ""


class AggregationCodePlan(BaseModel):
    """
    Second orchestration stage.

    Contains only generated aggregation code. The code receives outputs whose
    structure is defined by a previously validated QuestionAgentPlan.
    """

    code: str
    rationale: str = ""

class AgentOutput(BaseModel):
    # Unique logical output ID. When one question-agent call processes a
    # batch of respondents, the pipeline derives one ID per respondent from
    # the shared batch task ID.
    task_id: str

    # Stable ID from the QuestionAgentPlan.
    #
    # Unlike task_id, this does not include the strategy ID, revision round,
    # survey ID, respondent ID, or question ID.
    source_task_id: str

    entity_id: str
    entity_type: str
    question_id: str

    output: Any

    raw_attempts: list[str]
    llm_metadata: list[dict[str, Any]]


class CommunicationStyleProfile(BaseModel):
    """Compact, content-free baseline for one respondent's writing style."""

    entity_id: str
    entity_type: str

    verbosity: Literal["low", "medium", "high", "unknown"]
    directness: Literal["low", "medium", "high", "unknown"]
    emphasis: Literal["low", "medium", "high", "unknown"]
    hedging: Literal["low", "medium", "high", "unknown"]
    confidence: Literal["low", "medium", "high"]

    style_summary: str = Field(max_length=240)


class ToneCalibrationResult(BaseModel):
    profiles: list[CommunicationStyleProfile]


class WeightGenerationIdea(BaseModel):
    """
    A high-level strategy produced by the meta orchestrator.

    This is not executable code. It is guidance for an individual
    downstream orchestrator.
    """

    id: str
    title: str

    instructions_for_orchestrator: str
    scoring_rationale: str

    risks_to_check: list[str] = Field(default_factory=list)


class MetaOrchestrationPlan(BaseModel):
    """
    Ideas are ordered from most preferred to least preferred.
    """

    ideas: list[WeightGenerationIdea]

    @model_validator(mode="after")
    def validate_unique_idea_ids(self) -> "MetaOrchestrationPlan":
        idea_ids = [idea.id for idea in self.ideas]

        if not idea_ids:
            raise ValueError(
                "The meta orchestrator must generate at least one idea."
            )

        if len(set(idea_ids)) != len(idea_ids):
            raise ValueError(
                "Meta-orchestration idea IDs must be unique."
            )

        return self


class AuditIssue(BaseModel):
    severity: Literal["critical", "major", "minor"]
    description: str
    evidence: str


class AuditResult(BaseModel):
    """
    If approved=False, feedback_to_orchestrator is sent into the next
    orchestration round for that strategy.
    """

    approved: bool
    summary: str

    issues: list[AuditIssue] = Field(default_factory=list)

    feedback_to_orchestrator: str = ""

    @model_validator(mode="after")
    def validate_rejection_has_feedback(self) -> "AuditResult":
        if not self.approved:
            if not self.issues:
                raise ValueError(
                    "A rejected audit must contain at least one issue."
                )

            if not self.feedback_to_orchestrator.strip():
                raise ValueError(
                    "A rejected audit must provide feedback_to_orchestrator."
                )

        return self
