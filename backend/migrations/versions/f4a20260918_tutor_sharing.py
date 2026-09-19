"""Explicit tutor snapshot consent, lab settings and safe provenance."""
from alembic import op
import sqlalchemy as sa

revision = "f4a20260918"
down_revision = "f3a20260918"
branch_labels = depends_on = None


def upgrade():
    op.add_column("chat_turns", sa.Column("ai_metadata", sa.JSON()))
    op.create_table("chat_shares",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("session_id", sa.Integer(), sa.ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("recipient_id", sa.Integer(), sa.ForeignKey("staff.user_id"), nullable=False),
        sa.Column("request_id", sa.String(36), nullable=False),
        sa.Column("through_turn_id", sa.Integer(), nullable=False),
        sa.Column("snapshot", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("session_id", "request_id", name="uq_chat_share_request"))
    op.create_index("ix_chat_shares_session_id", "chat_shares", ["session_id"])
    op.create_index("ix_chat_shares_recipient_id", "chat_shares", ["recipient_id"])
    op.create_table("task_tutor_settings",
        sa.Column("task_id", sa.Integer(), sa.ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("lab_mode", sa.String(16), nullable=False),
        sa.Column("updated_by", sa.Integer(), sa.ForeignKey("staff.user_id"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False))


def downgrade():
    op.drop_table("task_tutor_settings")
    op.drop_table("chat_shares")
    op.drop_column("chat_turns", "ai_metadata")
