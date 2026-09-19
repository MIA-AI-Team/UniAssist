"""Approved public repositories, attribution audit and immutable private archives."""
from alembic import op
import sqlalchemy as sa

revision = "f7a20260919"
down_revision = "f6a20260918"
branch_labels = depends_on = None


def upgrade():
    if op.get_bind().execute(sa.text("SELECT repository_id,commit_hash FROM commits GROUP BY repository_id,commit_hash HAVING COUNT(*)>1 LIMIT 1")).first():
        raise RuntimeError("Repository migration requires reviewed duplicate commits; no records were removed.")
    for column in [
        sa.Column("status",sa.String(24),nullable=False,server_default="legacy"),
        sa.Column("version",sa.Integer(),nullable=False,server_default="1"),
        sa.Column("full_name",sa.String(150)), sa.Column("github_id",sa.BigInteger()),
        sa.Column("created_by",sa.Integer(),sa.ForeignKey("users.id")),
        sa.Column("request_id",sa.String(36)),
        sa.Column("approved_team_version",sa.Integer()),
        sa.Column("last_synced_at",sa.DateTime(timezone=True)),
        sa.Column("sync_error",sa.String(40)),
        sa.Column("partial_history",sa.Boolean(),nullable=False,server_default=sa.true()),
        sa.Column("is_fixture",sa.Boolean(),nullable=False,server_default=sa.false()),
    ]: op.add_column("repositories",column)
    op.create_unique_constraint("uq_repository_create_request","repositories",["created_by","request_id"])
    op.create_index("uq_active_team_repository","repositories",["team_id"],unique=True,postgresql_where=sa.text("status='approved'"))
    op.create_unique_constraint("uq_repository_commit","commits",["repository_id","commit_hash"])
    op.add_column("commits",sa.Column("attributed_by",sa.Integer(),sa.ForeignKey("staff.user_id")))
    op.add_column("commits",sa.Column("attributed_at",sa.DateTime(timezone=True)))
    op.create_table("repository_events",
        sa.Column("id",sa.Integer(),primary_key=True),
        sa.Column("repository_id",sa.Integer(),sa.ForeignKey("repositories.id",ondelete="CASCADE"),nullable=False),
        sa.Column("actor_id",sa.Integer(),sa.ForeignKey("users.id"),nullable=False),
        sa.Column("request_id",sa.String(36),nullable=False),
        sa.Column("request_hash",sa.String(64),nullable=False),
        sa.Column("action",sa.String(24),nullable=False),
        sa.Column("version",sa.Integer(),nullable=False),
        sa.Column("details",sa.JSON(),nullable=False),
        sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),
        sa.UniqueConstraint("actor_id","request_id",name="uq_repository_event_request"))
    op.create_index("ix_repository_events_repository_id","repository_events",["repository_id"])
    op.create_table("repository_snapshots",
        sa.Column("id",sa.Integer(),primary_key=True),
        sa.Column("repository_id",sa.Integer(),sa.ForeignKey("repositories.id",ondelete="CASCADE"),nullable=False),
        sa.Column("owner_id",sa.Integer(),sa.ForeignKey("students.user_id"),nullable=False),
        sa.Column("request_id",sa.String(36),nullable=False),
        sa.Column("commit_sha",sa.String(40),nullable=False),
        sa.Column("archive",sa.LargeBinary(),nullable=False),
        sa.Column("provenance",sa.JSON(),nullable=False),
        sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),
        sa.UniqueConstraint("owner_id","request_id",name="uq_repository_snapshot_request"))
    op.create_index("ix_repository_snapshots_repository_id","repository_snapshots",["repository_id"])
    op.add_column("submissions",sa.Column("repository_snapshot_id",sa.Integer(),sa.ForeignKey("repository_snapshots.id",ondelete="CASCADE")))


def downgrade():
    op.drop_column("submissions","repository_snapshot_id")
    op.drop_table("repository_snapshots")
    op.drop_table("repository_events")
    op.drop_column("commits","attributed_at")
    op.drop_column("commits","attributed_by")
    op.drop_constraint("uq_repository_commit","commits",type_="unique")
    op.drop_index("uq_active_team_repository",table_name="repositories")
    op.drop_constraint("uq_repository_create_request","repositories",type_="unique")
    for name in ("status","version","full_name","github_id","created_by","request_id","approved_team_version","last_synced_at","sync_error","partial_history","is_fixture"):
        op.drop_column("repositories",name)
