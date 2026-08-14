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
from surveyopt.json_tasks import JsonTaskError, JsonTaskRunner
from surveyopt.meta_orchestration import make_meta_orchestrator_task
from surveyopt.models import (
    AgentOutput,
    AuditResult,
    DecisionGuidance,
    DecisionProblem,
    JsonAgentTask,
    MetaOrchestrationPlan,
    OrchestrationPlan,
    SurveyDefinition,
    SurveyResponse,
    WeightGenerationIdea,
)
from surveyopt.orchestration import (
    make_orchestrator_task,
    validate_plan,
)

@dataclass(frozen=True)
class PipelineConfig:
    artifact_root: Path = Path("runs")

    response_sample_size: int = 10
    agent_workers: int = 8

    # Number of independent scoring strategies the meta orchestrator proposes.
    meta_idea_count: int = 3

    # Initial orchestration plus possible auditor-driven revisions.
    max_revision_rounds: int = 3


@dataclass
class AuditRoundResult:
    round_index: int

    plan: OrchestrationPlan | None = None
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
                    },
                },
            )

            response_sample = responses[
                : self.config.response_sample_size
            ]

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
                    "meta_plan": meta_plan.model_dump(mode="json"),
                    "raw_attempts": meta_result.raw_attempts,
                    "llm_metadata": meta_result.metadata,
                },
            )

            candidates: list[CandidateRunResult] = []

            for strategy_index, strategy in enumerate(
                meta_plan.ideas,
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

        prior_plan: OrchestrationPlan | None = None
        revision_feedback: str | None = None

        for round_index in range(
            1,
            self.config.max_revision_rounds + 1,
        ):
            round_directory = (
                candidate_directory / f"round_{round_index:02d}"
            )
            round_directory.mkdir(parents=True, exist_ok=True)

            plan: OrchestrationPlan | None = None
            agent_outputs: list[AgentOutput] = []
            optimization_input: dict[str, Any] | None = None
            decision: dict[str, Any] | None = None

            try:
                orchestrator_task = make_orchestrator_task(
                    surveys=surveys,
                    response_sample=response_sample,
                    decision_problem=decision_problem,
                    guidance=guidance,
                    weight_generation_idea=strategy,
                    task_id=(
                        f"orchestrator__{strategy.id}"
                        f"__round_{round_index}"
                    ),
                    revision_feedback=revision_feedback,
                    previous_plan=prior_plan,
                )

                orchestration_result = self.task_runner.run(
                    orchestrator_task,
                    response_model=OrchestrationPlan,
                    result_validator=validate_plan,
                )

                plan = orchestration_result.value


                self._write_json(
                    round_directory / "orchestrator_output.json",
                    {
                        "plan": plan.model_dump(mode="json"),
                        "raw_attempts": orchestration_result.raw_attempts,
                        "llm_metadata": orchestration_result.metadata,
                    },
                )

                (
                    round_directory / "aggregation_code.py"
                ).write_text(
                    plan.aggregation.code,
                    encoding="utf-8",
                )

                runtime_tasks = self._expand_question_tasks(
                    plan=plan,
                    surveys=surveys,
                    responses=responses,
                    task_namespace=(
                        f"{strategy.id}__round_{round_index}"
                    ),
                )

                agent_outputs = self._run_question_agents(
                    runtime_tasks=runtime_tasks,
                    output_directory=round_directory / "agent_outputs",
                )

                aggregation_inputs = [
                    {
                        "task_id": output.task_id,
                        "entity_id": output.entity_id,
                        "entity_type": output.entity_type,
                        "question_id": output.question_id,
                        "output": output.output,
                    }
                    for output in agent_outputs
                ]

                optimization_input = execute_generated_aggregation(
                    source=plan.aggregation.code,
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
                    plan=plan,
                    agent_outputs=agent_outputs,
                    optimization_input=optimization_input,
                    decision=decision,
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
                    plan=plan,
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
                prior_plan = plan

            except Exception as exc:
                self._write_json(
                    round_directory / "execution_error.json",
                    self._failure_payload(exc),
                )

                candidate.rounds.append(
                    AuditRoundResult(
                        round_index=round_index,
                        plan=plan,
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

                prior_plan = plan

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

        def execute_task(task: JsonAgentTask) -> AgentOutput:
            try:
                result = self.task_runner.run(task)

                payload = task.input_payload

                output = AgentOutput(
                    task_id=task.task_id,
                    entity_id=payload["entity"]["id"],
                    entity_type=payload["entity"]["type"],
                    question_id=payload["question"]["id"],
                    output=result.value,
                    raw_attempts=result.raw_attempts,
                    llm_metadata=result.metadata,
                )

                self._write_json(
                    output_directory
                    / f"{self._safe_filename(task.task_id)}.json",
                    output.model_dump(mode="json"),
                )

                return output

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
                outputs.append(future.result())

        outputs.sort(key=lambda output: output.task_id)

        return outputs

    def _expand_question_tasks(
        self,
        *,
        plan: OrchestrationPlan,
        surveys: list[SurveyDefinition],
        responses: list[SurveyResponse],
        task_namespace: str,
    ) -> list[JsonAgentTask]:
        survey_by_id = {
            survey.id: survey
            for survey in surveys
        }

        runtime_tasks: list[JsonAgentTask] = []

        for plan_task in plan.question_tasks:
            for response in responses:
                if response.entity_type != plan_task.target_entity_type:
                    continue

                survey = survey_by_id[response.survey_id]

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

                if question.id not in response.answers:
                    continue

                task_id = (
                    f"{task_namespace}"
                    f"__{plan_task.task_id}"
                    f"__{response.entity_id}"
                    f"__{question.id}"
                )

                input_payload = {
                    "entity": {
                        "id": response.entity_id,
                        "type": response.entity_type,
                    },
                    "survey": {
                        "id": survey.id,
                        "respondent_type": survey.respondent_type,
                    },
                    "question": question.model_dump(mode="json"),
                    "answer": response.answers[question.id],
                }

                runtime_tasks.append(
                    plan_task.model_copy(
                        update={
                            "task_id": task_id,
                            "input_payload": input_payload,
                        }
                    )
                )

        return runtime_tasks

    def _validate_config(self) -> None:
        if self.config.meta_idea_count < 1:
            raise ValueError("meta_idea_count must be at least 1.")

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