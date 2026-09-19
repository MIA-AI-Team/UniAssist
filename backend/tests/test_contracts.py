"""HTTP integration tests. Requires docker-compose.test.yml (never the user's DB)."""
import datetime as dt
import io
import os
import uuid
from concurrent.futures import ThreadPoolExecutor

import httpx
import pytest
from pypdf import PdfWriter

URL = os.getenv("TEST_API_URL", "http://localhost:18001")
PASSWORD = "Verify-password-123"

def ok(response, status=200):
    assert response.status_code == status, response.text
    return response.json() if response.content else None

@pytest.fixture()
def world():
    tag = uuid.uuid4().hex[:10]
    client = httpx.Client(base_url=URL, timeout=180)
    users = {}
    for role in ("professor", "teaching_assistant", "student", "other"):
        actual = "student" if role == "other" else role
        body = dict(name=role+" "+tag, email=f"{role}-{tag}@example.com", password=PASSWORD,
                    role=actual, staff_role=actual, department="CS",
                    student_number=role+tag, cohort_year=2027, major="CS")
        registered = ok(client.post("/auth/register", json=body), 201)
        login = ok(client.post("/auth/login", json={"email": body["email"], "password": PASSWORD}))
        users[role] = {"Authorization": "Bearer "+login["access_token"]}
        me = ok(client.get("/auth/me", headers=users[role]))
        assert me["id"] == registered["id"] and me["role"] == actual
    yield client, users
    client.close()

def create_task(client, users, **changes):
    body = dict(type="assignment", title="Integration assignment", description="Explain binary search and its complexity.",
                due_date=(dt.datetime.now(dt.timezone.utc)+dt.timedelta(days=2)).isoformat(),
                target_cohort_year=2027, target_major="CS", allowed_file_types=["txt","pdf","zip"])
    body.update(changes)
    return ok(client.post("/tasks/", headers=users["professor"], json=body), 201)["id"]

def accept(client, users, task):
    rubric = ok(client.post(f"/tasks/{task}/rubrics/create", headers=users["teaching_assistant"], json={
        "criteria":[{"name":"Reasoning","description":"Correct explanation","max_points":25,"sort_order":1}]}), 201)
    denied = client.patch(f"/tasks/{task}/rubrics/status?rubric_id={rubric['rubric_id']}",
        headers=users["teaching_assistant"],json={"status":"accepted"})
    assert denied.status_code == 403
    ok(client.patch(f"/tasks/{task}/rubrics/status?version={rubric['version']}",
        headers=users["professor"],json={"status":"accepted"}))
    return rubric

def submit(client, users, task, text="Binary search halves a sorted search interval. Complexity O(log n).", file_id=None):
    return client.post("/submissions/",headers=users["student"],
                       json={"task_id":task,"submission_text":text,"file_id":file_id,"team_id":None})

def upload(client, users, task, text=b"print('binary search')", name="answer.txt", role="student", purpose="submission"):
    return ok(client.post("/files/upload",headers=users[role],data={"purpose":purpose,"task_id":str(task)},
                          files={"file":(name,text)}),201)["file_id"]

