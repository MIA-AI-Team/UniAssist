"""Real PostgreSQL/HTTP team consent, concurrency and private assessment contracts."""
import uuid
import datetime as dt
import asyncio
import asyncpg
from concurrent.futures import ThreadPoolExecutor
from test_contracts import world, ok, create_task, accept, submit, upload, PASSWORD


def detail(c, u, team, role="student"):
    return ok(c.get(f"/teams/{team}", headers=u[role]))


def action(c, u, team, action, role="student", **extra):
    version = extra.pop("expected_version", detail(c, u, team, role)["version"])
    body = dict(request_id=str(uuid.uuid4()), expected_version=version, action=action)
    body.update(extra)
    return c.post(f"/teams/{team}/actions", headers=u[role], json=body)


def create(c, u, task, role="student"):
    return ok(c.post(f"/tasks/{task}/teams", headers=u[role], json={"name":"Consent team", "request_id":str(uuid.uuid4())}), 201)["id"]


def invite(c, u, team):
    me = ok(c.get("/auth/me", headers=u["other"]))
    ok(action(c,u,team,"invite",student_number=me["student_number"]))
    return detail(c,u,team)["invitations"][0]["id"]


def reply(c,u,team,invitation,decision="accept"):
    body={"request_id":str(uuid.uuid4()),"expected_version":detail(c,u,team)["version"],"decision":decision}
    result=c.post(f"/team-invitations/{invitation}/respond",headers=u["other"],json=body)
    assert c.post(f"/team-invitations/{invitation}/respond",headers=u["other"],json=body).json()==result.json()
    return ok(result)


def approve(c,u,team):
    ok(action(c,u,team,"request_approval"))
    ok(action(c,u,team,"approve",role="teaching_assistant"))


def test_team_consent_approval_private_submission_and_lock(world):
    c,u=world
    task=create_task(c,u,type="project",require_team=True)
    accept(c,u,task)
    team=create(c,u,task)
    assert submit(c,u,task).json()["code"]=="team_not_approved"
    assert c.get(f"/teams/{team}",headers=u["other"]).status_code==404
    invitation=invite(c,u,team)
    assert c.get(f"/teams/{team}/history",headers=u["other"]).status_code==403
    assert action(c,u,team,"request_approval").json()["code"]=="team_consent_required"
    assert c.post(f"/team-invitations/{invitation}/respond",headers=u["student"],json={
        "request_id":str(uuid.uuid4()),"expected_version":2,"decision":"accept"}).status_code==404
    reply(c,u,team,invitation)
    assert action(c,u,team,"approve").status_code==403
    approve(c,u,team)
    approved=detail(c,u,team)
    assert approved["status"]=="approved" and len(approved["members"])==2
    assert action(c,u,team,"archive",expected_version=1).json()["code"]=="team_changed"
    assert c.post("/submissions/",headers=u["student"],json={"task_id":task,"team_id":team+99999,
        "submission_text":"Private answer","file_id":None}).json()["code"]=="team_forbidden"
    artifact=upload(c,u,task)
    sid=ok(submit(c,u,task,file_id=artifact),201)["submission_id"]
    attempt=ok(c.get(f"/submissions/{sid}",headers=u["student"]))
    assert attempt["team_id"]==team and attempt["team_snapshot"]["members"]==approved["members"]
    assert detail(c,u,team)["locked_at"]
    assert action(c,u,team,"archive").json()["code"]=="team_locked"
    assert action(c,u,team,"leave",role="other").json()["code"]=="team_locked"
    assert c.get(f"/submissions/{sid}",headers=u["other"]).status_code==403
    assert c.get(f"/files/{artifact}/download",headers=u["other"]).status_code==403
    other=dict(u,student=u["other"])
    other_sid=ok(submit(c,other,task),201)["submission_id"]
    ok(c.post(f"/submissions/{sid}/grade",headers=u["professor"]))
    hidden=ok(c.get(f"/submissions/{sid}",headers=u["student"]))
    assert hidden["feedback"] is None
    ok(c.patch(f"/submissions/{sid}/confirm",headers=u["professor"],json={"final_grade":22}))
    assert submit(c,u,task).json()["code"]=="grade_confirmed"
    assert ok(c.get(f"/submissions/{other_sid}",headers=u["other"]))["status"]=="pending"
    ok(submit(c,other,task),201)
    ok(c.delete(f"/tasks/{task}",headers=u["professor"]),204)
    assert c.get(f"/teams/{team}",headers=u["student"]).status_code==404


def test_team_roster_changes_reapproval_and_archiving(world):
    c,u=world
    task=create_task(c,u,type="project",require_team=True)
    team=create(c,u,task)
    invitation=invite(c,u,team)
    reply(c,u,team,invitation,"decline")
    assert not detail(c,u,team)["invitations"]
    invitation=invite(c,u,team)
    ok(action(c,u,team,"cancel_invitation",invitation_id=invitation))
    invitation=invite(c,u,team)
    reply(c,u,team,invitation)
    approve(c,u,team)
    ok(action(c,u,team,"leave",role="other"))
    assert detail(c,u,team)["status"]=="draft"
    invitation=invite(c,u,team)
    reply(c,u,team,invitation)
    approve(c,u,team)
    other=ok(c.get("/auth/me",headers=u["other"]))
    ok(action(c,u,team,"remove",student_id=other["id"]))
    assert detail(c,u,team)["status"]=="draft"
    ok(action(c,u,team,"request_approval"))
    ok(action(c,u,team,"reject",role="professor"))
    assert detail(c,u,team)["status"]=="rejected"
    ok(action(c,u,team,"archive"))
    assert detail(c,u,team)["status"]=="archived"
    assert create(c,u,task)!=team
    history=ok(c.get(f"/teams/{team}/history?limit=2",headers=u["student"]))
    assert len(history["items"])==2 and history["next_cursor"]
    assert history["items"][0]["action"]=="archive"


