"""Store UTC review timestamps consistently with the ORM."""
from alembic import op
import sqlalchemy as sa

revision = 'f2a20260918'
down_revision = 'f1a20260917'
branch_labels = depends_on = None

def upgrade():
    op.alter_column('code_reviews', 'created_at', type_=sa.DateTime(timezone=True),
                    postgresql_using="created_at AT TIME ZONE 'UTC'")

def downgrade():
    op.alter_column('code_reviews', 'created_at', type_=sa.DateTime(timezone=False),
                    postgresql_using="created_at AT TIME ZONE 'UTC'")
