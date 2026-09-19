import type { components } from "./schema";
type S = components["schemas"];
export type Identity = S["IdentityResponse"];
export type Task = S["TaskListItemResponse"];
export type TaskDetail = S["TaskDetailResponse"];
export type Attempt = S["SubmissionListItemResponse"];
export type QueueItem = S["SubmissionQueueItem"];
export type Rubric = S["RubricListItem"];
export type Criterion = S["RubricCriterionInput"];
// Feature adapters narrow JSON persistence fields from the generated transport.
export type Submission = Omit<
  S["SubmissionDetailResponse"],
  "artifacts" | "rubric_criteria" | "criterion_evaluations" | "code_reviews"
> & {
  artifacts: { file_id: number; file_name: string; file_type: string }[];
  rubric_criteria: Criterion[];
  criterion_evaluations:
    | {
        criterion_name: string;
        score_given: number;
        max_points: number;
        reasoning: string;
      }[]
    | null;
  code_reviews:
    | {
        file_path: string;
        line_number: number | null;
        severity: string;
        finding: string;
      }[]
    | null;
};
