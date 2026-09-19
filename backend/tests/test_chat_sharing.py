"""Explicit consent snapshots and teaching settings against the isolated real API."""
import datetime as dt
import io
import uuid
from pypdf import PdfWriter
from test_contracts import world, ok, create_task


def test_sharing_is_recipient_only_immutable_and_revocable(world):
    client, users = world
    task = create_task(client, users)
    sid = ok(client.post(f"/tasks/{task}/chat-sessions", headers=users["student"],
                         json={"request_id": str(uuid.uuid4())}), 201)["id"]
    def ask(content):
        return ok(client.post(f"/chat-sessions/{sid}/messages", headers=users["student"],
                              json={"request_id": str(uuid.uuid4()), "content": content}))
    first = ask("Shared question")
    assert first["ai_metadata"]["latency_ms"] >= 0
    preview_url = f"/chat-sessions/{sid}/share-preview?through_turn_id={first['id']}"
    preview = ok(client.get(preview_url, headers=users["student"]))
    assert [x["id"] for x in preview] == [first["id"]]
    recipient = ok(client.get("/auth/me", headers=users["professor"]))["email"]
    body = {"request_id": str(uuid.uuid4()), "recipient_email": recipient,
            "through_turn_id": first["id"], "preview_turn_ids": [first["id"]]}
    url = f"/chat-sessions/{sid}/shares"
    assert client.post(url, headers=users["student"], json={**body, "preview_turn_ids": [999999]}).status_code == 409
    assert client.post(url, headers=users["student"], json={**body, "recipient_email": "missing@example.com"}).status_code == 404
    share = ok(client.post(url, headers=users["student"], json=body), 201)
    assert ok(client.post(url, headers=users["student"], json=body), 201)["id"] == share["id"]
    for role in ("other", "professor", "teaching_assistant"):
        assert client.get(preview_url, headers=users[role]).status_code in (403, 404)
        assert client.get(f"/chat-sessions/{sid}/messages", headers=users[role]).status_code in (403, 404)
    path = f"/chat-shares/{share['id']}"
    for role in ("other", "student", "teaching_assistant"):
        assert client.get(path, headers=users[role]).status_code in (403, 404)
    ask("PRIVATE_LATER_QUESTION")
    snapshot = ok(client.get(path, headers=users["professor"]))
    assert snapshot["snapshot"] == preview and "PRIVATE_LATER_QUESTION" not in str(snapshot)
    assert len(ok(client.get("/chat-shares", headers=users["professor"]))["items"]) == 1
    assert client.delete(path, headers=users["other"]).status_code in (403, 404)
    ok(client.delete(path, headers=users["student"]), 204)
    ok(client.delete(path, headers=users["student"]), 204)
    assert client.get(path, headers=users["professor"]).status_code == 404
    assert ok(client.get("/chat-shares", headers=users["professor"]))["items"] == []
    assert ok(client.get(url, headers=users["student"]))["items"][0]["revoked_at"]
    assert ok(client.post(url, headers=users["student"], json=body), 201)["revoked_at"]
    # Academic deletion must still work with settings, conversations and shares present.
    ok(client.delete(f"/tasks/{task}", headers=users["professor"]), 204)
    assert client.get(path, headers=users["professor"]).status_code == 404


def test_staff_lab_settings_control_future_turns(world):
    client, users = world
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    pdf = io.BytesIO()
    writer.write(pdf)
    reference = ok(client.post("/files/upload", headers=users["professor"], data={"purpose": "reference"},
        files={"file": ("lab.pdf", pdf.getvalue(), "application/pdf")}), 201)["file_id"]
    task = create_task(client, users, type="lab", reference_file_id=reference,
                       scheduled_date=dt.datetime.now(dt.timezone.utc).isoformat())
    path = f"/tasks/{task}/tutor-settings"
    assert ok(client.get(path, headers=users["professor"]))["lab_mode"] == "experiment"
    for method in (client.get, client.patch):
        assert method(path, headers=users["student"]).status_code == 403
    assert client.patch(path, headers=users["professor"], json={"lab_mode": "answer"}).status_code == 422
    ok(client.patch(path, headers=users["teaching_assistant"], json={"lab_mode": "coding"}))
    sid = ok(client.post(f"/tasks/{task}/chat-sessions", headers=users["student"],
                         json={"request_id": str(uuid.uuid4())}), 201)["id"]
    reply = ok(client.post(f"/chat-sessions/{sid}/messages", headers=users["student"],
        json={"request_id": str(uuid.uuid4()), "content": "Help me debug my loop"}))
    assert reply["context_info"]["lab_mode"] == "coding" and reply["is_mock"]
    assignment = create_task(client, users)
    assert client.get(f"/tasks/{assignment}/tutor-settings", headers=users["professor"]).status_code == 422
    ok(client.delete(f"/tasks/{task}", headers=users["professor"]), 204)
