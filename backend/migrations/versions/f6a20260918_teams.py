"""Consented teams, versioned approvals and individual roster snapshots."""
from alembic import op
import sqlalchemy as sa

revision = "f6a20260918"
down_revision = "f5a20260918"
branch_labels = depends_on = None


def upgrade():
    # Do not delete or choose between ambiguous historical memberships.
    conflicts = op.get_bind().execute(sa.text("""SELECT t.task_id, m.student_id FROM team_members m
        JOIN teams t ON t.id=m.team_id GROUP BY t.task_id,m.student_id HAVING COUNT(*)>1 LIMIT 1""")).first()
    if conflicts:
        raise RuntimeError("Team migration requires reviewed duplicate task/student memberships; no records were removed.")
    op.add_column("teams", sa.Column("created_by", sa.Integer(), sa.ForeignKey("students.user_id")))
    op.add_column("teams", sa.Column("request_id", sa.String(36)))
    op.add_column("teams", sa.Column("status", sa.String(24), server_default="legacy", nullable=False))
    op.add_column("teams", sa.Column("version", sa.Integer(), server_default="1", nullable=False))
    op.add_column("teams", sa.Column("approved_roster", sa.JSON()))
    op.add_column("teams", sa.Column("locked_at", sa.DateTime(timezone=True)))
    op.create_unique_constraint("uq_team_create_request", "teams", ["created_by", "request_id"])
    op.add_column("team_members", sa.Column("task_id", sa.Integer(), sa.ForeignKey("tasks.id", ondelete="CASCADE")))
    op.execute("UPDATE team_members m SET task_id=t.task_id FROM teams t WHERE m.team_id=t.id")
    op.alter_column("team_members", "task_id", nullable=False)
    op.add_column("team_members", sa.Column("active", sa.Boolean(), server_default=sa.true(), nullable=False))
    op.add_column("team_members", sa.Column("accepted_at", sa.DateTime(timezone=True)))
    op.create_index("uq_active_task_membership", "team_members", ["task_id", "student_id"], unique=True, postgresql_where=sa.text("active"))
    op.execute("""UPDATE teams t SET locked_at=s.first_submission FROM
        (SELECT team_id,MIN(submitted_at) AS first_submission FROM submissions WHERE team_id IS NOT NULL GROUP BY team_id) s
        WHERE t.id=s.team_id""")
    op.add_column("submissions", sa.Column("team_snapshot", sa.JSON()))
    op.create_table("team_invitations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("team_id", sa.Integer(), sa.ForeignKey("teams.id", ondelete="CASCADE"), nullable=False),
        sa.Column("student_id", sa.Integer(), sa.ForeignKey("students.user_id"), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("responded_at", sa.DateTime(timezone=True)))
    op.create_index("ix_team_invitations_team_id", "team_invitations", ["team_id"])
    op.create_index("ix_team_invitations_student_id", "team_invitations", ["student_id"])
    op.create_index("uq_pending_team_invitation", "team_invitations", ["team_id", "student_id"], unique=True,
                    postgresql_where=sa.text("status = 'pending'"))
    op.create_table("team_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("team_id", sa.Integer(), sa.ForeignKey("teams.id", ondelete="CASCADE"), nullable=False),
        sa.Column("actor_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("request_id", sa.String(36), nullable=False),
        sa.Column("request_hash", sa.String(64), nullable=False),
        sa.Column("action", sa.String(24), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("roster", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("actor_id", "request_id", name="uq_team_event_request"))
    op.create_index("ix_team_events_team_id", "team_events", ["team_id"])


def downgrade():
    op.drop_table("team_events")
    op.drop_table("team_invitations")
    op.drop_column("submissions", "team_snapshot")
    op.drop_index("uq_active_task_membership", table_name="team_members")
    for column in ("accepted_at", "active", "task_id"):
        op.drop_column("team_members", column)
    op.drop_constraint("uq_team_create_request", "teams", type_="unique")
    for column in ("locked_at", "approved_roster", "version", "status", "request_id", "created_by"):
        op.drop_column("teams", column)
