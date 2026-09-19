"""Creates its own PostgreSQL database; never drops or recreates user data."""
import asyncio
import os
from pathlib import Path
import subprocess
import sys
import uuid
import asyncpg
import pytest

ROOT = Path(__file__).resolve().parents[2]

@pytest.mark.parametrize("duplicate_kind", [None, "membership", "commit"])
def test_old_head_upgrade_preserves_records(duplicate_kind):
    database = "verify_migration_" + uuid.uuid4().hex[:12]
    async def create():
        connection = await asyncpg.connect("postgresql://verify:verify-local-only@localhost:15432/verify")
        await connection.execute(f'CREATE DATABASE "{database}"')
        await connection.close()
    asyncio.run(create())
    env = dict(os.environ, DATABASE_URL=f"postgresql+asyncpg://verify:verify-local-only@localhost:15432/{database}",
               PYTHONPATH=str(ROOT/"backend"), SECRET_KEY="migration-test-only")
    def migrate(revision):
        subprocess.run([sys.executable,"-m","alembic","upgrade",revision],cwd=ROOT/"backend",env=env,check=True,capture_output=True,text=True)
    migrate("e49cd157b008")
    async def seed():
        connection=await asyncpg.connect(f"postgresql://verify:verify-local-only@localhost:15432/{database}")
        await connection.execute("""
        INSERT INTO users(id,name,email,password_hash,role) VALUES(1,'Historical professor','historical@example.com','not-a-login','professor'),(2,'Historical student','student@example.com','not-a-login','student');
        INSERT INTO staff(user_id,staff_role,department) VALUES(1,'professor','CS');
        INSERT INTO students(user_id,student_number,cohort_year,major) VALUES(2,'OLD001',2027,'CS');
        INSERT INTO tasks(id,type,title,description,due_date,target_cohort_year,created_by) VALUES(1,'assignment','History','Keep this record',NOW(),2027,1);
        INSERT INTO rubrics(id,task_id,version,source,status,created_at) VALUES(1,1,1,'staff_created','accepted',NOW());
        INSERT INTO rubric_criteria(id,rubric_id,name,description,max_points,sort_order) VALUES(1,1,'Correctness','Historical rubric',25,1);
        INSERT INTO submissions(id,task_id,student_id,rubric_id,attempt_number,is_latest,submitted_at,status,final_grade,feedback) VALUES(1,1,2,1,1,true,NOW(),'staff_confirmed',23,'Historical feedback');
        INSERT INTO teams(id,task_id,name) VALUES(1,1,'Historical team');
        INSERT INTO team_members(team_id,student_id) VALUES(1,2);
        UPDATE submissions SET team_id=1 WHERE id=1;
        INSERT INTO repositories(id,task_id,team_id,repo_url,provider) VALUES(1,1,1,'https://github.com/historical/project','github');
        INSERT INTO commits(id,repository_id,student_id,commit_hash,author_name,author_github_username,message,committed_at) VALUES(1,1,2,'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa','Historical author','old-author','Preserve this commit',NOW());
        INSERT INTO files(id,owner_id,task_id,submission_id,purpose,file_type,storage_path,uploaded_at) VALUES(1,2,1,1,'submission','txt','uploads/historical.txt',NOW());
        INSERT INTO chat_sessions(id,user_id,task_id,title,created_at,updated_at) VALUES(1,2,1,'Historical conversation',NOW(),NOW());
        INSERT INTO chat_messages(id,session_id,sender_type,content,created_at) VALUES(1,1,'user','Historical question',NOW()),(2,1,'assistant','Historical hint',NOW());
        """)
        await connection.close()
    asyncio.run(seed())
    if duplicate_kind:
        old_head="f5a20260918" if duplicate_kind=="membership" else "f6a20260918"
        migrate(old_head)
        async def duplicate():
            connection=await asyncpg.connect(f"postgresql://verify:verify-local-only@localhost:15432/{database}")
            if duplicate_kind=="membership":
                await connection.execute("INSERT INTO teams(id,task_id,name) VALUES(2,1,'Ambiguous legacy team'); INSERT INTO team_members(team_id,student_id) VALUES(2,2)")
            else:
                await connection.execute("INSERT INTO commits(id,repository_id,student_id,commit_hash,author_name,author_github_username,message,committed_at) SELECT 2,repository_id,student_id,commit_hash,author_name,author_github_username,'Duplicate history',committed_at FROM commits WHERE id=1")
            await connection.close()
        asyncio.run(duplicate())
        with pytest.raises(subprocess.CalledProcessError) as failed:
            migrate("head")
        assert "reviewed duplicate" in failed.value.stderr
        async def preserved():
            connection=await asyncpg.connect(f"postgresql://verify:verify-local-only@localhost:15432/{database}")
            table="team_members" if duplicate_kind=="membership" else "commits"
            assert await connection.fetchval(f"SELECT COUNT(*) FROM {table}")==2
            assert await connection.fetchval("SELECT version_num FROM alembic_version")==old_head
            assert await connection.fetchval("SELECT feedback FROM submissions WHERE id=1")=="Historical feedback"
            await connection.close()
        asyncio.run(preserved())
        return
    migrate("head")
    migrate("head") # idempotent restart
    async def verify():
        connection=await asyncpg.connect(f"postgresql://verify:verify-local-only@localhost:15432/{database}")
        row=await connection.fetchrow("SELECT * FROM submissions WHERE id=1")
        assert row["feedback"]=="Historical feedback" and row["final_grade"]==23
        assert row["submission_text"]=="" and row["criterion_evaluations"] is None and row["is_mock"] is None
        assert await connection.fetchval("SELECT original_filename FROM files WHERE id=1") is None
        assert await connection.fetchval("SELECT language FROM chat_sessions WHERE id=1") == "en"
        assert await connection.fetchval("SELECT request_id FROM chat_sessions WHERE id=1") is None
        assert await connection.fetchval("SELECT content FROM chat_messages WHERE id=2") == "Historical hint"
        assert await connection.fetchval("SELECT COUNT(*) FROM chat_turns") == 0
        assert row["grading_guidance_id"] is None
        assert row["team_snapshot"] is None
        team=await connection.fetchrow("SELECT * FROM teams WHERE id=1")
        assert team["status"]=="legacy" and team["approved_roster"] is None and team["created_by"] is None
        assert team["locked_at"]==row["submitted_at"]
        member=await connection.fetchrow("SELECT * FROM team_members WHERE team_id=1")
        assert member["active"] and member["task_id"]==1 and member["accepted_at"] is None
        assert await connection.fetchval("SELECT COUNT(*) FROM team_events")==0
        assert row["repository_snapshot_id"] is None
        assert await connection.fetchval("SELECT status FROM repositories WHERE id=1")=="legacy"
        assert await connection.fetchval("SELECT full_name FROM repositories WHERE id=1") is None
        assert await connection.fetchval("SELECT attributed_by FROM commits WHERE id=1") is None
        assert await connection.fetchval("SELECT student_id FROM commits WHERE id=1")==2
        assert await connection.fetchval("SELECT COUNT(*) FROM repository_snapshots")==0
        assert await connection.fetchval("SELECT version_num FROM alembic_version")=="f8a20260919"
        assert await connection.fetchval("SELECT bool_and(is_active) FROM users") is True
        assert await connection.fetchval("SELECT COUNT(*) FROM audit_events")==0
        assert await connection.fetchval("SELECT COUNT(*) FROM ai_operations")==0
        await connection.close()
    asyncio.run(verify())
