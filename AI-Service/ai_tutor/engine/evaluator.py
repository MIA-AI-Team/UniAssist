import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple, Union

from ai_tutor.metrics import metrics_collector
from ai_tutor.config import Config
from ai_tutor.engine.exceptions import (
    AnalyticsResponseError,
    ChatResponseError,
    GradingResponseError,
    RubricResponseError,
)
from ai_tutor.models import (
    AIMetadata,
    ChatMessage,
    CodeReviewFinding,
    CohortAnalyticsResponse,
    CohortCodeReviewSnapshot,
    CohortCriterionSnapshot,
    CohortGradeSnapshot,
    CommonIssue,
    CriterionEvaluation,
    Misconception,
    RubricCriteriaItem,
    RubricSuggestionResponse,
    SubmissionGradingResponse,
    StudentChatResponse,
    LabChatResponse,
)
from ai_tutor.prompts import (
    RUBRIC_SUGGESTION_SYSTEM_PROMPT,
    RUBRIC_SUGGESTION_USER_PROMPT,
    RUBRIC_REFINEMENT_SYSTEM_PROMPT,
    RUBRIC_REFINEMENT_USER_PROMPT,
    SUBMISSION_GRADING_SYSTEM_PROMPT,
    SUBMISSION_GRADING_USER_PROMPT,
    STUDENT_SOCRATIC_TUTOR_SYSTEM_PROMPT,
    STUDENT_SOCRATIC_TUTOR_USER_PROMPT,
    LAB_ASSISTANT_SYSTEM_PROMPT,
    LAB_ASSISTANT_USER_PROMPT,
    COHORT_ANALYTICS_SYSTEM_PROMPT,
    COHORT_ANALYTICS_USER_PROMPT,
    get_task_type_guidance,
)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AIEvaluationEngine")


