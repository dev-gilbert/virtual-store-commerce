"""Add rich product discovery and tenant-scoped commerce columns."""
from alembic import op
import sqlalchemy as sa
from app.main import SearchEvent, ProductReview, WishlistItem, StockMovement, StoreLayoutVersion

revision = "0004_search_tenant_security"
down_revision = "0003_retailer_operations"
branch_labels = None
depends_on = None

RICH_PRODUCT_COLUMNS = {
    "brand": sa.Column("brand", sa.String(120), nullable=False, server_default=""),
    "synonyms": sa.Column("synonyms", sa.Text(), nullable=False, server_default=""),
    "unit": sa.Column("unit", sa.String(40), nullable=False, server_default="each"),
    "ingredients": sa.Column("ingredients", sa.Text(), nullable=False, server_default=""),
    "allergens": sa.Column("allergens", sa.Text(), nullable=False, server_default=""),
    "nutrition": sa.Column("nutrition", sa.Text(), nullable=False, server_default=""),
    "gallery_json": sa.Column("gallery_json", sa.Text(), nullable=False, server_default="[]"),
    "video_url": sa.Column("video_url", sa.String(500), nullable=True),
    "discontinued": sa.Column("discontinued", sa.Boolean(), nullable=False, server_default=sa.false()),
    "popularity": sa.Column("popularity", sa.Integer(), nullable=False, server_default="0"),
    "tenant_id": sa.Column("tenant_id", sa.String(36), nullable=True),
}
TENANT_TABLES = (
    "fixtures", "product_placements", "cart_items", "orders", "promotions",
    "suppliers", "purchase_orders", "store_branches", "branch_inventory",
    "staff_members", "return_requests", "audit_events", "search_events",
    "product_reviews", "wishlist_items", "stock_movements", "store_layout_versions",
)

def _add_missing(table_name, column):
    inspector = sa.inspect(op.get_bind())
    if inspector.has_table(table_name):
        existing = {item["name"] for item in inspector.get_columns(table_name)}
        if column.name not in existing:
            op.add_column(table_name, column)

ORDER_COLUMNS = {
    "discount_amount": sa.Column("discount_amount", sa.Numeric(12, 2), nullable=False, server_default="0"),
    "delivery_fee": sa.Column("delivery_fee", sa.Numeric(12, 2), nullable=False, server_default="0"),
    "total": sa.Column("total", sa.Numeric(12, 2), nullable=False, server_default="0"),
    "delivery_method": sa.Column("delivery_method", sa.String(20), nullable=False, server_default="delivery"),
    "expected_delivery_window": sa.Column("expected_delivery_window", sa.String(120), nullable=True),
    "proof_of_delivery": sa.Column("proof_of_delivery", sa.Text(), nullable=True),
}

def upgrade():
    bind = op.get_bind()
    for model in (SearchEvent, ProductReview, WishlistItem, StockMovement, StoreLayoutVersion):
        model.__table__.create(bind=bind, checkfirst=True)
    for name, column in RICH_PRODUCT_COLUMNS.items():
        _add_missing("products", column)
    for name, column in ORDER_COLUMNS.items():
        _add_missing("orders", column)
    for table_name in TENANT_TABLES:
        _add_missing(table_name, sa.Column("tenant_id", sa.String(36), nullable=True))
    for table_name in ("products",) + TENANT_TABLES:
        inspector = sa.inspect(bind)
        if inspector.has_table(table_name):
            names = {item["name"] for item in inspector.get_columns(table_name)}
            if "tenant_id" in names:
                index_name = f"ix_{table_name}_tenant_id"
                indexes = {item["name"] for item in inspector.get_indexes(table_name)}
                if index_name not in indexes:
                    op.create_index(index_name, table_name, ["tenant_id"], unique=False)

def downgrade():
    # Keep tenant data and discovery history intact; schema rollback is intentionally non-destructive.
    pass
