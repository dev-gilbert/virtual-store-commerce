"""Add customer contact and delivery details to orders."""
from alembic import op
import sqlalchemy as sa

revision = "0002_order_customer_details"
down_revision = "0001_initial"
branch_labels = None
depends_on = None

def upgrade() -> None:
    existing = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("orders")}
    columns = [
        sa.Column("customer_name", sa.String(length=180), nullable=True),
        sa.Column("customer_phone", sa.String(length=40), nullable=False, server_default=""),
        sa.Column("customer_email", sa.String(length=254), nullable=True),
        sa.Column("delivery_address", sa.Text(), nullable=True),
        sa.Column("delivery_instructions", sa.Text(), nullable=True),
        sa.Column("is_anonymous", sa.Boolean(), nullable=False, server_default=sa.false()),
    ]
    for column in columns:
        if column.name not in existing:
            op.add_column("orders", column)

def downgrade() -> None:
    existing = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("orders")}
    for name in ("is_anonymous", "delivery_instructions", "delivery_address", "customer_email", "customer_phone", "customer_name"):
        if name in existing:
            op.drop_column("orders", name)
