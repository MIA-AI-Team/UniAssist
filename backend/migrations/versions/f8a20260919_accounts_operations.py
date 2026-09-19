"""Account status and content-free durable operational history."""
from alembic import op
import sqlalchemy as sa

revision = "f8a20260919"
down_revision = "f7a20260919"
branch_labels = depends_on = None


def upgrade():
    op.add_column("users", sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column("users", sa.Column("profile_version", sa.Integer(), nullable=False, server_default="1"))
    op.create_table("audit_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("actor_id", sa.Integer()),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("target_type", sa.String(30), nullable=False),
        sa.Column("target_id", sa.Integer(), nullable=False),
        sa.Column("fields", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()))
    op.create_table("ai_operations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("operation", sa.String(40), nullable=False),
        sa.Column("provider", sa.String(30), nullable=False),
        sa.Column("outcome", sa.String(20), nullable=False),
        sa.Column("latency_ms", sa.Float(), nullable=False),
        sa.Column("is_mock", sa.Boolean()),
        sa.Column("truncated", sa.Boolean()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()))
    op.create_index("ix_ai_operations_created_at", "ai_operations", ["created_at"])


def downgrade():
    op.drop_table("ai_operations")
    op.drop_table("audit_events")
    op.drop_column("users", "profile_version")
    op.drop_column("users", "is_active")
