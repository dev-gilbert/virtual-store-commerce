"""Add coupon redemption limits and counters."""
from alembic import op
import sqlalchemy as sa

revision = "0005_promotion_usage_limits"
down_revision = "0004_search_tenant_security"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("promotions", sa.Column("usage_limit", sa.Integer(), nullable=True))
    op.add_column("promotions", sa.Column("usage_count", sa.Integer(), nullable=False, server_default="0"))


def downgrade() -> None:
    op.drop_column("promotions", "usage_count")
    op.drop_column("promotions", "usage_limit")