def test_full_release_and_attempt_history(world):
    client,users=world
    task=create_task(client,users)
    assert submit(client,users,task).json()["code"]=="rubric_not_ready"
    rubric=accept(client,users,task)
    first=ok(submit(client,users,task),201)["submission_id"]
    artifact=upload(client,users,task)
    metadata=ok(client.get(f"/files/{artifact}",headers=users["student"]))
    assert "storage_path" not in metadata and metadata["size_bytes"] > 0
    assert metadata["file_name"]=="answer.txt" and metadata["purpose"]=="submission"
    second=ok(submit(client,users,task,file_id=artifact),201)["submission_id"]
    assert client.post(f"/submissions/{first}/grade",headers=users["professor"]).status_code==409
    assert submit(client,users,task,file_id=artifact).json()["code"]=="file_already_submitted"
    queue=ok(client.get(f"/tasks/{task}/submissions",headers=users["teaching_assistant"]))
    assert [s["id"] for s in queue]==[second] and queue[0]["student_name"]
    assert len(ok(client.get(f"/tasks/{task}/submissions?latest_only=false",headers=users["professor"])))==2
    detail=ok(client.get(f"/submissions/{second}",headers=users["student"]))
    assert detail["submission_text"].startswith("Binary search") and detail["artifacts"][0]["file_name"]=="answer.txt"
    # New rubric never changes the rubric attached to an existing attempt.
    accept(client,users,task)
    ok(client.post(f"/submissions/{second}/grade",headers=users["teaching_assistant"]))
    assert client.post(f"/submissions/{second}/grade",headers=users["professor"]).status_code==409
    staff=ok(client.get(f"/submissions/{second}",headers=users["professor"]))
    assert staff["rubric_id"]==rubric["rubric_id"] and staff["total_possible_grade"]==25
    assert staff["criterion_evaluations"] and staff["is_mock"] is True
    hidden=ok(client.get(f"/submissions/{second}",headers=users["student"]))
    for key in ("ai_suggested_grade","feedback","criterion_evaluations","code_reviews","ai_warnings","is_mock"):
        assert hidden[key] is None
    assert hidden["rubric_criteria"][0]["name"]=="Reasoning"
    assert hidden["rubric_id"]==rubric["rubric_id"]
    history=ok(client.get(f"/submissions/my/{task}",headers=users["student"]))
    assert all(x["ai_suggested_grade"] is None and x["feedback"] is None for x in history)
    assert client.get(f"/submissions/{second}",headers=users["other"]).status_code==403
    assert client.get(f"/files/{artifact}/download",headers=users["other"]).status_code==403
    assert client.patch(f"/submissions/{second}/confirm",headers=users["professor"],json={"final_grade":26}).status_code==400
    ok(client.patch(f"/submissions/{second}/confirm",headers=users["professor"],json={"final_grade":23}))
    released=ok(client.get(f"/submissions/{second}",headers=users["student"]))
    assert released["final_grade"]==23 and released["feedback"] and released["criterion_evaluations"]==staff["criterion_evaluations"]
    assert submit(client,users,task).json()["code"]=="grade_confirmed"
    tasks=ok(client.get("/tasks/?cohort_year=1900&major=Wrong",headers=users["student"]))
    item=next(t for t in tasks if t["id"]==task)
    assert item["latest_submission"]["final_grade"]==23
    ok(client.delete(f"/tasks/{task}",headers=users["professor"]),204)
    assert client.get(f"/submissions/{second}",headers=users["student"]).status_code==404

def test_deadlines_projects_and_authorization(world):
    client,users=world
    past=(dt.datetime.now(dt.timezone.utc)-dt.timedelta(hours=1)).isoformat()
    closed=create_task(client,users,due_date=past)
    accept(client,users,closed)
    assert submit(client,users,closed).json()["code"]=="deadline_passed"
    late=create_task(client,users,due_date=past,allow_late=True)
    accept(client,users,late)
    sid=ok(submit(client,users,late),201)["submission_id"]
    ok(client.post(f"/submissions/{sid}/grade",headers=users["professor"])) # text-only
    forbidden=create_task(client,users,target_cohort_year=2028)
    assert client.get(f"/tasks/{forbidden}",headers=users["student"]).status_code==403
    assert client.post("/files/upload",headers=users["student"],data={"purpose":"reference"},files={"file":("x.pdf",b"%PDF-")}).status_code==403
    team=create_task(client,users,type="project",require_team=True)
    accept(client,users,team)
    assert submit(client,users,team).json()["code"]=="team_required"
    individual=create_task(client,users,type="project",require_team=False)
    accept(client,users,individual)
    artifact=upload(client,users,individual)
    sid=ok(submit(client,users,individual,text="",file_id=artifact),201)["submission_id"]
    ok(client.post(f"/submissions/{sid}/grade",headers=users["professor"])) # file-only
    restricted=create_task(client,users,allowed_file_types=["pdf"])
    accept(client,users,restricted)
    artifact=upload(client,users,restricted)
    assert submit(client,users,restricted,file_id=artifact).json()["code"]=="file_type_not_allowed"


