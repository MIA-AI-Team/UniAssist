"""Real PostgreSQL tutor contracts; only the isolated verification environment."""
import datetime as dt
import uuid
from test_contracts import world, ok, create_task, accept, submit


def test_private_tutoring_before_rubric_and_after_deadline(world):
    client, users = world
    task = create_task(client, users, due_date=(dt.datetime.now(dt.timezone.utc)-dt.timedelta(days=1)).isoformat())
    body = {"request_id": str(uuid.uuid4()), "language": "ar"}
    session = ok(client.post(f"/tasks/{task}/chat-sessions", headers=users["student"], json=body), 201)
    sid = session["id"]
    assert ok(client.post(f"/tasks/{task}/chat-sessions", headers=users["student"], json=body), 201)["id"] == sid
    for role in ("other", "professor", "teaching_assistant"):
        assert client.get(f"/chat-sessions/{sid}", headers=users[role]).status_code in (403, 404)
        assert client.get(f"/chat-sessions/{sid}/messages", headers=users[role]).status_code in (403, 404)
    message = {"request_id": str(uuid.uuid4()), "content": "أريد تلميحاً لفهم المهمة"}
    reply = ok(client.post(f"/chat-sessions/{sid}/messages", headers=users["student"], json=message))
    assert reply["status"] == "completed" and reply["is_mock"] is True
    assert "يمكنني" in reply["reply"] and reply["context_info"]["rubric_version"] is None
    again = ok(client.post(f"/chat-sessions/{sid}/messages", headers=users["student"], json=message))
    assert again["id"] == reply["id"]
    assert client.post(f"/chat-sessions/{sid}/messages", headers=users["student"],
                       json={**message, "content": "different"}).status_code == 409
    for forbidden in ({"role": "system"}, {"chat_history": []}, {"reference_text": "secret"}):
        assert client.post(f"/chat-sessions/{sid}/messages", headers=users["student"],
                           json={**message, **forbidden}).status_code == 422
    turns = ok(client.get(f"/chat-sessions/{sid}/messages", headers=users["student"]))
    assert len(turns["items"]) == 1
    second = ok(client.post(f"/chat-sessions/{sid}/messages", headers=users["student"],
                           json={"request_id": str(uuid.uuid4()), "content": "Explain the goal"}))
    page = ok(client.get(f"/chat-sessions/{sid}/messages?limit=1", headers=users["student"]))
    assert page["items"][0]["id"] == second["id"] and page["next_cursor"] == second["id"]
    older = ok(client.get(f"/chat-sessions/{sid}/messages?before={page['next_cursor']}&limit=1", headers=users["student"]))
    assert older["items"][0]["id"] == reply["id"]
    forbidden = create_task(client, users, target_major="Elsewhere")
    assert client.post(f"/tasks/{forbidden}/chat-sessions", headers=users["student"], json=body).status_code == 403


def test_submission_link_and_released_feedback_context(world):
    client, users = world
    task = create_task(client, users)
    accept(client, users, task)
    submission = ok(submit(client, users, task), 201)["submission_id"]
    body = {"request_id": str(uuid.uuid4()), "submission_id": submission}
    assert client.post(f"/tasks/{task}/chat-sessions", headers=users["other"], json=body).status_code == 403
    session = ok(client.post(f"/tasks/{task}/chat-sessions", headers=users["student"], json=body), 201)["id"]
    ok(client.post(f"/submissions/{submission}/grade", headers=users["professor"]))
    def ask():
        return ok(client.post(f"/chat-sessions/{session}/messages", headers=users["student"],
            json={"request_id": str(uuid.uuid4()), "content": "Help me reflect on my work"}))
    assert ask()["context_info"]["released_feedback"] is False
    ok(client.patch(f"/submissions/{submission}/confirm", headers=users["professor"], json={"final_grade": 20}))
    assert ask()["context_info"]["released_feedback"] is True