def test_team_concurrent_membership_and_cohort_scope(world):
    c,u=world
    task=create_task(c,u,type="project",require_team=True)
    team=create(c,u,task)
    tag=uuid.uuid4().hex
    body=dict(name="Third",email=f"{tag}@example.com",password=PASSWORD,role="student",
              student_number=tag,cohort_year=2027,major="CS")
    ok(c.post("/auth/register",json=body),201)
    token=ok(c.post("/auth/login",json={"email":body["email"],"password":PASSWORD}))["access_token"]
    third=dict(u,student={"Authorization":"Bearer "+token})
    team2=create(c,third,task)
    invitations=[invite(c,u,team),invite(c,third,team2)]
    def join(pair):
        tid,iid=pair
        return c.post(f"/team-invitations/{iid}/respond",headers=u["other"],json={
            "request_id":str(uuid.uuid4()),"expected_version":2,"decision":"accept"})
    with ThreadPoolExecutor(2) as pool:
        results=list(pool.map(join,zip([team,team2],invitations)))
    assert sorted(r.status_code for r in results)==[200,409]
    assert next(r for r in results if r.status_code==409).json()["code"]=="team_membership_exists"
    forbidden=create_task(c,u,type="project",require_team=True,target_cohort_year=2028)
    assert c.get(f"/tasks/{forbidden}/teams",headers=u["student"]).status_code==403
    assert c.post(f"/tasks/{forbidden}/teams",headers=u["student"],json={"name":"No access","request_id":str(uuid.uuid4())}).status_code==403
    individual=create_task(c,u,type="project",require_team=False)
    assert c.get(f"/tasks/{individual}/teams",headers=u["student"]).json()["code"]=="team_not_required"


def test_submission_and_removal_serialize_and_deadlines_hold(world):
    c,u=world
    task=create_task(c,u,type="project",require_team=True)
    accept(c,u,task)
    team=create(c,u,task)
    reply(c,u,team,invite(c,u,team))
    approve(c,u,team)
    member=ok(c.get("/auth/me",headers=u["other"]))
    version=detail(c,u,team)["version"]
    other=dict(u,student=u["other"])
    with ThreadPoolExecutor(2) as pool:
        saving=pool.submit(submit,c,other,task)
        removing=pool.submit(action,c,u,team,"remove",student_id=member["id"],expected_version=version)
        saved,removed=saving.result(),removing.result()
    current=detail(c,u,team)
    if saved.status_code==201:
        assert removed.json()["code"]=="team_locked" and len(current["members"])==2
        attempt=ok(c.get(f"/submissions/{saved.json()['submission_id']}",headers=u["other"]))
        assert len(attempt["team_snapshot"]["members"])==2
    else:
        assert saved.json()["code"]=="team_required" and removed.status_code==200
        assert current["locked_at"] is None and current["status"]=="draft"
    closed=create_task(c,u,type="project",require_team=True,
        due_date=(dt.datetime.now(dt.timezone.utc)-dt.timedelta(hours=1)).isoformat())
    accept(c,u,closed)
    closedteam=create(c,u,closed)
    approve(c,u,closedteam)
    assert submit(c,u,closed).json()["code"]=="deadline_passed"
    assert detail(c,u,closedteam)["locked_at"] is None


def test_legacy_rosters_stay_review_blocked_without_invented_consent(world):
    c,u=world
    task=create_task(c,u,type="project",require_team=True)
    accept(c,u,task)
    student=ok(c.get("/auth/me",headers=u["student"]))
    async def historical():
        db=await asyncpg.connect("postgresql://verify:verify-local-only@localhost:15432/verify")
        try:
            team=await db.fetchval("INSERT INTO teams(task_id,name) VALUES($1,'Legacy review') RETURNING id",task)
            await db.execute("INSERT INTO team_members(team_id,student_id,task_id) VALUES($1,$2,$3)",team,student["id"],task)
            return team
        finally:
            await db.close()
    team=asyncio.run(historical())
    info=detail(c,u,team)
    assert info["status"]=="legacy" and info["members"][0]["accepted_at"] is None
    assert not info["actions"] and info["unavailable_reason"]=="team_legacy_review"
    assert action(c,u,team,"approve",role="professor").json()["code"]=="team_legacy_review"
    assert submit(c,u,task).json()["code"]=="team_legacy_review"
    duplicate=c.post(f"/tasks/{task}/teams",headers=u["student"],json={"name":"Bypass legacy","request_id":str(uuid.uuid4())})
    assert duplicate.json()["code"]=="team_membership_exists"
