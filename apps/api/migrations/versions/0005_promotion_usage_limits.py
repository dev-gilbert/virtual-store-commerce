"""Ensure coupon redemption limits exist (also added by 0004 for fresh installs)."""
from alembic import op
import sqlalchemy as sa

revision = "0005_promotion_usage_limits"
down_revision = "0004_search_tenant_security"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    existing = {column["name"] for column in inspector.get_columns("promotions")}
    if "usage_limit" not in existing:
        op.add_column("promotions", sa.Column("usage_limit", sa.Integer(), nullable=True))
    if "usage_count" not in existing:
        op.add_column("promotions", sa.Column("usage_count", sa.Integer(), nullable=False, server_default="0"))


def downgrade() -> None:
    # Preserve redemption data during rollback; the columns are safe to leave in place.
    pass
