from alembic import op
import sqlalchemy as sa

revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('email', sa.String(length=255), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_table(
        'app_projects',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('owner_user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('package_name', sa.String(length=255), nullable=False, unique=True),
        sa.Column('url', sa.String(length=1024), nullable=False),
        sa.Column('min_sdk', sa.Integer(), nullable=False),
        sa.Column('target_sdk', sa.Integer(), nullable=False),
        sa.Column('version_code', sa.Integer(), nullable=False),
        sa.Column('version_name', sa.String(length=50), nullable=False),
        sa.Column('icon_path', sa.String(length=1024), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )
    op.create_table(
        'keystores',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('app_project_id', sa.Integer(), sa.ForeignKey('app_projects.id'), nullable=False, unique=True),
        sa.Column('keystore_path', sa.String(length=1024), nullable=False),
        sa.Column('alias', sa.String(length=255), nullable=False),
        sa.Column('store_password', sa.String(length=255), nullable=False),
        sa.Column('key_password', sa.String(length=255), nullable=False),
        sa.Column('download_allowed', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )
    op.create_table(
        'build_jobs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('app_project_id', sa.Integer(), sa.ForeignKey('app_projects.id'), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('log', sa.Text(), nullable=True),
        sa.Column('apk_path', sa.String(length=1024), nullable=True),
        sa.Column('aab_path', sa.String(length=1024), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('finished_at', sa.DateTime(), nullable=True),
    )
    op.create_table(
        'keystore_download_requests',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('keystore_id', sa.Integer(), sa.ForeignKey('keystores.id'), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('admin_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('decision_at', sa.DateTime(), nullable=True),
    )


def downgrade():
    op.drop_table('keystore_download_requests')
    op.drop_table('build_jobs')
    op.drop_table('keystores')
    op.drop_table('app_projects')
    op.drop_table('users')
