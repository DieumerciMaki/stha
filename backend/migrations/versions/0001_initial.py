"""Initial schema snapshot; independent of subsequent ORM changes."""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('settings',
        sa.Column('key', sa.String(length=64), nullable=False, primary_key=True),
        sa.Column('value', sa.Text(), nullable=False, primary_key=False),
    )
    op.create_table('users',
        sa.Column('id', sa.String(length=36), nullable=False, primary_key=True),
        sa.Column('name', sa.String(length=120), nullable=False, primary_key=False),
        sa.Column('login', sa.String(length=120), nullable=False, primary_key=False, unique=True),
        sa.Column('password_hash', sa.Text(), nullable=False, primary_key=False),
        sa.Column('role', sa.String(length=24), nullable=False, primary_key=False),
        sa.Column('active', sa.Boolean(), nullable=False, primary_key=False),
        sa.Column('created_at', sa.String(length=40), nullable=False, primary_key=False),
    )
    op.create_table('login_sessions',
        sa.Column('token_hash', sa.String(length=64), nullable=False, primary_key=True),
        sa.Column('user_id', sa.String(length=36), sa.ForeignKey('users.id'), nullable=False, primary_key=False),
        sa.Column('expires_at', sa.String(length=40), nullable=False, primary_key=False),
    )
    op.create_index('ix_login_sessions_user_id', 'login_sessions', ['user_id'], unique=False)
    op.create_table('observations',
        sa.Column('id', sa.String(length=36), nullable=False, primary_key=True),
        sa.Column('title', sa.String(length=120), nullable=False, primary_key=False),
        sa.Column('neighborhood', sa.String(length=120), nullable=False, primary_key=False),
        sa.Column('location', sa.String(length=160), nullable=False, primary_key=False),
        sa.Column('notes', sa.Text(), nullable=False, primary_key=False),
        sa.Column('latitude', sa.Float(), nullable=True, primary_key=False),
        sa.Column('longitude', sa.Float(), nullable=True, primary_key=False),
        sa.Column('coordinate_source', sa.String(length=24), nullable=True, primary_key=False),
        sa.Column('captured_at', sa.String(length=10), nullable=True, primary_key=False),
        sa.Column('created_at', sa.String(length=40), nullable=False, primary_key=False),
        sa.Column('created_by', sa.String(length=36), sa.ForeignKey('users.id'), nullable=False, primary_key=False),
        sa.Column('width', sa.Integer(), nullable=False, primary_key=False),
        sa.Column('height', sa.Integer(), nullable=False, primary_key=False),
        sa.Column('image_sha256', sa.String(length=64), nullable=False, primary_key=False),
        sa.Column('original_sha256', sa.String(length=64), nullable=False, primary_key=False),
    )
    op.create_index('ix_observations_created_at', 'observations', ['created_at'], unique=False)
    op.create_table('analyses',
        sa.Column('id', sa.String(length=36), nullable=False, primary_key=True),
        sa.Column('observation_id', sa.String(length=36), sa.ForeignKey('observations.id'), nullable=False, primary_key=False),
        sa.Column('status', sa.String(length=24), nullable=False, primary_key=False),
        sa.Column('created_at', sa.String(length=40), nullable=False, primary_key=False),
        sa.Column('finished_at', sa.String(length=40), nullable=True, primary_key=False),
        sa.Column('created_by', sa.String(length=36), sa.ForeignKey('users.id'), nullable=False, primary_key=False),
        sa.Column('confidence', sa.Float(), nullable=False, primary_key=False),
        sa.Column('result_json', sa.Text(), nullable=True, primary_key=False),
        sa.Column('error', sa.Text(), nullable=True, primary_key=False),
    )
    op.create_index('ix_analyses_status', 'analyses', ['status'], unique=False)
    op.create_index('ix_analyses_observation_id', 'analyses', ['observation_id'], unique=False)
    op.create_table('reviews',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('analysis_id', sa.String(length=36), sa.ForeignKey('analyses.id'), nullable=False, primary_key=False),
        sa.Column('decision', sa.String(length=24), nullable=False, primary_key=False),
        sa.Column('comment', sa.Text(), nullable=False, primary_key=False),
        sa.Column('reviewed_by', sa.String(length=36), sa.ForeignKey('users.id'), nullable=False, primary_key=False),
        sa.Column('created_at', sa.String(length=40), nullable=False, primary_key=False),
    )
    op.create_index('ix_reviews_analysis_id', 'reviews', ['analysis_id'], unique=False)

def downgrade():
    op.drop_table('reviews')
    op.drop_table('analyses')
    op.drop_table('observations')
    op.drop_table('login_sessions')
    op.drop_table('users')
    op.drop_table('settings')