class AIEvaluationEngine:
    """Core AI Evaluation Engine implementing Simple Context (prompt-stuffing) access."""

    def __init__(self, provider: Optional[str] = None):
        self.provider = (provider or Config.PRIMARY_PROVIDER).lower()
        self.mock_mode = Config.MOCK_MODE
        self._groq_client = None
        self._gemini_client = None
        self._last_llm_info: Dict[str, Optional[str]] = {"provider": None, "model": None}

        if not self.mock_mode:
            self._init_clients()

    def _init_clients(self):
        if Config.GROQ_API_KEY:
            try:
                from groq import Groq
                self._groq_client = Groq(api_key=Config.GROQ_API_KEY)
                logger.info("Groq client initialized successfully.")
            except Exception as e:
                logger.warning(f"Failed to initialize Groq client: {e}")

        if Config.GEMINI_API_KEY:
            try:
                from google import genai
                self._gemini_client = genai.Client(api_key=Config.GEMINI_API_KEY)
                logger.info("Google Gemini client initialized successfully.")
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini client: {e}")

        if not self._groq_client and not self._gemini_client:
            logger.info("No active API keys found. Running in MOCK_MODE.")
            self.mock_mode = True

    def _build_metadata(
        self,
        record,
        *,
        warnings: Optional[List[str]] = None,
    ) -> AIMetadata:
        meta = record.to_metadata(
            ai_engine_version=Config.AI_ENGINE_VERSION,
            prompt_version=Config.PROMPT_VERSION,
        )
        if warnings is not None:
            meta.warnings_count = len(warnings)
        return meta

    def suggest_rubric(
        self,
        task_title: str,
        task_type: str,
        task_description: str,
        reference_text: str,
    ) -> RubricSuggestionResponse:
        ref_content = reference_text or task_description or f"Detailed task specification for '{task_title}' ({task_type})."
        ref_for_prompt, _ = self._budget_text(ref_content, Config.MAX_REFERENCE_CHARS, "reference")

        user_prompt = RUBRIC_SUGGESTION_USER_PROMPT.format(
            task_title=task_title,
            task_type=task_type,
            task_description=task_description,
            reference_text=ref_for_prompt,
            task_type_guidance=get_task_type_guidance(task_type),
        )

        with metrics_collector.track("suggest_rubric") as record:
            if self.mock_mode:
                response = self._mock_suggest_rubric(task_title, task_type)
                response.ai_metadata = self._build_metadata(record)
                return response

            try:
                json_str = self._call_llm(
                    system_prompt=RUBRIC_SUGGESTION_SYSTEM_PROMPT,
                    user_prompt=user_prompt,
                )
                record.provider = self._last_llm_info.get("provider")
                record.model_used = self._last_llm_info.get("model")
                data = self._clean_and_parse_json(json_str)
                response = RubricSuggestionResponse(**data)
                response = self._normalize_rubric_response(response)
                response.ai_metadata = self._build_metadata(record, warnings=response.warnings)
                return response
            except RubricResponseError:
                record.parse_success = False
                raise
            except Exception as e:
                record.parse_success = False
                logger.error(f"Rubric suggestion failed: {e}")
                raise RubricResponseError(f"AI rubric response was invalid: {e}") from e

    def refine_rubric(
        self,
        task_title: str,
        task_type: str,
        task_description: str,
        reference_text: str,
        previous_criteria: List[Union[RubricCriteriaItem, dict]],
        staff_feedback: str,
    ) -> RubricSuggestionResponse:
        formatted_prev = []
        for idx, item in enumerate(previous_criteria, 1):
            if isinstance(item, RubricCriteriaItem):
                formatted_prev.append(f"{idx}. {item.name} ({item.max_points} pts): {item.description}")
            elif isinstance(item, dict):
                formatted_prev.append(f"{idx}. {item.get('name')} ({item.get('max_points')} pts): {item.get('description')}")
        prev_str = "\n".join(formatted_prev)
        ref_content = reference_text or task_description or f"Task specification for '{task_title}' ({task_type})."
        ref_for_prompt, _ = self._budget_text(ref_content, Config.MAX_REFERENCE_CHARS, "reference")

        user_prompt = RUBRIC_REFINEMENT_USER_PROMPT.format(
            task_title=task_title,
            task_type=task_type,
            task_description=task_description,
            reference_text=ref_for_prompt,
            previous_rubric_formatted=prev_str,
            staff_feedback=staff_feedback,
        )

        with metrics_collector.track("refine_rubric") as record:
            if self.mock_mode:
                response = self._mock_suggest_rubric(task_title, task_type)
                response.ai_metadata = self._build_metadata(record)
                return response

            try:
                json_str = self._call_llm(
                    system_prompt=RUBRIC_REFINEMENT_SYSTEM_PROMPT,
                    user_prompt=user_prompt,
                )
                record.provider = self._last_llm_info.get("provider")
                record.model_used = self._last_llm_info.get("model")
                data = self._clean_and_parse_json(json_str)
                response = RubricSuggestionResponse(**data)
                response = self._normalize_rubric_response(response)
                response.ai_metadata = self._build_metadata(record, warnings=response.warnings)
                return response
            except RubricResponseError:
                record.parse_success = False
                raise
            except Exception as e:
                record.parse_success = False
                logger.error(f"Rubric refinement failed: {e}")
                raise RubricResponseError(f"AI rubric refinement response was invalid: {e}") from e

    def grade_submission(
        self,
        task_title: str,
        task_type: str,
        reference_text: str,
        rubric_criteria: List[Union[RubricCriteriaItem, dict]],
        submission_text: str,
        code_files: Optional[Dict[str, str]] = None,
        grading_key: Optional[str] = None,
        prep_warnings: Optional[List[str]] = None,
    ) -> SubmissionGradingResponse:
        prep_warnings = list(prep_warnings or [])
        ref_text_clean = (reference_text or "").strip()
        if not ref_text_clean:
            raise ValueError("Task specification is required for grading. Provide a spec file or pasted spec text.")

        sub_text_clean = (submission_text or "").strip()
        code_files = code_files or {}
        has_code = bool(code_files and any(content.strip() for content in code_files.values()))
        if not sub_text_clean and not has_code:
            raise ValueError("Student submission is empty. Upload a file or paste submission content.")

        ref_for_prompt, sub_for_prompt, code_section, grading_key_section, budget_warnings, truncated = (
            self._allocate_grading_context(
                reference_text=ref_text_clean,
                submission_text=sub_text_clean,
                code_files=code_files,
                grading_key=(grading_key or "").strip(),
            )
        )
        prep_warnings.extend(budget_warnings)

        formatted_criteria = []
        for idx, item in enumerate(rubric_criteria, 1):
            if isinstance(item, RubricCriteriaItem):
                formatted_criteria.append(f"{idx}. {item.name} ({item.max_points} pts): {item.description}")
            elif isinstance(item, dict):
                formatted_criteria.append(f"{idx}. {item.get('name')} ({item.get('max_points')} pts): {item.get('description')}")
        rubric_str = "\n".join(formatted_criteria)

        user_prompt = SUBMISSION_GRADING_USER_PROMPT.format(
            task_title=task_title,
            task_type=task_type,
            task_type_guidance=get_task_type_guidance(task_type),
            reference_text=ref_for_prompt,
            rubric_criteria_formatted=rubric_str,
            grading_key_section=grading_key_section,
            submission_text=sub_for_prompt or "No additional submission text provided.",
            code_files_section=code_section,
        )

        with metrics_collector.track("grade_submission") as record:
            record.prompt_truncated = truncated

            if self.mock_mode:
                response = self._mock_grade_submission(rubric_criteria, code_files=code_files, warnings=prep_warnings)
                response.ai_metadata = self._build_metadata(record, warnings=response.warnings)
                return response

            try:
                json_str = self._call_llm(
                    system_prompt=SUBMISSION_GRADING_SYSTEM_PROMPT,
                    user_prompt=user_prompt,
                )
                record.provider = self._last_llm_info.get("provider")
                record.model_used = self._last_llm_info.get("model")
                data = self._clean_and_parse_json(json_str)
                response = SubmissionGradingResponse(**data)
                response = self._normalize_grading_response(response, rubric_criteria, prep_warnings)
                record.scores_adjusted = any("adjusted" in w.lower() for w in response.warnings)
                response.ai_metadata = self._build_metadata(record, warnings=response.warnings)
                return response
            except GradingResponseError:
                record.parse_success = False
                raise
            except Exception as e:
                record.parse_success = False
                logger.error(f"Grading failed: {e}")
                raise GradingResponseError(f"AI grading response was invalid: {e}") from e

    def analyze_cohort_patterns(
        self,
        task_title: str,
        task_type: str = "lab",
        task_description: str = "",
        rubric_criteria_names: Optional[List[str]] = None,
        grades: Optional[List[CohortGradeSnapshot]] = None,
        code_reviews: Optional[List[CohortCodeReviewSnapshot]] = None,
        criterion_stats: Optional[List[CohortCriterionSnapshot]] = None,
    ) -> CohortAnalyticsResponse:
        """
        Analyze anonymized cohort aggregates for shared errors/misconceptions.
        Backend owns auth and DB aggregation; this method only interprets prepared data.
        """
        grades = list(grades or [])
        code_reviews = list(code_reviews or [])
        criterion_stats = list(criterion_stats or [])
        rubric_criteria_names = list(rubric_criteria_names or [])

        if not grades and not code_reviews and not criterion_stats:
            raise ValueError(
                "Cohort analytics requires at least one of: grades, code_reviews, or criterion_stats."
            )

        student_count = len(grades)
        percentages = [
            (g.grade / g.max_grade) * 100.0 for g in grades if g.max_grade > 0
        ]
        average_percentage = round(sum(percentages) / len(percentages), 2) if percentages else 0.0
        fail_count = sum(1 for p in percentages if p < 50.0)

        warnings: List[str] = []
        if student_count < Config.MIN_COHORT_SIZE_FOR_PATTERNS:
            warnings.append(
                f"Cohort size ({student_count}) is below "
                f"{Config.MIN_COHORT_SIZE_FOR_PATTERNS}; patterns may be unreliable."
            )

        grades_for_prompt = grades[: Config.MAX_COHORT_FEEDBACK_SNIPPETS]
        reviews_for_prompt = code_reviews[: Config.MAX_COHORT_CODE_REVIEW_ROWS]
        if len(grades) > len(grades_for_prompt):
            warnings.append(
                f"Only the first {len(grades_for_prompt)} grade/feedback rows were sent to the model."
            )
        if len(code_reviews) > len(reviews_for_prompt):
            warnings.append(
                f"Only the first {len(reviews_for_prompt)} code-review rows were sent to the model."
            )

        grades_section = self._format_cohort_grades(grades_for_prompt) or "No grade rows provided."
        code_reviews_section = (
            self._format_cohort_code_reviews(reviews_for_prompt) or "No code-review rows provided."
        )
        criterion_stats_section = (
            self._format_cohort_criterion_stats(criterion_stats) or "No criterion stats provided."
        )
        criteria_label = ", ".join(rubric_criteria_names) if rubric_criteria_names else "Not provided"

        user_prompt = COHORT_ANALYTICS_USER_PROMPT.format(
            task_title=task_title,
            task_type=task_type,
            task_description=task_description or "No description provided.",
            rubric_criteria_names=criteria_label,
            student_count=student_count,
            average_percentage=average_percentage,
            fail_count=fail_count,
            grades_section=grades_section,
            code_reviews_section=code_reviews_section,
            criterion_stats_section=criterion_stats_section,
        )

        with metrics_collector.track("analyze_cohort_patterns") as record:
            if self.mock_mode:
                response = self._mock_cohort_analytics(
                    task_title=task_title,
                    student_count=student_count,
                    average_percentage=average_percentage,
                    fail_count=fail_count,
                    code_reviews=code_reviews,
                    criterion_stats=criterion_stats,
                    warnings=warnings,
                )
                response.ai_metadata = self._build_metadata(record, warnings=response.warnings)
                return response

            try:
                json_str = self._call_llm(
                    system_prompt=COHORT_ANALYTICS_SYSTEM_PROMPT,
                    user_prompt=user_prompt,
                )
                record.provider = self._last_llm_info.get("provider")
                record.model_used = self._last_llm_info.get("model")
                data = self._clean_and_parse_json(json_str)
                response = CohortAnalyticsResponse(**data)
                response.student_count = student_count
                response.task_title = task_title
                response.warnings = list(dict.fromkeys([*(response.warnings or []), *warnings]))
                response = self._normalize_cohort_analytics(response)
                response.ai_metadata = self._build_metadata(record, warnings=response.warnings)
                return response
            except AnalyticsResponseError:
                record.parse_success = False
                raise
            except Exception as e:
                record.parse_success = False
                logger.error(f"Cohort analytics failed: {e}")
                raise AnalyticsResponseError(f"AI cohort analytics response was invalid: {e}") from e

    def socratic_tutor_chat(
        self,
        reference_text: str,
        chat_history: List[ChatMessage],
        student_message: str,
        task_title: Optional[str] = None,
    ) -> StudentChatResponse:
        history_formatted = "\n".join(
            f"[{msg.role.upper()}]: {msg.content}" for msg in chat_history
        ) if chat_history else "No previous chat history."

        ref_content = reference_text.strip() if reference_text and reference_text.strip() else f"Task: {task_title or 'University Assignment'}"
        ref_for_prompt, _ = self._budget_text(ref_content, Config.MAX_REFERENCE_CHARS, "reference")

        user_prompt = STUDENT_SOCRATIC_TUTOR_USER_PROMPT.format(
            reference_text=ref_for_prompt,
            chat_history_formatted=history_formatted,
            student_message=student_message,
        )

        with metrics_collector.track("socratic_tutor_chat") as record:
            if self.mock_mode:
                response = self._mock_socratic_tutor_response(student_message)
                response.ai_metadata = self._build_metadata(record)
                return response

            try:
                ai_reply = self._call_llm(
                    system_prompt=STUDENT_SOCRATIC_TUTOR_SYSTEM_PROMPT,
                    user_prompt=user_prompt,
                    response_json=False,
                )
                record.provider = self._last_llm_info.get("provider")
                record.model_used = self._last_llm_info.get("model")
                return StudentChatResponse(
                    reply=ai_reply.strip(),
                    ai_metadata=self._build_metadata(record),
                )
            except Exception as e:
                record.parse_success = False
                logger.error(f"Socratic chat failed: {e}")
                raise ChatResponseError(f"AI Socratic tutor failed: {e}") from e

    def lab_assistant_chat(
        self,
        lab_title: str,
        lab_type: str,
        steps_and_theory: str,
        model_answers: str,
        chat_history: List[ChatMessage],
        student_message: str,
    ) -> LabChatResponse:
        history_formatted = "\n".join(
            f"[{msg.role.upper()}]: {msg.content}" for msg in chat_history
        ) if chat_history else "No previous chat history."

        steps_for_prompt, _ = self._budget_text(steps_and_theory or "", Config.MAX_REFERENCE_CHARS, "lab steps")
        answers_for_prompt, _ = self._budget_text(model_answers or "", Config.MAX_GRADING_KEY_CHARS, "model answers")

        user_prompt = LAB_ASSISTANT_USER_PROMPT.format(
            lab_title=lab_title,
            lab_type=lab_type,
            steps_and_theory=steps_for_prompt or "No specific lab steps provided.",
            model_answers=answers_for_prompt or "No model answers provided.",
            chat_history_formatted=history_formatted,
            student_message=student_message,
        )
        detected_mode = "experiment_guide" if lab_type == "experiment" else "coding_hint"

        with metrics_collector.track("lab_assistant_chat") as record:
            if self.mock_mode:
                response = self._mock_lab_assistant_response(lab_title, lab_type, student_message)
                response.ai_metadata = self._build_metadata(record)
                return response

            try:
                ai_reply = self._call_llm(
                    system_prompt=LAB_ASSISTANT_SYSTEM_PROMPT,
                    user_prompt=user_prompt,
                    response_json=False,
                )
                record.provider = self._last_llm_info.get("provider")
                record.model_used = self._last_llm_info.get("model")
                sanitized_reply, was_sanitized = self._sanitize_lab_reply(ai_reply.strip(), model_answers)
                record.output_sanitized = was_sanitized
                return LabChatResponse(
                    reply=sanitized_reply,
                    detected_mode=detected_mode,
                    ai_metadata=self._build_metadata(record),
                )
            except Exception as e:
                record.parse_success = False
                logger.error(f"Lab assistant chat failed: {e}")
                raise ChatResponseError(f"AI Lab assistant failed: {e}") from e

    def _call_llm(self, system_prompt: str, user_prompt: str, response_json: bool = True) -> str:
        if self.provider == "groq" and self._groq_client:
            for model_name in (Config.GROQ_MODEL, Config.GROQ_FALLBACK_MODEL):
                try:
                    logger.info(f"Calling Groq model: {model_name}")
                    kwargs = {
                        "model": model_name,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        "temperature": Config.TEMPERATURE,
                    }
                    if response_json:
                        kwargs["response_format"] = {"type": "json_object"}
                    response = self._groq_client.chat.completions.create(**kwargs)
                    self._last_llm_info = {"provider": "groq", "model": model_name}
                    return response.choices[0].message.content
                except Exception as e:
                    logger.warning(f"Groq model ({model_name}) failed: {e}")

        if self._gemini_client:
            text = self._call_gemini(system_prompt, user_prompt, response_json)
            return text

        raise RuntimeError("All LLM providers failed to execute response generation.")

    def _call_gemini(self, system_prompt: str, user_prompt: str, response_json: bool = True) -> str:
        prompt = f"{system_prompt}\n\n{user_prompt}"
        config = {"response_mime_type": "application/json"} if response_json else {}
        models = []
        for model_name in (Config.GEMINI_MODEL, Config.GEMINI_FALLBACK_MODEL):
            if model_name and model_name not in models:
                models.append(model_name)

        last_error: Optional[Exception] = None
        for model_name in models:
            try:
                logger.info(f"Calling Gemini model: {model_name}")
                response = self._gemini_client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=config,
                )
                self._last_llm_info = {"provider": "gemini", "model": model_name}
                return response.text
            except Exception as e:
                last_error = e
                logger.warning(f"Gemini model ({model_name}) failed: {e}")

        raise RuntimeError(f"All Gemini models failed. Last error: {last_error}")

    def _budget_text(self, text: str, max_chars: int, label: str) -> Tuple[str, bool]:
        if len(text) <= max_chars:
            return text, False
        return text[:max_chars] + f"\n\n[... {label} truncated at {max_chars} characters ...]", True

    def _allocate_grading_context(
        self,
        reference_text: str,
        submission_text: str,
        code_files: Dict[str, str],
        grading_key: str,
    ) -> Tuple[str, str, str, str, List[str], bool]:
        """Token-aware character budgeting across grading prompt sections."""
        total = Config.MAX_TOTAL_PROMPT_CHARS
        ref_cap = min(Config.MAX_REFERENCE_CHARS, int(total * Config.BUDGET_REFERENCE_RATIO))
        sub_cap = min(Config.MAX_SUBMISSION_CHARS, int(total * Config.BUDGET_SUBMISSION_RATIO))
        code_cap = min(Config.MAX_CODE_FILE_CHARS * max(len(code_files), 1), int(total * Config.BUDGET_CODE_RATIO))
        key_cap = min(Config.MAX_GRADING_KEY_CHARS, int(total * 0.08))

        warnings: List[str] = []
        any_truncated = False

        ref_text, t1 = self._budget_text(reference_text, ref_cap, "reference specification")
        if t1:
            warnings.append(f"Reference spec truncated to {ref_cap} characters.")
            any_truncated = True

        sub_text, t2 = self._budget_text(submission_text, sub_cap, "submission text")
        if t2:
            warnings.append(f"Submission text truncated to {sub_cap} characters.")
            any_truncated = True

        key_section = ""
        if grading_key:
            key_text, t3 = self._budget_text(grading_key, key_cap, "grading key")
            if t3:
                warnings.append(f"Grading key truncated to {key_cap} characters.")
                any_truncated = True
            key_section = (
                "--- TA GRADING KEY (INTERNAL VERIFICATION ONLY — DO NOT QUOTE TO STUDENT) ---\n"
                f"{key_text}\n"
            )

        code_section = ""
        if code_files:
            per_file_cap = max(500, code_cap // max(len(code_files), 1))
            blocks = []
            for fname, content in code_files.items():
                truncated_content, t4 = self._budget_text(content, per_file_cap, f"code file '{fname}'")
                if t4:
                    warnings.append(f"Code file '{fname}' truncated to {per_file_cap} characters.")
                    any_truncated = True
                blocks.append(f"--- FILE: {fname} ---\n{truncated_content}\n")
            code_section = "--- SUBMITTED CODE FILES ---\n" + "\n".join(blocks)

        return ref_text, sub_text, code_section, key_section, warnings, any_truncated

    def _normalize_rubric_response(self, response: RubricSuggestionResponse) -> RubricSuggestionResponse:
        warnings: List[str] = list(response.warnings or [])
        if not response.criteria:
            raise RubricResponseError("Rubric must contain at least one criterion.")

        if len(response.criteria) < Config.MIN_RUBRIC_CRITERIA:
            warnings.append(f"Rubric has fewer than {Config.MIN_RUBRIC_CRITERIA} criteria.")
        if len(response.criteria) > Config.MAX_RUBRIC_CRITERIA:
            warnings.append(f"Rubric exceeds {Config.MAX_RUBRIC_CRITERIA} criteria; review recommended.")

        computed_total = round(sum(c.max_points for c in response.criteria), 2)
        if abs(response.total_max_points - computed_total) > 0.01:
            warnings.append(
                f"Total points adjusted from {response.total_max_points} to {computed_total} to match criteria sum."
            )
            response.total_max_points = computed_total
        else:
            response.total_max_points = computed_total

        response.warnings = warnings
        return response

    def _normalize_grading_response(
        self,
        response: SubmissionGradingResponse,
        rubric_criteria: List[Union[RubricCriteriaItem, dict]],
        prep_warnings: Optional[List[str]] = None,
    ) -> SubmissionGradingResponse:
        rubric_max_by_name: Dict[str, float] = {}
        norm_rubric_map: Dict[str, float] = {}
        rubric_names: List[str] = []
        total_possible = 0.0

        def _norm_key(k: str) -> str:
            return re.sub(r"^[0-9\.\s\-]+", "", k.strip().lower())

        for item in rubric_criteria:
            if isinstance(item, RubricCriteriaItem):
                name, max_pts = item.name, item.max_points
            else:
                name = str(item.get("name", ""))
                max_pts = float(item.get("max_points", 0))
            rubric_max_by_name[name] = max_pts
            norm_rubric_map[_norm_key(name)] = max_pts
            rubric_names.append(name)
            total_possible += max_pts

        normalized_evaluations: List[CriterionEvaluation] = []
        total_awarded = 0.0
        warnings = list(prep_warnings or [])
        scores_adjusted = False
        evaluated_names = set()

        for evaluation in response.criterion_evaluations:
            c_name = evaluation.criterion_name
            evaluated_names.add(_norm_key(c_name))
            rubric_max = rubric_max_by_name.get(c_name)
            if rubric_max is None:
                rubric_max = norm_rubric_map.get(_norm_key(c_name), evaluation.max_points)

            capped_score = min(max(evaluation.score_given, 0.0), rubric_max)
            if capped_score != evaluation.score_given:
                scores_adjusted = True
                warnings.append(
                    f"Score for '{c_name}' adjusted from {evaluation.score_given} to {capped_score} (rubric max)."
                )
            if not (evaluation.reasoning or "").strip():
                warnings.append(f"Criterion '{c_name}' has empty reasoning; manual review recommended.")

            total_awarded += capped_score
            normalized_evaluations.append(
                CriterionEvaluation(
                    criterion_name=c_name,
                    score_given=capped_score,
                    max_points=rubric_max,
                    reasoning=evaluation.reasoning,
                )
            )

        missing = [n for n in rubric_names if _norm_key(n) not in evaluated_names]
        if missing:
            warnings.append(f"AI did not evaluate these rubric criteria: {', '.join(missing)}. Manual review required.")
        if len(normalized_evaluations) != len(rubric_criteria):
            warnings.append(
                f"Criterion count mismatch: rubric has {len(rubric_criteria)}, AI returned {len(normalized_evaluations)}."
            )

        if total_possible <= 0:
            total_possible = sum(e.max_points for e in normalized_evaluations) or 100.0

        response.criterion_evaluations = normalized_evaluations
        response.ai_suggested_grade = round(total_awarded, 2)
        response.total_possible_grade = round(total_possible, 2)
        response.percentage = round(min((total_awarded / total_possible) * 100, 100.0), 2)
        response.warnings = warnings
        return response

    def _sanitize_lab_reply(self, reply: str, model_answers: str) -> Tuple[str, bool]:
        """Anti-leak guardrail: block large copied segments from model answers."""
        if not model_answers or not reply:
            return reply, False

        reply_lower = reply.lower()
        leak_phrases = [
            "here is the complete solution",
            "here is the full code",
            "the answer is:",
            "model answer:",
            "final solution:",
        ]
        if any(p in reply_lower for p in leak_phrases):
            return (
                "I can guide you step-by-step, but I cannot provide the direct final answer or full solution code. "
                "What part of the lab are you working on right now?",
                True,
            )

        # Detect long verbatim overlap from model answers (>= 80 chars contiguous substring)
        normalized_answers = re.sub(r"\s+", " ", model_answers.strip())
        for chunk_start in range(0, max(len(normalized_answers) - 80, 1), 40):
            chunk = normalized_answers[chunk_start:chunk_start + 80]
            if len(chunk) >= 80 and chunk.lower() in reply.lower():
                return (
                    "I can help with hints and procedural guidance, but I cannot repeat the TA model answer directly. "
                    "Tell me which step you are stuck on and what you have tried so far.",
                    True,
                )

        return reply, False

    def _clean_and_parse_json(self, json_str: str) -> dict:
        cleaned = json_str.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
            cleaned = re.sub(r"\s*```$", "", cleaned)
        return json.loads(cleaned)

    def _format_cohort_grades(self, grades: List[CohortGradeSnapshot]) -> str:
        lines = []
        for i, g in enumerate(grades, start=1):
            pct = round((g.grade / g.max_grade) * 100.0, 1) if g.max_grade else 0.0
            feedback = (g.feedback or "").strip() or "(no feedback)"
            if len(feedback) > 280:
                feedback = feedback[:277] + "..."
            lines.append(f"{i}. grade={g.grade}/{g.max_grade} ({pct}%) | feedback: {feedback}")
        return "\n".join(lines)

    def _format_cohort_code_reviews(self, reviews: List[CohortCodeReviewSnapshot]) -> str:
        lines = []
        for i, r in enumerate(reviews, start=1):
            path = r.file_path or "(unspecified file)"
            lines.append(
                f"{i}. [{r.severity}] count={r.count} file={path} | {r.finding.strip()}"
            )
        return "\n".join(lines)

    def _format_cohort_criterion_stats(self, stats: List[CohortCriterionSnapshot]) -> str:
        lines = []
        for s in stats:
            ratio = round((s.average_score / s.max_points) * 100.0, 1) if s.max_points else 0.0
            lines.append(
                f"- {s.criterion_name}: avg {s.average_score}/{s.max_points} ({ratio}%), "
                f"low_score_count={s.low_score_count}"
            )
        return "\n".join(lines)

    def _normalize_cohort_analytics(self, response: CohortAnalyticsResponse) -> CohortAnalyticsResponse:
        warnings = list(response.warnings or [])
        if not response.summary or not response.summary.strip():
            raise AnalyticsResponseError("Cohort analytics summary is empty.")

        allowed = {"info", "warning", "critical"}
        for issue in response.common_issues:
            sev = (issue.severity or "warning").strip().lower()
            if sev not in allowed:
                warnings.append(f"Normalized unknown severity '{issue.severity}' to 'warning'.")
                issue.severity = "warning"
            else:
                issue.severity = sev

        if not response.common_issues and not response.misconceptions and not response.teaching_focus:
            warnings.append("Model returned no common issues, misconceptions, or teaching focus items.")

        response.warnings = warnings
        return response

    def _mock_cohort_analytics(
        self,
        task_title: str,
        student_count: int,
        average_percentage: float,
        fail_count: int,
        code_reviews: List[CohortCodeReviewSnapshot],
        criterion_stats: List[CohortCriterionSnapshot],
        warnings: List[str],
    ) -> CohortAnalyticsResponse:
        common_issues: List[CommonIssue] = []
        misconceptions: List[Misconception] = []
        teaching_focus: List[str] = []

        if code_reviews:
            top = sorted(code_reviews, key=lambda r: r.count, reverse=True)[0]
            common_issues.append(
                CommonIssue(
                    title="Repeated code-review finding",
                    description=top.finding,
                    severity=top.severity if top.severity in {"info", "warning", "critical"} else "warning",
                    affected_estimate=f"seen {top.count} time(s) across the cohort",
                    evidence=f"Top aggregated finding on {top.file_path or 'unspecified file'}",
                )
            )
            teaching_focus.append(f"Revisit the issue: {top.finding[:120]}")

        weak_criteria = [
            s for s in criterion_stats
            if s.max_points > 0 and (s.average_score / s.max_points) < 0.6
        ]
        for s in weak_criteria[:3]:
            misconceptions.append(
                Misconception(
                    concept=s.criterion_name,
                    description=f"Class average is low on '{s.criterion_name}'.",
                    suggested_remediation=f"Re-teach or give a short example focused on '{s.criterion_name}'.",
                )
            )
            teaching_focus.append(f"Strengthen understanding of '{s.criterion_name}'")

        if fail_count > 0:
            common_issues.append(
                CommonIssue(
                    title="Students below passing threshold",
                    description=f"{fail_count} of {student_count} latest attempts scored below 50%.",
                    severity="critical" if fail_count >= max(1, student_count // 3) else "warning",
                    affected_estimate=f"{fail_count}/{student_count}",
                    evidence="Derived from anonymized grade percentages.",
                )
            )

        if not common_issues:
            common_issues.append(
                CommonIssue(
                    title="No dominant shared error detected",
                    description="Mock analysis did not find a strong repeated code-review pattern.",
                    severity="info",
                    affected_estimate="n/a",
                    evidence="Limited or empty code-review aggregates.",
                )
            )

        if not teaching_focus:
            teaching_focus.append(f"Review class average ({average_percentage}%) and sample feedback themes.")

        return CohortAnalyticsResponse(
            task_title=task_title,
            student_count=student_count,
            summary=(
                f"Mock cohort summary for '{task_title}': "
                f"{student_count} students, average {average_percentage}%, {fail_count} below 50%."
            ),
            common_issues=common_issues,
            misconceptions=misconceptions,
            teaching_focus=teaching_focus,
            warnings=list(warnings),
        )

    def _mock_suggest_rubric(self, task_title: str, task_type: str) -> RubricSuggestionResponse:
        criteria = [
            RubricCriteriaItem(
                name=f"{task_title} Core Implementation",
                description=f"Accurate implementation of requirements for '{task_title}'.",
                max_points=40.0,
                sort_order=1,
            ),
            RubricCriteriaItem(
                name="Edge Case Handling",
                description="Handles boundary conditions and error cases.",
                max_points=30.0,
                sort_order=2,
            ),
            RubricCriteriaItem(
                name="Documentation & Presentation",
                description="Clear structure, comments, and write-up quality.",
                max_points=30.0,
                sort_order=3,
            ),
        ]
        return RubricSuggestionResponse(
            task_title=task_title,
            criteria=criteria,
            total_max_points=100.0,
            rationale=f"Domain-tailored rubric for '{task_title}' ({task_type}).",
        )

    def _mock_grade_submission(
        self,
        rubric_criteria: List[Union[RubricCriteriaItem, dict]],
        code_files: Optional[Dict[str, str]] = None,
        warnings: Optional[List[str]] = None,
    ) -> SubmissionGradingResponse:
        evaluations = []
        total_awarded = 0.0
        total_possible = 0.0

        for item in rubric_criteria:
            if isinstance(item, RubricCriteriaItem):
                c_name, max_pts = item.name, item.max_points
            else:
                c_name = item.get("name", "Criterion")
                max_pts = float(item.get("max_points", 25.0))

            awarded = round(max_pts * 0.9, 1)
            total_awarded += awarded
            total_possible += max_pts
            evaluations.append(
                CriterionEvaluation(
                    criterion_name=c_name,
                    score_given=awarded,
                    max_points=max_pts,
                    reasoning=f"Strong performance on '{c_name}' with minor improvements possible.",
                )
            )

        pct = round((total_awarded / total_possible) * 100, 2) if total_possible > 0 else 0.0
        code_reviews = []
        if code_files:
            code_reviews = [
                CodeReviewFinding(
                    file_path=next(iter(code_files.keys())),
                    line_number=None,
                    severity="info",
                    finding="Consider adding clearer variable names and inline comments.",
                ),
            ]

        return SubmissionGradingResponse(
            ai_suggested_grade=total_awarded,
            total_possible_grade=total_possible,
            percentage=pct,
            summary_feedback=f"Mock grading result: {pct}% across criteria.",
            criterion_evaluations=evaluations,
            code_reviews=code_reviews,
            warnings=list(warnings or []),
        )

    def _mock_socratic_tutor_response(self, student_message: str) -> StudentChatResponse:
        msg_lower = student_message.lower()
        if any(w in msg_lower for w in ["code", "solution", "answer", "solve", "direct"]):
            reply = "I cannot write the direct code or solution for you. What have you tried so far?"
        else:
            reply = f"Good question about '{student_message}'. What is the main objective of this step?"
        return StudentChatResponse(reply=reply)

    def _mock_lab_assistant_response(self, lab_title: str, lab_type: str, student_message: str) -> LabChatResponse:
        mode = "experiment_guide" if lab_type == "experiment" else "coding_hint"
        msg_lower = student_message.lower()

        if mode == "experiment_guide":
            if "step" in msg_lower or "procedure" in msg_lower or "how" in msg_lower:
                reply = f"Step Guidance for {lab_title}: follow the uploaded procedure and verify equipment setup before measurements."
            else:
                reply = f"Lab assistant ready for '{lab_title}'. Ask about steps, theory, or debugging hints."
        elif any(w in msg_lower for w in ["code", "solution", "answer", "write", "give me"]):
            reply = f"Hint Only Mode for {lab_title}: I cannot give direct solution code. What have you tried so far?"
        else:
            reply = f"Coding guide for '{lab_title}': break the problem into smaller steps and check edge cases."

        return LabChatResponse(reply=reply, detected_mode=mode)
