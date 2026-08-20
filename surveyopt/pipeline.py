from __future__ import annotations

import json
import re
import traceback
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from surveyopt.aggregation import execute_generated_aggregation
from surveyopt.audit import make_auditor_task
from surveyopt.calibration import (
    make_tone_calibration_task,
    profile_map,
    validate_tone_calibration_result,
)
from surveyopt.json_tasks import JsonTaskError, JsonTaskRunner
from surveyopt.meta_orchestration import make_meta_orchestrator_task
from surveyopt.models import (
    AggregationCodePlan,
    AgentOutput,
    AuditResult,
    CommunicationStyleProfile,
    DecisionGuidance,
    DecisionProblem,
    JsonAgentTask,
    MetaOrchestrationPlan,
    QuestionAgentPlan,
    SurveyDefinition,
    SurveyResponse,
    ToneCalibrationResult,
    WeightGenerationIdea,
)

from surveyopt.orchestration import (
    TONE_CALIBRATION_RULES,
    make_aggregation_code_task,
    make_question_format_task,
    validate_aggregation_code_plan,
    validate_question_agent_plan,
)

@dataclass(frozen=True)
class PipelineConfig:
    artifact_root: Path = Path("runs")

    response_sample_size: int = 10
    agent_workers: int = 8

    # If True, the meta-orchestrator proposes several independent
    # weight-generation strategies.
    #
    # If False, skip the meta-orchestrator and run one ordinary orchestrator
    # directly from the survey, response sample, decision documentation,
    # and user guidance.
    use_meta_orchestrator: bool = True

    # Used only when use_meta_orchestrator=True.
    meta_idea_count: int = 3

    # Initial orchestration plus possible auditor-driven revisions.
    max_revision_rounds: int = 10

    auditor_mode: Literal[
        "lenient",
        "balanced",
        "strict",
    ] = "lenient"


@dataclass
class AuditRoundResult:
    round_index: int

    question_agent_plan: QuestionAgentPlan | None = None
    aggregation_code_plan: AggregationCodePlan | None = None

    agent_outputs: list[AgentOutput] = field(default_factory=list)

    optimization_input: dict[str, Any] | None = None
    decision: dict[str, Any] | None = None

    audit: AuditResult | None = None
    execution_error: str | None = None


@dataclass
class CandidateRunResult:
    """
    One complete meta-orchestrator strategy branch.

    A result is returned by DecisionPipeline.run() only when:
    - status == "approved"
    - decision is not None
    """

    run_id: str
    run_directory: Path
    candidate_directory: Path

    strategy: WeightGenerationIdea
    status: str
    rounds: list[AuditRoundResult]

    decision: dict[str, Any] | None = None




