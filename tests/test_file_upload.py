import os
import sys
from evaluator import AIEvaluationEngine
from file_parser import extract_text_from_file, extract_submission_content

sys.stdout.reconfigure(encoding='utf-8')


def demo_file_upload():
    print("=" * 70)
    print("AI EVALUATION ENGINE - FILE UPLOAD DEMO")
    print("=" * 70)

    engine = AIEvaluationEngine()

    # Step 1: Upload Reference Document (e.g. sample_spec.pdf or spec PDF/TXT)
    spec_path = "sample_spec.pdf"
    print(f"\n[1] Extracting reference specification from uploaded file: '{spec_path}'...")

    if os.path.exists(spec_path):
        spec_text = extract_text_from_file(spec_path)
        print(f"-> Successfully extracted {len(spec_text)} characters from '{spec_path}'.")
    else:
        spec_text = "Sample task specification for AI System Architecture evaluation."
        print(f"-> Spec file not found, using sample text.")

    # Step 2: Generate AI Rubric from uploaded spec file
    print("\n[2] Generating AI Rubric from uploaded specification file...")
    rubric_response = engine.suggest_rubric(
        task_title="AI System Architecture Spec Evaluation",
        task_type="assignment",
        task_description="Evaluate student proposals for AI Content Access architecture (Simple Context vs RAG).",
        reference_text=spec_text[:4000],  # Simple Context chunk
    )

    print(f"\n-> Rubric Created from uploaded file! Rationale:\n   {rubric_response.rationale}\n")
    print("Generated Criteria:")
    for c in rubric_response.criteria:
        print(f"  - [{c.sort_order}] {c.name} ({c.max_points} pts): {c.description}")

    # Step 3: Upload Student Submission File(s)
    # Create a temporary student code file to simulate file upload
    sample_student_file = "student_proposal.py"
    with open(sample_student_file, "w", encoding="utf-8") as f:
        f.write('''
# Student Architecture Submission: Simple Context vs RAG

def suggest_rubric(task_id: int):
    # Load reference spec file directly
    ref_text = get_reference_file(task_id)
    prompt = f"Reference: {ref_text}\\nGenerate rubric."
    return call_groq(prompt)

def grade_submission(submission_id: int):
    # Retrieve submission text
    sub_text = get_submission_file(submission_id)
    ref_text = get_reference_file(task_id)
    prompt = f"Spec: {ref_text}\\nSubmission: {sub_text}\\nGrade submission."
    return call_groq(prompt)
''')

    print(f"\n[3] Extracting student submission content from uploaded file: '{sample_student_file}'...")
    sub_text, code_files = extract_submission_content(sample_student_file)
    print(f"-> Extracted {len(code_files)} code file(s): {list(code_files.keys())}")

    # Step 4: Grade Student Submission Files against the Rubric
    print("\n[4] Grading Student Submission File against the AI Rubric...")
    grading_response = engine.grade_submission(
        task_title="AI System Architecture Spec Evaluation",
        task_type="assignment",
        reference_text=spec_text[:4000],
        rubric_criteria=rubric_response.criteria,
        submission_text=sub_text,
        code_files=code_files,
    )

    print("\n" + "=" * 70)
    print(f"FILE EVALUATION RESULT: {grading_response.ai_suggested_grade} / {grading_response.total_possible_grade} ({grading_response.percentage}%)")
    print("=" * 70)
    print(f"Summary Feedback:\n{grading_response.summary_feedback}\n")

    print("Criterion Breakdown:")
    for eval_item in grading_response.criterion_evaluations:
        print(f"  - {eval_item.criterion_name}: {eval_item.score_given}/{eval_item.max_points} pts")
        print(f"    Reasoning: {eval_item.reasoning}")

    if grading_response.code_reviews:
        print("\nCode Review Findings:")
        for rev in grading_response.code_reviews:
            print(f"  - [{rev.severity.upper()}] {rev.file_path}:{rev.line_number or 'N/A'} - {rev.finding}")

    # Cleanup temp file
    if os.path.exists(sample_student_file):
        os.remove(sample_student_file)


if __name__ == "__main__":
    demo_file_upload()