def test_student_approved_rubric_visibility(world):
    client, users = world
    task = create_task(client, users)
    def student_task():
        return ok(client.get(f"/tasks/{task}", headers=users["student"]))
    assert student_task()["accepted_rubric"] is None
    draft = ok(client.post(f"/tasks/{task}/rubrics/create", headers=users["professor"], json={
        "criteria": [{"name": "Private draft", "description": "Not approved for students", "max_points": 10}]}), 201)
    assert student_task()["accepted_rubric"] is None
    assert client.get(f"/tasks/{task}/rubrics", headers=users["student"]).status_code == 403
    approved = accept(client, users, task)
    public = student_task()["accepted_rubric"]
    assert public["id"] == approved["rubric_id"] and public["total"] == 25
    assert public["criteria"][0]["description"] == "Correct explanation"
    assert "Private draft" not in str(student_task())
    attempt = ok(submit(client, users, task), 201)["submission_id"]
    next_version = accept(client, users, task)
    assert student_task()["accepted_rubric"]["id"] == next_version["rubric_id"]
    detail = ok(client.get(f"/submissions/{attempt}", headers=users["student"]))
    assert detail["rubric_id"] == approved["rubric_id"]
    assert detail["rubric_criteria"] == public["criteria"]
    assert detail["feedback"] is None and detail["criterion_evaluations"] is None
    ok(client.patch(f"/tasks/{task}/rubrics/status?rubric_id={draft['rubric_id']}",
                    headers=users["professor"], json={"status": "rejected"}))
    assert "Private draft" not in str(student_task())
    for restriction in ({"target_cohort_year": 2028}, {"target_major": "Other"}):
        forbidden = create_task(client, users, **restriction)
        accept(client, users, forbidden)
        assert client.get(f"/tasks/{forbidden}", headers=users["student"]).status_code == 403

def test_lab_rubrics_and_concurrent_attempts(world):
    client,users=world
    writer=PdfWriter();writer.add_blank_page(width=100,height=100)
    pdf=io.BytesIO();writer.write(pdf)
    reference=ok(client.post("/files/upload",headers=users["professor"],data={"purpose":"reference"},
                             files={"file":("lab.pdf",pdf.getvalue(),"application/pdf")}),201)["file_id"]
    task=create_task(client,users,type="lab",reference_file_id=reference,
                     scheduled_date=dt.datetime.now(dt.timezone.utc).isoformat())
    assert client.get(f"/files/{reference}/download",headers=users["student"]).status_code==200
    suggestion=ok(client.post(f"/tasks/{task}/rubrics/suggest",headers=users["professor"]),201)
    refined=ok(client.post(f"/tasks/{task}/rubrics/refine?rubric_id={suggestion['rubric_id']}",
                           headers=users["teaching_assistant"],json={"staff_feedback":"Focus on reasoning"}),201)
    ok(client.patch(f"/tasks/{task}/rubrics/status?rubric_id={refined['rubric_id']}",
                    headers=users["professor"],json={"status":"accepted"}))
    assert len(ok(client.get(f"/tasks/{task}/rubrics",headers=users["professor"])))==2
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(lambda _: submit(client,users,task),range(2)))
    assert all(r.status_code in (201,409) for r in results)
    history=ok(client.get(f"/submissions/my/{task}",headers=users["student"]))
    assert sum(s["is_latest"] for s in history)==1
    latest=next(s for s in history if s["is_latest"])
    with ThreadPoolExecutor(max_workers=2) as pool:
        graded=list(pool.map(lambda _:client.post(f"/submissions/{latest['id']}/grade",headers=users["professor"]),range(2)))
    assert sorted(r.status_code for r in graded)==[200,409]
    other_task=create_task(client,users,target_major="Other")
    assert client.patch(f"/tasks/{other_task}/rubrics/status?rubric_id={refined['rubric_id']}",headers=users["professor"],json={"status":"accepted"}).status_code==422
    assert client.get(f"/tasks/{task}/submissions",headers=users["student"]).status_code==403