class DecisionPipeline:
    def __init__(
        self,
        *,
        task_runner: JsonTaskRunner,
        config: PipelineConfig = PipelineConfig(),
    ) -> None:
        self.task_runner = task_runner
        self.config = config

    def run(
        self,
        *,
        surveys: list[SurveyDefinition],
        responses: list[SurveyResponse],
        decision_problem: DecisionProblem,
        guidance: DecisionGuidance,
    ) -> list[CandidateRunResult]:
        self._validate_inputs(surveys, responses)
        self._validate_config()

        run_id = self._new_run_id()
        run_directory = Path(self.config.artifact_root) / run_id
        run_directory.mkdir(parents=True, exist_ok=False)

        try:
            self._write_json(
                run_directory / "inputs.json",
                {
                    "surveys": [
                        survey.model_dump(mode="json")
                        for survey in surveys
                    ],
                    "responses": [
                        response.model_dump(mode="json")
                        for response in responses
                    ],
                    "guidance": guidance.model_dump(mode="json"),
                    "decision_problem": {
                        "name": decision_problem.name,
                        "documentation": decision_problem.documentation,
                    },
                    "pipeline_config": {
                        "response_sample_size": (
                            self.config.response_sample_size
                        ),
                        "agent_workers": self.config.agent_workers,
                        "meta_idea_count": self.config.meta_idea_count,
                        "max_revision_rounds": (
                            self.config.max_revision_rounds
                        ),
                        "use_meta_orchestrator": self.config.use_meta_orchestrator,
                    },
                },
            )

            response_sample = responses[
                : self.config.response_sample_size
            ]

            tone_profiles = self._build_tone_profiles(
                run_directory=run_directory,
                surveys=surveys,
                responses=responses,
            )

            strategies = self._get_weight_generation_strategies(
                run_directory=run_directory,
                surveys=surveys,
                response_sample=response_sample,
                decision_problem=decision_problem,
                guidance=guidance,
            )

            candidates: list[CandidateRunResult] = []

            for strategy_index, strategy in enumerate(
                strategies,
                start=1,
            ):
                candidate_directory = (
                    run_directory
                    / "candidates"
                    / (
                        f"{strategy_index:02d}_"
                        f"{self._safe_filename(strategy.id)}"
                    )
                )

                candidate = self._run_candidate(
                    run_id=run_id,
                    run_directory=run_directory,
                    candidate_directory=candidate_directory,
                    strategy=strategy,
                    surveys=surveys,
                    responses=responses,
                    response_sample=response_sample,
                    decision_problem=decision_problem,
                    guidance=guidance,
                    tone_profiles=tone_profiles,
                )

                candidates.append(candidate)


            successful_results = [
                candidate
                for candidate in candidates
                if candidate.status == "approved"
                and candidate.decision is not None
            ]

            self._write_json(
                run_directory / "run_summary.json",
                {
                    "successful_result_count": len(successful_results),
                    "successful_strategy_ids": [
                        candidate.strategy.id
                        for candidate in successful_results
                    ],
                    "candidates": [
                        {
                            "strategy": candidate.strategy.model_dump(mode="json"),
                            "status": candidate.status,
                            "round_count": len(candidate.rounds),
                            "decision": candidate.decision,
                            "candidate_directory": str(
                                candidate.candidate_directory
                            ),
                        }
                        for candidate in candidates
                    ],
                },
            )

            self._write_json(
                run_directory / "successful_results.json",
                {
                    "results": [
                        {
                            "strategy": candidate.strategy.model_dump(mode="json"),
                            "decision": candidate.decision,
                            "candidate_directory": str(
                                candidate.candidate_directory
                            ),
                            "final_audit": (
                                candidate.rounds[-1].audit.model_dump(mode="json")
                                if candidate.rounds
                                and candidate.rounds[-1].audit is not None
                                else None
                            ),
                        }
                        for candidate in successful_results
                    ]
                },
            )

            return successful_results

        except Exception as exc:
            self._write_json(
                run_directory / "error.json",
                self._failure_payload(exc),
            )
            raise

    def _build_tone_profiles(
        self,
        *,
        run_directory: Path,
        surveys: list[SurveyDefinition],
        responses: list[SurveyResponse],
    ) -> dict[tuple[str, str], CommunicationStyleProfile]:
        """Create one reusable communication-style baseline per respondent."""

        survey_by_id = {
            survey.id: survey
            for survey in surveys
        }
        respondents_by_entity: dict[tuple[str, str], dict[str, Any]] = {}

        for response in responses:
            entity_key = (
                response.entity_type,
                response.entity_id,
            )
            respondent = respondents_by_entity.setdefault(
                entity_key,
                {
                    "entity": {
                        "id": response.entity_id,
                        "type": response.entity_type,
                    },
                    "answers": [],
                },
            )
            survey = survey_by_id[response.survey_id]

            for question in survey.questions:
                if question.id not in response.answers:
                    continue

                respondent["answers"].append(
                    {
                        "survey": {
                            "id": survey.id,
                            "respondent_type": survey.respondent_type,
                        },
                        "question": question.model_dump(mode="json"),
                        "answer": response.answers[question.id],
                    }
                )

        calibration_respondents = [
            respondent
            for respondent in respondents_by_entity.values()
            if respondent["answers"]
        ]

        if not calibration_respondents:
            self._write_json(
                run_directory / "tone_profiles.json",
                {
                    "profiles": [],
                    "raw_attempts": [],
                    "llm_metadata": [],
                },
            )
            return {}

        expected_entities = {
            (
                respondent["entity"]["type"],
                respondent["entity"]["id"],
            )
            for respondent in calibration_respondents
        }
        task = make_tone_calibration_task(
            respondents=calibration_respondents,
        )
        task_result = self.task_runner.run(
            task,
            response_model=ToneCalibrationResult,
            result_validator=lambda result: validate_tone_calibration_result(
                result,
                expected_entities,
            ),
        )
        calibration_result: ToneCalibrationResult = task_result.value

        self._write_json(
            run_directory / "tone_profiles.json",
            {
                "profiles": [
                    profile.model_dump(mode="json")
                    for profile in calibration_result.profiles
                ],
                "raw_attempts": task_result.raw_attempts,
                "llm_metadata": task_result.metadata,
            },
        )

        return profile_map(calibration_result)

    def _get_weight_generation_strategies(
        self,
        *,
        run_directory: Path,
        surveys: list[SurveyDefinition],
        response_sample: list[SurveyResponse],
        decision_problem: DecisionProblem,
        guidance: DecisionGuidance,
    ) -> list[WeightGenerationIdea]:
        """
        Return the strategies that will be passed to ordinary orchestrators.

        When use_meta_orchestrator=False, no meta-orchestrator LLM call occurs.
        Instead, one deterministic direct-orchestration strategy is used.
        """

        if not self.config.use_meta_orchestrator:
            direct_strategy = WeightGenerationIdea(
                id="direct_orchestration",
                title="Direct orchestration",
                instructions_for_orchestrator=(
                    "Independently design an appropriate procedure for converting "
                    "survey responses into the numerical optimization inputs "
                    "required by the documented decision function. Use the "
                    "decision-maker's prompt, surveys, and response sample "
                    "directly. Choose useful intermediate JSON representations "
                    "for question agents and implement the resulting scoring "
                    "logic in generated aggregation code."
                ),
                scoring_rationale=(
                    "No separate meta-orchestration strategy is imposed. "
                    "The orchestrator should derive a reasonable scoring "
                    "procedure directly from the supplied problem context."
                ),
                risks_to_check=[
                    "Do not infer unsupported preferences or attributes.",
                    "Respect explicit exclusions and dealbreakers.",
                    "Ensure generated aggregation code returns the exact input "
                    "format documented for the deterministic decision function.",
                ],
            )

            self._write_json(
                run_directory / "direct_orchestration_strategy.json",
                {
                    "meta_orchestrator_used": False,
                    "strategy": direct_strategy.model_dump(mode="json"),
                },
            )

            return [direct_strategy]

        meta_task = make_meta_orchestrator_task(
            surveys=surveys,
            response_sample=response_sample,
            decision_problem=decision_problem,
            guidance=guidance,
            idea_count=self.config.meta_idea_count,
        )

        meta_result = self.task_runner.run(
            meta_task,
            response_model=MetaOrchestrationPlan,
        )

        meta_plan: MetaOrchestrationPlan = meta_result.value

        self._write_json(
            run_directory / "meta_orchestrator_output.json",
            {
                "meta_orchestrator_used": True,
                "meta_plan": meta_plan.model_dump(mode="json"),
                "raw_attempts": meta_result.raw_attempts,
                "llm_metadata": meta_result.metadata,
            },
        )

        return meta_plan.ideas



    def _run_candidate(
        self,
        *,
        run_id: str,
        run_directory: Path,
        candidate_directory: Path,
        strategy: WeightGenerationIdea,
        surveys: list[SurveyDefinition],
        responses: list[SurveyResponse],
        response_sample: list[SurveyResponse],
        decision_problem: DecisionProblem,
        guidance: DecisionGuidance,
        tone_profiles: dict[
            tuple[str, str],
            CommunicationStyleProfile,
        ],
    ) -> CandidateRunResult:
        candidate_directory.mkdir(parents=True, exist_ok=True)

        candidate = CandidateRunResult(
            run_id=run_id,
            run_directory=run_directory,
            candidate_directory=candidate_directory,
            strategy=strategy,
            status="exhausted",
            rounds=[],
        )

        prior_question_agent_plan: QuestionAgentPlan | None = None
        prior_aggregation_code_plan: AggregationCodePlan | None = None
        revision_feedback: str | None = None

        for round_index in range(
            1,
            self.config.max_revision_rounds + 1,
        ):
            round_directory = (
                candidate_directory / f"round_{round_index:02d}"
            )
            round_directory.mkdir(parents=True, exist_ok=True)

            question_agent_plan: QuestionAgentPlan | None = None
            aggregation_code_plan: AggregationCodePlan | None = None
            agent_outputs: list[AgentOutput] = []
            optimization_input: dict[str, Any] | None = None
            decision: dict[str, Any] | None = None

            try:
                # ---------------------------------------------------------------
                # Stage 1: Question-agent formats, prompts, and output schemas.
                # ---------------------------------------------------------------

                question_format_task = make_question_format_task(
                    surveys=surveys,
                    response_sample=response_sample,
                    decision_problem=decision_problem,
                    guidance=guidance,
                    weight_generation_idea=strategy,
                    task_id=(
                        f"question_format_orchestrator__{strategy.id}"
                        f"__round_{round_index}"
                    ),
                    revision_feedback=revision_feedback,
                    previous_question_plan=prior_question_agent_plan,
                )

                question_format_result = self.task_runner.run(
                    question_format_task,
                    response_model=QuestionAgentPlan,
                    result_validator=lambda plan: validate_question_agent_plan(
                        plan,
                        surveys,
                    ),
                )

                question_agent_plan = question_format_result.value

                self._write_json(
                    round_directory / "question_agent_plan_output.json",
                    {
                        "question_agent_plan": question_agent_plan.model_dump(
                            mode="json"
                        ),
                        "raw_attempts": question_format_result.raw_attempts,
                        "llm_metadata": question_format_result.metadata,
                    },
                )

                # ---------------------------------------------------------------
                # Stage 2: Aggregation code. It receives the validated output
                # contract from Stage 1.
                # ---------------------------------------------------------------

                aggregation_code_task = make_aggregation_code_task(
                    surveys=surveys,
                    response_sample=response_sample,
                    decision_problem=decision_problem,
                    guidance=guidance,
                    weight_generation_idea=strategy,
                    question_agent_plan=question_agent_plan,
                    task_id=(
                        f"aggregation_code_orchestrator__{strategy.id}"
                        f"__round_{round_index}"
                    ),
                    revision_feedback=revision_feedback,
                    previous_aggregation_plan=prior_aggregation_code_plan,
                )

                aggregation_code_result = self.task_runner.run(
                    aggregation_code_task,
                    response_model=AggregationCodePlan,
                    result_validator=validate_aggregation_code_plan,
                )

                aggregation_code_plan = aggregation_code_result.value

                self._write_json(
                    round_directory / "aggregation_code_output.json",
                    {
                        "aggregation_code_plan": aggregation_code_plan.model_dump(
                            mode="json"
                        ),
                        "raw_attempts": aggregation_code_result.raw_attempts,
                        "llm_metadata": aggregation_code_result.metadata,
                    },
                )

                (round_directory / "aggregation_code.py").write_text(
                    aggregation_code_plan.code,
                    encoding="utf-8",
                )

                runtime_tasks = self._expand_question_tasks(
                    question_agent_plan=question_agent_plan,
                    surveys=surveys,
                    responses=responses,
                    task_namespace=(
                        f"{strategy.id}__round_{round_index}"
                    ),
                    tone_profiles=tone_profiles,
                )

                agent_outputs = self._run_question_agents(
                    runtime_tasks=runtime_tasks,
                    output_directory=round_directory / "agent_outputs",
                )

                aggregation_inputs = [
                {
                    # Unique per-entity output ID. Several outputs may come
                    # from one batched question-agent invocation.
                    "task_id": output.task_id,

                    # Stable task ID from the QuestionAgentPlan.
                    "source_task_id": output.source_task_id,

                    "entity_id": output.entity_id,
                    "entity_type": output.entity_type,
                    "question_id": output.question_id,
                    "output": output.output,
                }
                for output in agent_outputs
            ]


                optimization_input = execute_generated_aggregation(
                    source=aggregation_code_plan.code,
                    question_outputs=aggregation_inputs,
                    survey=[
                        survey.model_dump(mode="json")
                        for survey in surveys
                    ],
                    responses=[
                        response.model_dump(mode="json")
                        for response in responses
                    ],
                )

                self._write_json(
                    round_directory / "optimization_input.json",
                    optimization_input,
                )

                decision = decision_problem.function(
                    optimization_input
                )

                # Verify it can be persisted before auditing it.
                json.dumps(
                    decision,
                    ensure_ascii=False,
                    allow_nan=False,
                )

                self._write_json(
                    round_directory / "decision.json",
                    decision,
                )

                auditor_task = make_auditor_task(
                    task_id=(
                        f"auditor__{strategy.id}"
                        f"__round_{round_index}"
                    ),
                    surveys=surveys,
                    responses=responses,
                    decision_problem=decision_problem,
                    guidance=guidance,
                    strategy=strategy,
                    question_agent_plan=question_agent_plan,
                    aggregation_code_plan=aggregation_code_plan,
                    agent_outputs=agent_outputs,
                    optimization_input=optimization_input,
                    decision=decision,
                    audit_mode=self.config.auditor_mode,
                )

                audit_task_result = self.task_runner.run(
                    auditor_task,
                    response_model=AuditResult,
                )

                audit: AuditResult = audit_task_result.value

                self._write_json(
                    round_directory / "auditor_output.json",
                    {
                        "audit": audit.model_dump(mode="json"),
                        "raw_attempts": audit_task_result.raw_attempts,
                        "llm_metadata": audit_task_result.metadata,
                    },
                )

                round_result = AuditRoundResult(
                    round_index=round_index,
                    question_agent_plan=question_agent_plan,
                    aggregation_code_plan=aggregation_code_plan,
                    agent_outputs=agent_outputs,
                    optimization_input=optimization_input,
                    decision=decision,
                    audit=audit,
                )

                candidate.rounds.append(round_result)

                if audit.approved:
                    candidate.status = "approved"
                    candidate.decision = decision

                    self._write_json(
                        candidate_directory / "approved_decision.json",
                        {
                            "strategy": strategy.model_dump(mode="json"),
                            "decision": decision,
                            "audit": audit.model_dump(mode="json"),
                        },
                    )

                    break

                # This feedback is fed into the next orchestration call.
                revision_feedback = audit.feedback_to_orchestrator
                prior_question_agent_plan = question_agent_plan
                prior_aggregation_code_plan = aggregation_code_plan

            except Exception as exc:
                self._write_json(
                    round_directory / "execution_error.json",
                    self._failure_payload(exc),
                )

                candidate.rounds.append(
                    AuditRoundResult(
                        round_index=round_index,
                        question_agent_plan=question_agent_plan,
                        aggregation_code_plan=aggregation_code_plan,
                        agent_outputs=agent_outputs,
                        optimization_input=optimization_input,
                        decision=decision,
                        execution_error=str(exc),
                    )
                )

                # Technical errors are also useful feedback for the next
                # orchestration attempt. For example, generated code may
                # have failed AST validation or produced an invalid solver
                # input.
                revision_feedback = (
                    "The prior strategy could not be executed successfully. "
                    "Revise the plan so it can be executed by the pipeline. "
                    f"Technical error: {type(exc).__name__}: {exc}"
                )

                prior_question_agent_plan = question_agent_plan
                prior_aggregation_code_plan = aggregation_code_plan

        self._write_json(
            candidate_directory / "candidate_summary.json",
            {
                "strategy": strategy.model_dump(mode="json"),
                "status": candidate.status,
                "round_count": len(candidate.rounds),
                "approved_decision": candidate.decision,
            },
        )

        return candidate

    def _run_question_agents(
        self,
        *,
        runtime_tasks: list[JsonAgentTask],
        output_directory: Path,
    ) -> list[AgentOutput]:
        if not runtime_tasks:
            raise ValueError(
                "The orchestration plan produced no applicable question tasks."
            )

        output_directory.mkdir(parents=True, exist_ok=True)

        def execute_task(task: JsonAgentTask) -> list[AgentOutput]:
            try:
                result = self.task_runner.run(task)

                payload = task.input_payload
                batch_values = result.value["outputs"]
                batch_outputs: list[AgentOutput] = []

                for respondent in payload["respondents"]:
                    entity = respondent["entity"]
                    entity_id = entity["id"]

                    batch_outputs.append(
                        AgentOutput(
                            task_id=(
                                f"{task.task_id}"
                                f"__{entity_id}"
                            ),
                            source_task_id=payload["source_task_id"],
                            entity_id=entity_id,
                            entity_type=entity["type"],
                            question_id=payload["question"]["id"],
                            output=batch_values[entity_id],
                            raw_attempts=result.raw_attempts,
                            llm_metadata=result.metadata,
                        )
                    )

                self._write_json(
                    output_directory
                    / f"{self._safe_filename(task.task_id)}.json",
                    {
                        "batch_task_id": task.task_id,
                        "source_task_id": payload["source_task_id"],
                        "survey": payload["survey"],
                        "question": payload["question"],
                        "respondent_count": len(payload["respondents"]),
                        "outputs": [
                            output.model_dump(mode="json")
                            for output in batch_outputs
                        ],
                        "raw_attempts": result.raw_attempts,
                        "llm_metadata": result.metadata,
                    },
                )

                return batch_outputs

            except Exception as exc:
                self._write_json(
                    output_directory
                    / (
                        f"{self._safe_filename(task.task_id)}"
                        "__failed.json"
                    ),
                    self._failure_payload(exc),
                )
                raise

        outputs: list[AgentOutput] = []

        with ThreadPoolExecutor(
            max_workers=self.config.agent_workers
        ) as executor:
            future_to_task = {
                executor.submit(execute_task, task): task
                for task in runtime_tasks
            }

            for future in as_completed(future_to_task):
                outputs.extend(future.result())

        outputs.sort(key=lambda output: output.task_id)

        return outputs

    def _expand_question_tasks(
        self,
        *,
        question_agent_plan: QuestionAgentPlan,
        surveys: list[SurveyDefinition],
        responses: list[SurveyResponse],
        task_namespace: str,
        tone_profiles: dict[
            tuple[str, str],
            CommunicationStyleProfile,
        ],
    ) -> list[JsonAgentTask]:
        runtime_tasks: list[JsonAgentTask] = []

        for plan_task in question_agent_plan.question_tasks:
            for survey in surveys:
                if survey.respondent_type != plan_task.target_entity_type:
                    continue

                question = next(
                    (
                        candidate
                        for candidate in survey.questions
                        if candidate.id == plan_task.target_question_id
                    ),
                    None,
                )

                if question is None:
                    continue

                matching_responses = [
                    response
                    for response in responses
                    if response.survey_id == survey.id
                    and response.entity_type == plan_task.target_entity_type
                    and question.id in response.answers
                ]

                if not matching_responses:
                    continue

                entity_ids = [
                    response.entity_id
                    for response in matching_responses
                ]

                if len(set(entity_ids)) != len(entity_ids):
                    raise ValueError(
                        "Question-agent batches require unique entity IDs. "
                        f"Duplicate ID found for survey {survey.id!r}, "
                        f"question {question.id!r}."
                    )

                task_id = (
                    f"{task_namespace}"
                    f"__{plan_task.task_id}"
                    f"__{survey.id}"
                    f"__{question.id}"
                )

                input_payload = {
                    "source_task_id": plan_task.task_id,
                    "survey": {
                        "id": survey.id,
                        "respondent_type": survey.respondent_type,
                    },
                    "question": question.model_dump(mode="json"),
                    "respondents": [
                        {
                            "entity": {
                                "id": response.entity_id,
                                "type": response.entity_type,
                            },
                            "answer": response.answers[question.id],
                            "tone_profile": tone_profiles[
                                (
                                    response.entity_type,
                                    response.entity_id,
                                )
                            ].model_dump(
                                mode="json",
                                exclude={"entity_id", "entity_type"},
                            ),
                        }
                        for response in matching_responses
                    ],
                }

                batch_output_schema = {
                    "$defs": {
                        "per_respondent_output": plan_task.output_schema,
                    },
                    "type": "object",
                    "required": ["outputs"],
                    "properties": {
                        "outputs": {
                            "type": "object",
                            "required": entity_ids,
                            "propertyNames": {
                                "enum": entity_ids,
                            },
                            "additionalProperties": {
                                "$ref": "#/$defs/per_respondent_output",
                            },
                        }
                    },
                    "additionalProperties": False,
                }

                runtime_tasks.append(
                    plan_task.model_copy(
                        update={
                            "task_id": task_id,
                            "input_payload": input_payload,
                            "output_schema": batch_output_schema,
                            "system_prompt": (
                                f"{plan_task.system_prompt}\n\n"
                                f"{TONE_CALIBRATION_RULES}"
                            ),
                            "instructions": (
                                f"{plan_task.instructions}\n\n"
                                "Process every respondent in the supplied "
                                "batch in this single call. Use the shared "
                                "question context to interpret answers "
                                "consistently, and use each respondent's "
                                "tone_profile only for within-person tone "
                                "calibration. "
                                "Return an `outputs` object containing exactly "
                                "one entry for every supplied entity ID. Each "
                                "entry must independently match the original "
                                "per-respondent output schema."
                            ),
                        }
                    )
                )

        return runtime_tasks

    def _validate_config(self) -> None:
        if (
            self.config.use_meta_orchestrator
            and self.config.meta_idea_count < 1
        ):
            raise ValueError(
                "meta_idea_count must be at least 1 when "
                "use_meta_orchestrator=True."
            )

        if self.config.max_revision_rounds < 1:
            raise ValueError(
                "max_revision_rounds must be at least 1."
            )

        if self.config.agent_workers < 1:
            raise ValueError("agent_workers must be at least 1.")

    @staticmethod
    def _validate_inputs(
        surveys: list[SurveyDefinition],
        responses: list[SurveyResponse],
    ) -> None:
        survey_by_id = {
            survey.id: survey
            for survey in surveys
        }

        if len(survey_by_id) != len(surveys):
            raise ValueError("Survey IDs must be unique.")

        for response in responses:
            if response.survey_id not in survey_by_id:
                raise ValueError(
                    f"Response {response.entity_id!r} references unknown "
                    f"survey {response.survey_id!r}."
                )

            survey = survey_by_id[response.survey_id]

            if response.entity_type != survey.respondent_type:
                raise ValueError(
                    f"Response entity type {response.entity_type!r} does not "
                    f"match survey respondent type "
                    f"{survey.respondent_type!r}."
                )

    @staticmethod
    def _failure_payload(exc: Exception) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "error_type": type(exc).__name__,
            "error": str(exc),
            "traceback": traceback.format_exc(),
        }

        if isinstance(exc, JsonTaskError):
            payload["task_id"] = exc.task_id
            payload["raw_attempts"] = exc.raw_attempts
            payload["llm_metadata"] = exc.metadata

        return payload

    @staticmethod
    def _write_json(
        path: Path,
        value: Any,
    ) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)

        path.write_text(
            json.dumps(
                value,
                indent=2,
                ensure_ascii=False,
                allow_nan=False,
            ),
            encoding="utf-8",
        )

    @staticmethod
    def _safe_filename(value: str) -> str:
        return re.sub(
            r"[^A-Za-z0-9_.-]",
            "_",
            value,
        )

    @staticmethod
    def _new_run_id() -> str:
        timestamp = datetime.now(UTC).strftime(
            "%Y%m%dT%H%M%SZ"
        )

        return f"{timestamp}_{uuid.uuid4().hex[:10]}"
