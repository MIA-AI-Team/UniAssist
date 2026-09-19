"""Real HTTP/PostgreSQL coverage of private guidance and released-only insights."""
import uuid
from test_contracts import world, ok, create_task, accept, submit, PASSWORD


def extra_student(client, tag):
    email = f"insights-{tag}@example.com"
    ok(client.post("/auth/register", json={"name": "Student " + tag, "email": email,
        "password": PASSWORD, "role": "student", "student_number": tag, "cohort_year": 2027, "major": "CS"}), 201)
    login = ok(client.post("/auth/login", json={"email": email, "password": PASSWORD}))
    return {"Authorization": "Bearer " + login["access_token"]}


def test_private_guidance_is_versioned_pinned_and_hidden(world):
    client, users = world
    task = create_task(client, users)
    accept(client, users, task)
    url = f"/tasks/{task}/grading-guidance"
    body = {"request_id": str(uuid.uuid4()), "content": "PRIVATE_GRADING_SENTINEL"}
    for method in (client.get, client.post):
        assert method(url, headers=users["student"]).status_code == 403
    v1 = ok(client.post(url, headers=users["teaching_assistant"], json=body), 201)
    assert ok(client.post(url, headers=users["teaching_assistant"], json=body), 201)["id"] == v1["id"]
    assert client.post(url, headers=users["teaching_assistant"], json={**body, "content": "changed"}).status_code == 409
    sid = ok(submit(client, users, task), 201)["submission_id"]
    ok(client.post(f"/submissions/{sid}/grade", headers=users["professor"]))
    v2 = ok(client.post(url, headers=users["professor"], json={"request_id": str(uuid.uuid4()), "content": "NEW_PRIVATE_KEY"}), 201)
    assert v2["version"] == 2
    staff = ok(client.get(f"/submissions/{sid}", headers=users["professor"]))
    assert staff["grading_guidance_id"] == v1["id"] and staff["grading_guidance_version"] == 1
    assert client.get(f"{url}/{v1['id']}", headers=users["student"]).status_code == 403
    other_task = create_task(client, users)
    assert client.get(f"/tasks/{other_task}/grading-guidance/{v1['id']}", headers=users["professor"]).status_code == 404
    for released in (False, True):
        if released:
            ok(client.patch(f"/submissions/{sid}/confirm", headers=users["professor"], json={"final_grade": 20}))
        student = ok(client.get(f"/submissions/{sid}", headers=users["student"]))
        assert student["grading_guidance_id"] is None and student["grading_guidance_version"] is None
        assert "PRIVATE_GRADING_SENTINEL" not in str(student)
    first_page = ok(client.get(url + "?limit=1", headers=users["professor"]))
    assert first_page["items"][0]["id"] == v2["id"]
    older = ok(client.get(url + f"?limit=1&before={first_page['next_cursor']}", headers=users["professor"]))
    assert older["items"][0]["content"] == body["content"]
    empty = ok(client.post(url, headers=users["professor"], json={"request_id": str(uuid.uuid4()), "content": ""}), 201)
    other_users = {**users, "student": users["other"]}
    sid2 = ok(submit(client, other_users, task), 201)["submission_id"]
    ok(client.post(f"/submissions/{sid2}/grade", headers=users["professor"]))
    assert ok(client.get(f"/submissions/{sid2}", headers=users["professor"]))["grading_guidance_id"] == empty["id"]
    ok(client.delete(f"/tasks/{task}", headers=users["professor"]), 204)


def test_insights_threshold_rubric_groups_release_staleness_and_language(world):
    client, users = world
    task = create_task(client, users)
    rubric = accept(client, users, task)
    path = f"/tasks/{task}/analytics"
    body = {"request_id": str(uuid.uuid4()), "rubric_id": rubric["rubric_id"], "language": "en"}
    assert client.get(path, headers=users["student"]).status_code == 403
    assert client.get(path + "/reports", headers=users["student"]).status_code == 403
    assert client.post(path + "/reports", headers=users["student"], json=body).status_code == 403
    assert ok(client.get(path, headers=users["professor"]))["released_count"] == 0
    students = [users["student"], users["other"], extra_student(client, uuid.uuid4().hex[:10])]
    for index, student in enumerate(students):
        sid = ok(submit(client, {**users, "student": student}, task), 201)["submission_id"]
        ok(client.post(f"/submissions/{sid}/grade", headers=users["professor"]))
        assert ok(client.get(path, headers=users["professor"]))["released_count"] == index
        assert client.post(path + "/reports", headers=users["professor"], json=body).json()["code"] == "analytics_insufficient"
        ok(client.patch(f"/submissions/{sid}/confirm", headers=users["professor"], json={"final_grade": [10, 20, 25][index]}))
        if index == 0:
            small = ok(client.get(path, headers=users["professor"]))["groups"][0]
            assert small["average_percentage"] is None and small["criteria"][0]["average_score"] is None
    snapshot = ok(client.get(path, headers=users["teaching_assistant"]))
    group = snapshot["groups"][0]
    assert snapshot["released_count"] == 3 and group["eligible"]
    assert group["average_percentage"] == 73.33 and group["below_half_count"] == 1
    assert group["mock_assessment_count"] == 3 and group["criteria"][0]["sample_count"] == 3
    report = ok(client.post(path + "/reports", headers=users["teaching_assistant"], json=body), 201)
    assert report["is_mock"] and not report["stale"] and report["ai_metadata"]["latency_ms"] >= 0
    assert report["input_snapshot"]["student_count"] == 3
    assert ok(client.post(path + "/reports", headers=users["teaching_assistant"], json=body), 201)["id"] == report["id"]
    arabic = ok(client.post(path + "/reports", headers=users["professor"], json={**body, "request_id": str(uuid.uuid4()), "language": "ar"}), 201)
    assert "تقرير تجريبي" in arabic["result"]["summary"]
    # A new rubric remains a separate below-threshold group; it never inflates the old group.
    second = accept(client, users, task)
    newcomer = extra_student(client, uuid.uuid4().hex[:10])
    sid = ok(submit(client, {**users, "student": newcomer}, task), 201)["submission_id"]
    ok(client.post(f"/submissions/{sid}/grade", headers=users["professor"]))
    assert not ok(client.get(path + "/reports", headers=users["professor"]))["items"][0]["stale"]
    ok(client.patch(f"/submissions/{sid}/confirm", headers=users["professor"], json={"final_grade": 15}))
    current = ok(client.get(path, headers=users["professor"]))
    assert [g["student_count"] for g in current["groups"]] == [3, 1]
    assert current["groups"][1]["rubric_id"] == second["rubric_id"] and not current["groups"][1]["eligible"]
    reports = ok(client.get(path + "/reports?limit=1", headers=users["professor"]))
    assert reports["items"][0]["stale"] and reports["items"][0]["input_snapshot"]["student_count"] == 3
    assert reports["next_cursor"]
    ok(client.delete(f"/tasks/{task}", headers=users["professor"]), 204)
