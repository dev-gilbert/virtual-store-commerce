"""Add customer contact and delivery details to orders."""
from alembic import op
import sqlalchemy as sa

revision = "0002_order_customer_details"
down_revision = "0001_initial"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column("orders", sa.Column("customer_name", sa.String(length=180), nullable=True))
    op.add_column("orders", sa.Column("customer_phone", sa.String(length=40), nullable=False, server_default=""))
    op.add_column("orders", sa.Column("customer_email", sa.String(length=254), nullable=True))
    op.add_column("orders", sa.Column("delivery_address", sa.Text(), nullable=True))
    op.add_column("orders", sa.Column("delivery_instructions", sa.Text(), nullable=True))
    op.add_column("orders", sa.Column("is_anonymous", sa.Boolean(), nullable=False, server_default=sa.false()))

def downgrade() -> None:
    op.drop_column("orders", "is_anonymous")
    op.drop_column("orders", "delivery_instructions")
    op.drop_column("orders", "delivery_address")
    op.drop_column("orders", "customer_email")
    op.drop_column("orders", "customer_phone")
    op.drop_column("orders", "customer_name")
