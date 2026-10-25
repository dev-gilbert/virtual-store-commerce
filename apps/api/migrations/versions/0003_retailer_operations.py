"""Add retailer operations tables for promotions, suppliers, branches, staff and returns."""
from alembic import op
from app.main import Promotion, Supplier, PurchaseOrder, StoreBranch, BranchInventory, StaffMember, ReturnRequest

revision = "0003_retailer_operations"
down_revision = "0002_order_customer_details"
branch_labels = None
depends_on = None

TABLES = [Promotion.__table__, Supplier.__table__, PurchaseOrder.__table__, StoreBranch.__table__, BranchInventory.__table__, StaffMember.__table__, ReturnRequest.__table__]

def upgrade():
    bind = op.get_bind()
    for table in TABLES:
        table.create(bind=bind, checkfirst=True)

def downgrade():
    bind = op.get_bind()
    for table in reversed(TABLES):
        table.drop(bind=bind, checkfirst=True)
