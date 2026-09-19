"""Persistent task tutoring, deduplication and retry leases; preserves old chats."""
from alembic import op
import sqlalchemy as sa

revision = "f3a20260918"
down_revision = "f2a20260918"
branch_labels = depends_on = None


def upgrade():
    op.add_column("chat_sessions", sa.Column("request_id", sa.String(36), nullable=True))
    op.add_column("chat_sessions", sa.Column("language", sa.String(2), nullable=False, server_default="en"))
    op.create_unique_constraint("uq_chat_session_request", "chat_sessions", ["user_id", "request_id"])
    op.create_table("chat_turns",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("session_id", sa.Integer(), sa.ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("request_id", sa.String(36), nullable=False),
        sa.Column("user_message_id", sa.Integer(), sa.ForeignKey("chat_messages.id", ondelete="CASCADE"), nullable=False),
        sa.Column("assistant_message_id", sa.Integer(), sa.ForeignKey("chat_messages.id", ondelete="SET NULL")),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column("generation", sa.String(36), nullable=False),
        sa.Column("lease_until", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("error_code", sa.String(64)),
        sa.Column("is_mock", sa.Boolean()),
        sa.Column("context_info", sa.JSON()),
        sa.UniqueConstraint("session_id", "request_id", name="uq_chat_turn_request"))
    op.create_index("ix_chat_turns_session_id", "chat_turns", ["session_id"])


def downgrade():
    op.drop_table("chat_turns")
    op.drop_constraint("uq_chat_session_request", "chat_sessions", type_="unique")
    op.drop_column("chat_sessions", "language")
    op.drop_column("chat_sessions", "request_id")
