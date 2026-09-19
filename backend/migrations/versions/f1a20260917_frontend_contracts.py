"""Persist submission content and provenance; never fabricate lost history."""
from alembic import op
import sqlalchemy as sa

revision = 'f1a20260917'
down_revision = 'e49cd157b008'
branch_labels = depends_on = None

CASCADE = [('rubrics', 'task_id', 'tasks'), ('submissions', 'task_id', 'tasks'),
    ('submissions', 'rubric_id', 'rubrics'), ('submissions', 'team_id', 'teams'),
    ('code_reviews', 'submission_id', 'submissions'), ('code_reviews', 'commit_id', 'commits'),
    ('repositories', 'task_id', 'tasks'), ('repositories', 'team_id', 'teams'),
    ('commits', 'repository_id', 'repositories')]

def replace_fk(table, column, target, cascade):
    for fk in sa.inspect(op.get_bind()).get_foreign_keys(table):
        if fk['constrained_columns'] == [column]:
            op.drop_constraint(fk['name'], table, type_='foreignkey')
    op.create_foreign_key(f'fk_{table}_{column}', table, target, [column], ['id'],
                          ondelete='CASCADE' if cascade else None)

def upgrade():
    op.add_column('submissions', sa.Column('submission_text', sa.Text(), server_default='', nullable=False))
    op.add_column('submissions', sa.Column('total_possible_grade', sa.Float(), nullable=True))
    op.add_column('submissions', sa.Column('criterion_evaluations', sa.JSON(), nullable=True))
    op.add_column('submissions', sa.Column('ai_warnings', sa.JSON(), nullable=True))
    op.add_column('submissions', sa.Column('is_mock', sa.Boolean(), nullable=True))
    op.add_column('files', sa.Column('original_filename', sa.String(255), nullable=True))
    op.alter_column('rubrics', 'reviewed_at', type_=sa.DateTime(timezone=True),
                    postgresql_using="reviewed_at AT TIME ZONE 'UTC'")
    for args in CASCADE:
        replace_fk(*args, cascade=True)

def downgrade():
    for args in reversed(CASCADE):
        replace_fk(*args, cascade=False)
    op.alter_column('rubrics', 'reviewed_at', type_=sa.DateTime(timezone=False),
                    postgresql_using="reviewed_at AT TIME ZONE 'UTC'")
    op.drop_column('files', 'original_filename')
    for column in ('is_mock', 'ai_warnings', 'criterion_evaluations', 'total_possible_grade', 'submission_text'):
        op.drop_column('submissions', column)
