import json
import logging
import os
import shutil
import tempfile
from typing import Optional, List, Dict

from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from ai_tutor import AIService, ChatResponseError, GradingResponseError, RubricResponseError
from ai_tutor.config import Config
from ai_tutor.engine import AIEvaluationEngine
from ai_tutor.parsers import extract_text_from_file, extract_submission_content
from ai_tutor.models import (
    RubricCriteriaItem,
    StudentChatRequest,
    LabItem,
    LabSubmission,
    LabChatRequest,
    RubricSuggestRequest,
    RubricRefineRequest,
    GradeSubmissionRequest,
    SocraticChatRequest,
    LabAssistantChatRequest,
)

logger = logging.getLogger("AIEvaluationApp")

app = FastAPI(title="AI Evaluation Assistant Web App", version="1.4.0")


# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize AI Service (backend integration entry point)
engine = AIEvaluationEngine()
ai_service = AIService(engine)

# Ensure static directory exists
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)
LABS_FILE = os.path.join(DATA_DIR, "labs_data.json")
SUBMISSIONS_FILE = os.path.join(DATA_DIR, "submissions_data.json")

DEFAULT_LABS: Dict[str, LabItem] = {
    "lab-1": LabItem(
        id="lab-1",
        title="Lab 1: RC Circuit Transient Dynamics (Experiment)",
        lab_type="experiment",
        description="Hardware experiment analyzing RC circuit step response, time constant tau, and phase lag on an oscilloscope.",
        steps_and_theory="""--- LAB STEPS & PROCEDURES ---
Step 1: Wire a 1k Ohm resistor and 10uF capacitor in series across a function generator outputting 5V peak-to-peak square wave at 50Hz.
Step 2: Connect Oscilloscope Probe 1 to Channel 1 (Input V_in) and Probe 2 to Channel 2 (Capacitor voltage V_cap).
Step 3: Measure the time constant tau from 0% to 63.2% of peak voltage.
Step 4: Theoretical Q1: How does increasing resistance R affect the charging time constant tau?
Step 5: Theoretical Q2: Derive the formula for cutoff frequency f_c from the transfer function.""",
        model_answers="""--- TA MODEL ANSWERS ---
Step 3 Expected Value: tau = R * C = 1000 * 10 * 10^-6 = 10 ms.
Theoretical Q1 Answer: Increasing R increases tau, meaning the capacitor takes longer to charge.
Theoretical Q2 Answer: f_c = 1 / (2 * pi * R * C) = 15.91 Hz.""",
        rubric_json="""[
  {"name": "Hardware Wiring & Measurement Correctness", "description": "Proper circuit setup and accurate measurement of time constant tau.", "max_points": 50.0, "sort_order": 1},
  {"name": "Theoretical Analysis & Derivations", "description": "Correct derivation of cutoff frequency and analysis of R/C variations.", "max_points": 50.0, "sort_order": 2}
]"""
    ),
    "lab-2": LabItem(
        id="lab-2",
        title="Lab 2: Binary Search Tree Implementation (Coding)",
        lab_type="coding",
        description="Implementation of BST insertion, search, and in-order traversal in C++/Python.",
        steps_and_theory="""--- CODING LAB REQUIREMENTS ---
Task 1: Implement insert(root, value) to add nodes into the BST.
Task 2: Implement search(root, key) returning true if key exists.
Task 3: Implement inorder_traversal(root) printing values in sorted ascending order.
Theoretical Question: What is the worst-case time complexity of BST insertion, and how can a balanced tree (AVL/Red-Black) prevent it?""",
        model_answers="""--- TA MODEL SOLUTION ---
TreeNode* insert(TreeNode* root, int val) {
    if (!root) return new TreeNode(val);
    if (val < root->val) root->left = insert(root->left, val);
    else root->right = insert(root->right, val);
    return root;
}
Worst case complexity: O(N) when tree degenerates into a linked list.""",
        rubric_json="""[
  {"name": "BST Core Implementation", "description": "Correct recursive/iterative insertion and search algorithms.", "max_points": 60.0, "sort_order": 1},
  {"name": "Memory & Edge Case Handling", "description": "Null pointer checks, empty trees, and memory cleanup.", "max_points": 40.0, "sort_order": 2}
]"""
    )
}

