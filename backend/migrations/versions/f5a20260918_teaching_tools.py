"""Private grading guidance and released-result teaching reports."""
from alembic import op
import sqlalchemy as sa

revision = "f5a20260918"
down_revision = "f4a20260918"
branch_labels = depends_on = None


def upgrade():
    op.create_table("grading_guidance",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("task_id", sa.Integer(), sa.ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("request_id", sa.String(36), nullable=False),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("staff.user_id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("task_id", "version", name="uq_guidance_version"),
        sa.UniqueConstraint("task_id", "request_id", name="uq_guidance_request"))
    op.create_index("ix_grading_guidance_task_id", "grading_guidance", ["task_id"])
    op.add_column("submissions", sa.Column("grading_guidance_id", sa.Integer(),
        sa.ForeignKey("grading_guidance.id", ondelete="SET NULL"), nullable=True))
    op.create_table("teaching_reports",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("task_id", sa.Integer(), sa.ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("rubric_id", sa.Integer(), sa.ForeignKey("rubrics.id", ondelete="CASCADE"), nullable=False),
        sa.Column("rubric_version", sa.Integer(), nullable=False),
        sa.Column("request_id", sa.String(36), nullable=False),
        sa.Column("language", sa.String(2), nullable=False),
        sa.Column("input_fingerprint", sa.String(64), nullable=False),
        sa.Column("input_snapshot", sa.JSON(), nullable=False),
        sa.Column("result", sa.JSON(), nullable=False),
        sa.Column("is_mock", sa.Boolean(), nullable=False),
        sa.Column("ai_metadata", sa.JSON()),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("staff.user_id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("task_id", "request_id", name="uq_teaching_report_request"))
    op.create_index("ix_teaching_reports_task_id", "teaching_reports", ["task_id"])


def downgrade():
    op.drop_table("teaching_reports")
    op.drop_column("submissions", "grading_guidance_id")
    op.drop_table("grading_guidance")
