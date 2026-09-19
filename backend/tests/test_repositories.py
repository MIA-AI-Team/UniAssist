"""Real backend/PostgreSQL, opt-in GitHub fixtures, never real external repositories."""
import hashlib
import uuid
from concurrent.futures import ThreadPoolExecutor
from test_contracts import world,ok,create_task,accept,submit,upload
from test_teams import create,approve,invite,reply,action


def repo_action(c,u,rid,action,role="teaching_assistant",**extra):
    version=ok(c.get(f"/repositories/{rid}",headers=u[role]))["version"]
    body=dict(request_id=str(uuid.uuid4()),expected_version=version,action=action)
    body.update(extra)
    return c.post(f"/repositories/{rid}/actions",headers=u[role],json=body)


def proposal(c,u,team,name="demo"):
    body={"request_id":str(uuid.uuid4()),"repo_url":"https://github.com/uniassist-fixtures/"+name}
    response=ok(c.post(f"/teams/{team}/repositories",headers=u["student"],json=body),201)
    assert ok(c.post(f"/teams/{team}/repositories",headers=u["student"],json=body),201)["id"]==response["id"]
    return response["id"]


def capture(c,u,rid):
    body={"request_id":str(uuid.uuid4()),"commit_sha":"a"*40}
    result=ok(c.post(f"/repositories/{rid}/snapshots",headers=u["student"],json=body),201)
    assert ok(c.post(f"/repositories/{rid}/snapshots",headers=u["student"],json=body),201)==result
    return result


def test_repository_lifecycle_private_snapshot_and_offline_grading(world):
    c,u=world
    task=create_task(c,u,type="project",require_team=True)
    accept(c,u,task)
    team=create(c,u,task)
    reply(c,u,team,invite(c,u,team))
    approve(c,u,team)
    rid=proposal(c,u,team)
    assert repo_action(c,u,rid,"approve",role="student").status_code==403
    assert c.post(f"/repositories/{rid}/snapshots",headers=u["student"],json={"request_id":str(uuid.uuid4()),"commit_sha":"a"*40}).json()["code"]=="repository_not_approved"
    ok(repo_action(c,u,rid,"approve"))
    ok(repo_action(c,u,rid,"sync",role="student"))
    commits=ok(c.get(f"/repositories/{rid}/commits",headers=u["student"]))["items"]
    assert len(commits)==1 and commits[0]["student_id"] is None and commits[0]["attributed_at"] is None
    ok(repo_action(c,u,rid,"sync"))
    assert len(ok(c.get(f"/repositories/{rid}/commits",headers=u["student"]))["items"])==1
    student=ok(c.get("/auth/me",headers=u["student"]))
    ok(repo_action(c,u,rid,"attribute",commit_id=commits[0]["id"],student_id=student["id"]))
    snapshot=capture(c,u,rid)
    assert snapshot["provenance"]["is_fixture"] and snapshot["provenance"]["attribution"][0]["student_id"]==student["id"]
    archive=c.get(f"/repository-snapshots/{snapshot['id']}/download",headers=u["student"])
    assert archive.status_code==200 and hashlib.sha256(archive.content).hexdigest()==snapshot["provenance"]["archive_sha256"]
    assert c.get(f"/repository-snapshots/{snapshot['id']}",headers=u["other"]).status_code==403
    assert c.get(f"/repository-snapshots/{snapshot['id']}/download",headers=u["other"]).status_code==403
    file=upload(c,u,task)
    body={"task_id":task,"submission_text":"Individual explanation","repository_snapshot_id":snapshot["id"]}
    conflict=c.post("/submissions/",headers=u["student"],json={**body,"file_id":file})
    assert conflict.json()["code"]=="repository_artifact_conflict"
    sid=ok(c.post("/submissions/",headers=u["student"],json=body),201)["submission_id"]
    # Correction cannot rewrite attribution captured on a submitted snapshot.
    ok(repo_action(c,u,rid,"attribute",commit_id=commits[0]["id"],student_id=None))
    detail=ok(c.get(f"/submissions/{sid}",headers=u["student"]))
    assert detail["repository_snapshot"]==snapshot and detail["team_snapshot"]
    ok(c.post(f"/submissions/{sid}/grade",headers=u["teaching_assistant"]))
    hidden=ok(c.get(f"/submissions/{sid}",headers=u["student"]))
    assert hidden["code_reviews"] is None and hidden["feedback"] is None
    staff=ok(c.get(f"/submissions/{sid}",headers=u["professor"]))
    assert any("Repository commit:" in w for w in staff["ai_warnings"])
    ok(c.patch(f"/submissions/{sid}/confirm",headers=u["professor"],json={"final_grade":20}))
    assert ok(c.get(f"/submissions/{sid}",headers=u["student"]))["repository_snapshot"]==snapshot
    assert c.get(f"/submissions/{sid}",headers=u["other"]).status_code==403
    # Task deletion must still cascade through academic records without breaking constraints.
    ok(c.delete(f"/tasks/{task}",headers=u["professor"]),204)
    assert c.get(f"/repository-snapshots/{snapshot['id']}",headers=u["student"]).status_code==404


def test_repository_reapproval_and_membership_scope(world):
    c,u=world
    task=create_task(c,u,type="project",require_team=True)
    accept(c,u,task)
    team=create(c,u,task)
    approve(c,u,team)
    rid=proposal(c,u,team)
    assert c.get(f"/repositories/{rid}",headers=u["other"]).status_code==404
    ok(repo_action(c,u,rid,"approve"))
    old=capture(c,u,rid)
    invitation=invite(c,u,team)
    assert c.get(f"/repositories/{rid}",headers=u["other"]).status_code==404 # invitee is not a member
    reply(c,u,team,invitation)
    approve(c,u,team)
    result=c.post("/submissions/",headers=u["student"],json={"task_id":task,"repository_snapshot_id":old["id"]})
    assert result.json()["code"]=="repository_not_approved"
    ok(repo_action(c,u,rid,"approve",role="professor"))
    result=c.post("/submissions/",headers=u["student"],json={"task_id":task,"repository_snapshot_id":old["id"]})
    assert result.json()["code"]=="repository_changed"
    new=capture(c,u,rid)
    assert new["provenance"]["team_version"]>old["provenance"]["team_version"]
    wrong=create_task(c,u,type="project",require_team=False)
    accept(c,u,wrong)
    assert c.post("/submissions/",headers=u["student"],json={"task_id":wrong,"repository_snapshot_id":new["id"]}).json()["code"]=="team_forbidden"
    # File/text fallback does not depend on GitHub or an approved repository.
    ok(submit(c,u,task),201)