def load_labs_from_disk() -> Dict[str, LabItem]:
    if os.path.exists(LABS_FILE):
        try:
            with open(LABS_FILE, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
                return {k: LabItem(**v) for k, v in raw_data.items()}
        except Exception as e:
            pass
    return dict(DEFAULT_LABS)

def save_labs_to_disk():
    try:
        raw_data = {k: v.model_dump() for k, v in LABS_DB.items()}
        with open(LABS_FILE, "w", encoding="utf-8") as f:
            json.dump(raw_data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        pass

def load_submissions_from_disk() -> List[LabSubmission]:
    if os.path.exists(SUBMISSIONS_FILE):
        try:
            with open(SUBMISSIONS_FILE, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
                return [LabSubmission(**v) for v in raw_data]
        except Exception as e:
            pass
    return []

def save_submissions_to_disk():
    try:
        raw_data = [s.model_dump() for s in SUBMISSIONS_DB]
        with open(SUBMISSIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(raw_data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        pass

LABS_DB: Dict[str, LabItem] = load_labs_from_disk()
SUBMISSIONS_DB: List[LabSubmission] = load_submissions_from_disk()


@app.get("/", response_class=HTMLResponse)
def get_dashboard():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>AI Evaluation Assistant Web App Running!</h1>"


@app.get("/api/ai/health")
def api_ai_health():
    """AI layer health check for backend integration."""
    return {
        "status": "ok",
        "mock_mode": engine.mock_mode,
        "provider": engine.provider,
        "ai_engine_version": Config.AI_ENGINE_VERSION,
        "prompt_version": Config.PROMPT_VERSION,
    }


@app.get("/api/ai/metrics")
def api_ai_metrics():
    """Recent AI evaluation metrics summary for observability."""
    return {
        "summary": ai_service.metrics_summary(),
        "recent": ai_service.recent_metrics(limit=20),
    }


# --- LAB MANAGEMENT & AI LAB ASSISTANT ENDPOINTS ---

@app.get("/api/labs")
def api_get_labs():
    """List all available labs configured by TAs."""
    return list(LABS_DB.values())


@app.get("/api/labs/{lab_id}")
def api_get_lab_by_id(lab_id: str):
    """Fetch details of a specific lab by ID."""
    if lab_id not in LABS_DB:
        raise HTTPException(status_code=404, detail=f"Lab '{lab_id}' not found.")
    return LABS_DB[lab_id]


@app.api_route("/api/delete-lab/{lab_id:path}", methods=["GET", "POST", "DELETE"])
@app.api_route("/api/labs/{lab_id:path}", methods=["DELETE"])
def api_delete_lab(lab_id: str):
    """
    TA Endpoint: Delete a lab and its associated student submissions.
    Supports matching by lab ID or lab title (case-insensitive).
    """
    target_id = None
    if lab_id in LABS_DB:
        target_id = lab_id
    else:
        norm_input = lab_id.strip().lower()
        for k, v in LABS_DB.items():
            if k.lower() == norm_input or v.title.strip().lower() == norm_input:
                target_id = k
                break

    if not target_id:
        raise HTTPException(status_code=404, detail=f"Lab '{lab_id}' not found in active labs list.")

    deleted_lab = LABS_DB.pop(target_id)
    save_labs_to_disk()

    global SUBMISSIONS_DB
    SUBMISSIONS_DB = [s for s in SUBMISSIONS_DB if s.lab_id != target_id]
    save_submissions_to_disk()

    return {
        "success": True,
        "message": f"Lab '{deleted_lab.title}' deleted successfully.",
        "deleted_lab_id": target_id
    }


@app.post("/api/create-lab")
async def api_create_lab(
    title: str = Form(...),
    lab_type: str = Form("experiment"),
    description: str = Form(""),
    steps_and_theory_file: Optional[UploadFile] = File(None),
    steps_and_theory_text: Optional[str] = Form(None),
    model_answers_file: Optional[UploadFile] = File(None),
    model_answers_text: Optional[str] = Form(None),
    rubric_json: Optional[str] = Form("[]"),
):
    """
    TA Endpoint: Create or Update a Lab with steps, theoretical questions, and model answers.
    Prevents duplicate lab creation by checking existing titles.
    """
    clean_title = title.strip()
    if not clean_title:
        raise HTTPException(status_code=400, detail="Lab title cannot be empty.")

    # Check if a lab with the same title (case-insensitive) already exists
    existing_lab = next(
        (lab for lab in LABS_DB.values() if lab.title.strip().lower() == clean_title.lower()),
        None
    )

    steps_text = ""
    if steps_and_theory_file and steps_and_theory_file.filename:
        temp_dir = tempfile.mkdtemp()
        temp_path = os.path.join(temp_dir, steps_and_theory_file.filename)
        try:
            with open(temp_path, "wb") as buf:
                shutil.copyfileobj(steps_and_theory_file.file, buf)
            steps_text = extract_text_from_file(temp_path)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    elif steps_and_theory_text and steps_and_theory_text.strip():
        steps_text = steps_and_theory_text.strip()

    answers_text = ""
    if model_answers_file and model_answers_file.filename:
        temp_dir = tempfile.mkdtemp()
        temp_path = os.path.join(temp_dir, model_answers_file.filename)
        try:
            with open(temp_path, "wb") as buf:
                shutil.copyfileobj(model_answers_file.file, buf)
            answers_text = extract_text_from_file(temp_path)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    elif model_answers_text and model_answers_text.strip():
        answers_text = model_answers_text.strip()

    if existing_lab:
        # Update existing lab instead of creating duplicate entry
        existing_lab.title = clean_title
        existing_lab.lab_type = lab_type
        if description:
            existing_lab.description = description
        if steps_text:
            existing_lab.steps_and_theory = steps_text
        if answers_text:
            existing_lab.model_answers = answers_text
        if rubric_json and rubric_json != "[]":
            existing_lab.rubric_json = rubric_json
        save_labs_to_disk()
        return existing_lab.model_dump()

    lab_id = f"lab-{len(LABS_DB) + 1}"
    new_lab = LabItem(
        id=lab_id,
        title=clean_title,
        lab_type=lab_type,
        description=description,
        steps_and_theory=steps_text,
        model_answers=answers_text,
        rubric_json=rubric_json or "[]",
    )
    LABS_DB[lab_id] = new_lab
    save_labs_to_disk()
    return new_lab.model_dump()


@app.post("/api/lab-chat")
async def api_lab_chat(req: LabChatRequest):
    """
    Student Endpoint: Scoped AI Lab Assistant Chat.
    Uses TA uploaded files (steps, theory questions, model answers) for context.
    Provides step guidance for experiment labs & hints for coding labs without leaking solutions.
    """
    if req.lab_id not in LABS_DB:
        raise HTTPException(status_code=404, detail=f"Selected lab '{req.lab_id}' does not exist.")

    target_lab = LABS_DB[req.lab_id]

    try:
        chat_resp = ai_service.lab_assistant_chat(
            LabAssistantChatRequest(
                lab_title=target_lab.title,
                lab_type=target_lab.lab_type,
                steps_and_theory=target_lab.steps_and_theory,
                model_answers=target_lab.model_answers,
                chat_history=req.chat_history,
                student_message=req.student_message,
            )
        )
        return chat_resp.model_dump()
    except ChatResponseError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Lab Assistant error: {e}")


@app.post("/api/submit-lab")
async def api_submit_lab(
    lab_id: str = Form(...),
    student_name: str = Form(...),
    student_id: str = Form(...),
    submission_text_override: Optional[str] = Form(None),
    submission_file: Optional[UploadFile] = File(None),
):
    """
    Student Endpoint: Submit completed lab work after lab finishes.
    """
    if lab_id not in LABS_DB:
        raise HTTPException(status_code=404, detail=f"Lab '{lab_id}' not found.")

    sub_text = ""
    code_files: Dict[str, str] = {}
    if submission_file and submission_file.filename:
        temp_dir = tempfile.mkdtemp()
        temp_path = os.path.join(temp_dir, submission_file.filename)
        try:
            with open(temp_path, "wb") as buf:
                shutil.copyfileobj(submission_file.file, buf)
            sub_text, code_files = extract_submission_content(temp_path)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    elif submission_text_override and submission_text_override.strip():
        sub_text = submission_text_override.strip()
    else:
        raise HTTPException(status_code=400, detail="Please upload a submission file or enter your lab answers.")

    import datetime
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sub_id = f"sub-{len(SUBMISSIONS_DB) + 1}"

    submission = LabSubmission(
        id=sub_id,
        lab_id=lab_id,
        student_name=student_name,
        student_id=student_id,
        submission_text=sub_text,
        code_files=code_files,
        submitted_at=timestamp,
        status="submitted",
    )
    SUBMISSIONS_DB.append(submission)
    save_submissions_to_disk()
    return submission.model_dump()


@app.get("/api/submissions/{lab_id}")
def api_get_submissions_for_lab(lab_id: str):
    """TA Endpoint: View all submissions for a given lab."""
    return [s.model_dump() for s in SUBMISSIONS_DB if s.lab_id == lab_id]


@app.post("/api/grade-lab-submission/{submission_id}")
def api_grade_lab_submission(submission_id: str):
    """TA Endpoint: Trigger AI auto-grading for a student submission against TA lab rubric & model answers."""
    target_sub = next((s for s in SUBMISSIONS_DB if s.id == submission_id), None)
    if not target_sub:
        raise HTTPException(status_code=404, detail=f"Submission '{submission_id}' not found.")

    target_lab = LABS_DB.get(target_sub.lab_id)
    if not target_lab:
        raise HTTPException(status_code=404, detail="Target lab not found.")

    try:
        raw_criteria = json.loads(target_lab.rubric_json) if target_lab.rubric_json else []
        rubric_criteria = [RubricCriteriaItem(**item) for item in raw_criteria]
    except Exception:
        rubric_criteria = []

    if not rubric_criteria:
        raise HTTPException(status_code=400, detail="Lab has no rubric criteria configured.")

    try:
        grading_resp = ai_service.grade_submission(
            GradeSubmissionRequest(
                task_title=target_lab.title,
                task_type=target_lab.lab_type,
                reference_text=target_lab.steps_and_theory or target_lab.description,
                rubric_criteria=rubric_criteria,
                submission_text=target_sub.submission_text,
                code_files=target_sub.code_files or {},
                grading_key=target_lab.model_answers or None,
            )
        )
    except GradingResponseError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    target_sub.grade_result = grading_resp
    target_sub.status = "graded"
    save_submissions_to_disk()
    return target_sub.model_dump()


@app.post("/api/grade-all-submissions/{lab_id}")
def api_grade_all_submissions(lab_id: str):
    """TA Endpoint: Batch auto-grade all student submissions for a given lab."""
    target_lab = LABS_DB.get(lab_id)
    if not target_lab:
        raise HTTPException(status_code=404, detail="Target lab not found.")

    lab_subs = [s for s in SUBMISSIONS_DB if s.lab_id == lab_id]
    if not lab_subs:
        return {"graded_count": 0, "message": "No student submissions found for this lab."}

    try:
        raw_criteria = json.loads(target_lab.rubric_json) if target_lab.rubric_json else []
        rubric_criteria = [RubricCriteriaItem(**item) for item in raw_criteria]
    except Exception:
        rubric_criteria = []

    graded_count = 0
    errors: List[str] = []
    for sub in lab_subs:
        try:
            grading_resp = ai_service.grade_submission(
                GradeSubmissionRequest(
                    task_title=target_lab.title,
                    task_type=target_lab.lab_type,
                    reference_text=target_lab.steps_and_theory or target_lab.description,
                    rubric_criteria=rubric_criteria,
                    submission_text=sub.submission_text,
                    code_files=sub.code_files or {},
                    grading_key=target_lab.model_answers or None,
                )
            )
            sub.grade_result = grading_resp
            sub.status = "graded"
            graded_count += 1
        except Exception as e:
            logger.error(f"Failed batch grading for submission {sub.id}: {e}")
            errors.append(f"{sub.id}: {e}")

    save_submissions_to_disk()
    return {
        "graded_count": graded_count,
        "total_submissions": len(lab_subs),
        "errors": errors,
        "submissions": [s.model_dump() for s in lab_subs],
    }


# --- EXISTING RUBRIC GENERATION & EVALUATION ENDPOINTS ---

@app.post("/api/suggest-rubric")
async def api_suggest_rubric(
    task_title: str = Form(...),
    task_type: str = Form("lab"),
    task_description: str = Form(""),
    spec_file: Optional[UploadFile] = File(None),
    spec_text_override: Optional[str] = Form(None),
):
    """
    Generate an AI Rubric from an uploaded spec file (PDF/DOCX/TXT) or raw spec text.
    """
    spec_text = ""

    if spec_file and spec_file.filename:
        temp_dir = tempfile.mkdtemp()
        temp_file_path = os.path.join(temp_dir, spec_file.filename)
        try:
            with open(temp_file_path, "wb") as buffer:
                shutil.copyfileobj(spec_file.file, buffer)
            spec_text = extract_text_from_file(temp_file_path)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to read spec file '{spec_file.filename}': {e}")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    elif spec_text_override and spec_text_override.strip():
        spec_text = spec_text_override.strip()

    try:
        rubric_response = ai_service.suggest_rubric(
            RubricSuggestRequest(
                task_title=task_title,
                task_type=task_type,
                task_description=task_description,
                reference_text=spec_text,
            )
        )
        return rubric_response.model_dump()
    except RubricResponseError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Engine evaluation error: {e}")


@app.post("/api/refine-rubric")
async def api_refine_rubric(
    task_title: str = Form(...),
    task_type: str = Form("lab"),
    task_description: str = Form(""),
    rubric_json: str = Form(...),
    staff_feedback: str = Form(...),
    spec_file: Optional[UploadFile] = File(None),
    spec_text_override: Optional[str] = Form(None),
):
    """
    Refine an existing rubric based on staff feedback instructions.
    """
    try:
        raw_criteria = json.loads(rubric_json)
        previous_criteria = [RubricCriteriaItem(**item) for item in raw_criteria]
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid previous rubric criteria format: {e}")

    spec_text = ""
    if spec_file and spec_file.filename:
        temp_dir = tempfile.mkdtemp()
        temp_file_path = os.path.join(temp_dir, spec_file.filename)
        try:
            with open(temp_file_path, "wb") as buffer:
                shutil.copyfileobj(spec_file.file, buffer)
            spec_text = extract_text_from_file(temp_file_path)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    elif spec_text_override and spec_text_override.strip():
        spec_text = spec_text_override.strip()

    try:
        refined_response = ai_service.refine_rubric(
            RubricRefineRequest(
                task_title=task_title,
                task_type=task_type,
                task_description=task_description,
                reference_text=spec_text,
                previous_criteria=previous_criteria,
                staff_feedback=staff_feedback,
            )
        )
        return refined_response.model_dump()
    except RubricResponseError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Engine refinement error: {e}")


@app.post("/api/grade-submission")
async def api_grade_submission(
    task_title: str = Form(...),
    task_type: str = Form("lab"),
    rubric_json: str = Form(...),
    spec_file: Optional[UploadFile] = File(None),
    spec_text_override: Optional[str] = Form(None),
    submission_file: Optional[UploadFile] = File(None),
    submission_text_override: Optional[str] = Form(None),
):
    """
    Grade a student submission against task spec and rubric criteria.
    """
    try:
        raw_criteria = json.loads(rubric_json)
        rubric_criteria = [RubricCriteriaItem(**item) for item in raw_criteria]
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid rubric criteria format: {e}")

    spec_text = ""
    if spec_file and spec_file.filename:
        temp_dir = tempfile.mkdtemp()
        temp_file_path = os.path.join(temp_dir, spec_file.filename)
        try:
            with open(temp_file_path, "wb") as buffer:
                shutil.copyfileobj(spec_file.file, buffer)
            spec_text = extract_text_from_file(temp_file_path)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    elif spec_text_override and spec_text_override.strip():
        spec_text = spec_text_override.strip()
    else:
        raise HTTPException(
            status_code=400,
            detail="Please upload a task specification file or paste specification text.",
        )

    sub_text = ""
    code_files_dict = {}

    if submission_file and submission_file.filename:
        temp_dir = tempfile.mkdtemp()
        temp_file_path = os.path.join(temp_dir, submission_file.filename)
        try:
            with open(temp_file_path, "wb") as buffer:
                shutil.copyfileobj(submission_file.file, buffer)
            sub_text, code_files_dict = extract_submission_content(temp_file_path)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to extract submission file '{submission_file.filename}': {e}")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    elif submission_text_override and submission_text_override.strip():
        sub_text = submission_text_override.strip()
    else:
        raise HTTPException(status_code=400, detail="Please upload a student submission file or enter submission code/text.")

    try:
        grading_response = ai_service.grade_submission(
            GradeSubmissionRequest(
                task_title=task_title,
                task_type=task_type,
                reference_text=spec_text,
                rubric_criteria=rubric_criteria,
                submission_text=sub_text,
                code_files=code_files_dict,
            )
        )
        return grading_response.model_dump()
    except GradingResponseError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Engine grading error: {e}")



@app.post("/api/student-chat")
async def api_student_chat(chat_req: StudentChatRequest):
    """
    Stateless Endpoint for General Socratic AI Guidance.
    """
    try:
        chat_resp = ai_service.socratic_chat(
            SocraticChatRequest(
                reference_text=chat_req.reference_text or "",
                chat_history=chat_req.chat_history,
                student_message=chat_req.student_message,
                task_title=chat_req.task_title,
            )
        )
        return chat_resp.model_dump()
    except ChatResponseError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Socratic Tutor error: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)


