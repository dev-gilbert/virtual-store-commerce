from __future__ import annotations
import os, uuid, hmac, hashlib, secrets, base64, time, smtplib, contextvars
from decimal import InvalidOperation
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from email.message import EmailMessage
from decimal import Decimal
from typing import Generator
from fastapi import Cookie, Depends, FastAPI, Header, HTTPException, Query, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, create_engine, select, func, event
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, sessionmaker, with_loader_criteria

DATABASE_URL=os.getenv("DATABASE_URL","sqlite:///./virtual_store.db")
engine=create_engine(DATABASE_URL,connect_args={"check_same_thread":False} if DATABASE_URL.startswith("sqlite") else {},pool_pre_ping=True)
SessionLocal=sessionmaker(bind=engine,autoflush=False,expire_on_commit=False)
def utcnow(): return datetime.now(timezone.utc)
class Base(DeclarativeBase): pass
class Product(Base):
 __tablename__="products"
 id:Mapped[str]=mapped_column(String(36),primary_key=True,default=lambda:str(uuid.uuid4()))
 sku:Mapped[str]=mapped_column(String(80),unique=True,index=True); name:Mapped[str]=mapped_column(String(180),index=True)
 description:Mapped[str]=mapped_column(Text,default=""); category:Mapped[str]=mapped_column(String(80),index=True)
 price:Mapped[Decimal]=mapped_column(Numeric(12,2)); currency:Mapped[str]=mapped_column(String(3),default="RWF")
 stock_quantity:Mapped[int]=mapped_column(Integer,default=0); image_url:Mapped[str|None]=mapped_column(String(500),nullable=True)
 color:Mapped[str]=mapped_column(String(16),default="#799d79"); active:Mapped[bool]=mapped_column(Boolean,default=True)
 brand:Mapped[str]=mapped_column(String(120),default="",index=True); synonyms:Mapped[str]=mapped_column(Text,default="")
 unit:Mapped[str]=mapped_column(String(40),default="each"); ingredients:Mapped[str]=mapped_column(Text,default="")
 allergens:Mapped[str]=mapped_column(Text,default=""); nutrition:Mapped[str]=mapped_column(Text,default="")
 gallery_json:Mapped[str]=mapped_column(Text,default="[]"); video_url:Mapped[str|None]=mapped_column(String(500),nullable=True)
 discontinued:Mapped[bool]=mapped_column(Boolean,default=False); popularity:Mapped[int]=mapped_column(Integer,default=0)
 tenant_id:Mapped[str|None]=mapped_column(String(36),nullable=True,index=True)
 created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow)
class Fixture(Base):
 __tablename__="fixtures"
 id:Mapped[str]=mapped_column(String(36),primary_key=True,default=lambda:str(uuid.uuid4()))
 code:Mapped[str]=mapped_column(String(80),unique=True); name:Mapped[str]=mapped_column(String(160)); kind:Mapped[str]=mapped_column(String(40),default="shelf")
 x:Mapped[float]=mapped_column(Numeric(8,3),default=0); y:Mapped[float]=mapped_column(Numeric(8,3),default=0); z:Mapped[float]=mapped_column(Numeric(8,3),default=0); tenant_id:Mapped[str|None]=mapped_column(String(36),nullable=True,index=True)
class ProductPlacement(Base):
 __tablename__="product_placements"
 id:Mapped[str]=mapped_column(String(36),primary_key=True,default=lambda:str(uuid.uuid4()))
 product_id:Mapped[str]=mapped_column(ForeignKey("products.id",ondelete="CASCADE"),index=True); fixture_id:Mapped[str]=mapped_column(ForeignKey("fixtures.id",ondelete="CASCADE"),index=True)
 shelf_level:Mapped[int]=mapped_column(Integer,default=0); slot:Mapped[int]=mapped_column(Integer,default=0); tenant_id:Mapped[str|None]=mapped_column(String(36),nullable=True,index=True)
 product:Mapped[Product]=relationship()
 __table_args__=(UniqueConstraint("product_id","fixture_id","shelf_level","slot",name="uq_product_fixture_slot"),)
class CartItem(Base):
 __tablename__="cart_items"
 id:Mapped[str]=mapped_column(String(36),primary_key=True,default=lambda:str(uuid.uuid4()))
 session_id:Mapped[str]=mapped_column(String(100),index=True); product_id:Mapped[str]=mapped_column(ForeignKey("products.id",ondelete="CASCADE"),index=True)
 quantity:Mapped[int]=mapped_column(Integer,default=1); tenant_id:Mapped[str|None]=mapped_column(String(36),nullable=True,index=True); product:Mapped[Product]=relationship()
 __table_args__=(UniqueConstraint("session_id","product_id",name="uq_cart_session_product"),)
class Order(Base):
 __tablename__="orders"
 id:Mapped[str]=mapped_column(String(36),primary_key=True,default=lambda:str(uuid.uuid4()))
 session_id:Mapped[str]=mapped_column(String(100),index=True); idempotency_key:Mapped[str]=mapped_column(String(160),unique=True,index=True)
 status:Mapped[str]=mapped_column(String(30),default="pending_payment"); payment_status:Mapped[str]=mapped_column(String(30),default="unpaid")
 subtotal:Mapped[Decimal]=mapped_column(Numeric(12,2)); currency:Mapped[str]=mapped_column(String(3),default="RWF")
 customer_name:Mapped[str|None]=mapped_column(String(180),nullable=True); customer_phone:Mapped[str]=mapped_column(String(40),default="")
 customer_email:Mapped[str|None]=mapped_column(String(254),nullable=True); delivery_address:Mapped[str|None]=mapped_column(Text,nullable=True)
 delivery_instructions:Mapped[str|None]=mapped_column(Text,nullable=True); is_anonymous:Mapped[bool]=mapped_column(Boolean,default=False); tenant_id:Mapped[str|None]=mapped_column(String(36),nullable=True,index=True)
 created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow)
 items:Mapped[list["OrderItem"]]=relationship(back_populates="order",cascade="all, delete-orphan")
class OrderItem(Base):
 __tablename__="order_items"
 id:Mapped[str]=mapped_column(String(36),primary_key=True,default=lambda:str(uuid.uuid4()))
 order_id:Mapped[str]=mapped_column(ForeignKey("orders.id",ondelete="CASCADE"),index=True); product_id:Mapped[str]=mapped_column(String(36))
 sku:Mapped[str]=mapped_column(String(80)); product_name:Mapped[str]=mapped_column(String(180)); unit_price:Mapped[Decimal]=mapped_column(Numeric(12,2)); quantity:Mapped[int]=mapped_column(Integer)
 order:Mapped[Order]=relationship(back_populates="items")
class SearchEvent(Base):
 __tablename__="search_events"
 id:Mapped[str]=mapped_column(String(36),primary_key=True,default=lambda:str(uuid.uuid4()))
 query:Mapped[str]=mapped_column(String(180),index=True)
 result_count:Mapped[int]=mapped_column(Integer,default=0)
 session_id:Mapped[str|None]=mapped_column(String(100),nullable=True,index=True)
 created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow); tenant_id:Mapped[str|None]=mapped_column(String(36),nullable=True,index=True)
class ProductReview(Base):
 __tablename__="product_reviews"
 id:Mapped[str]=mapped_column(String(36),primary_key=True,default=lambda:str(uuid.uuid4()))
 product_id:Mapped[str]=mapped_column(ForeignKey("products.id",ondelete="CASCADE"),index=True)
 session_id:Mapped[str]=mapped_column(String(100),index=True)
 rating:Mapped[int]=mapped_column(Integer)
 title:Mapped[str]=mapped_column(String(180),default="")
 body:Mapped[str]=mapped_column(String(2000),default="")
 tenant_id:Mapped[str|None]=mapped_column(String(36),nullable=True,index=True); created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow)
 __table_args__=(UniqueConstraint("product_id","session_id",name="uq_review_product_session"),)
class WishlistItem(Base):
 __tablename__="wishlist_items"
 id:Mapped[str]=mapped_column(String(36),primary_key=True,default=lambda:str(uuid.uuid4()))
 session_id:Mapped[str]=mapped_column(String(100),index=True)
 product_id:Mapped[str]=mapped_column(ForeignKey("products.id",ondelete="CASCADE"),index=True)
 tenant_id:Mapped[str|None]=mapped_column(String(36),nullable=True,index=True); created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow)
 __table_args__=(UniqueConstraint("session_id","product_id",name="uq_wishlist_session_product"),)
class AuditEvent(Base):
 __tablename__="audit_events"
 id:Mapped[str]=mapped_column(String(36),primary_key=True,default=lambda:str(uuid.uuid4())); event_type:Mapped[str]=mapped_column(String(100),index=True)
 entity_type:Mapped[str]=mapped_column(String(80)); entity_id:Mapped[str]=mapped_column(String(36),index=True); details:Mapped[str]=mapped_column(Text,default="{}")
 tenant_id:Mapped[str|None]=mapped_column(String(36),nullable=True,index=True)
 created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow)


class StoreTenant(Base):
 __tablename__="store_tenants"
 id:Mapped[str]=mapped_column(String(36),primary_key=True,default=lambda:str(uuid.uuid4()))
 name:Mapped[str]=mapped_column(String(180),index=True)
 slug:Mapped[str]=mapped_column(String(200),unique=True,index=True)
 owner_account_id:Mapped[str]=mapped_column(String(36),index=True)
 status:Mapped[str]=mapped_column(String(24),default="pending",index=True)
 plan:Mapped[str]=mapped_column(String(40),default="starter")
 notes:Mapped[str]=mapped_column(Text,default="")
 created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow)
 reviewed_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True),nullable=True)
 reviewed_by:Mapped[str|None]=mapped_column(String(36),nullable=True)

class Account(Base):
 __tablename__="accounts"
 id:Mapped[str]=mapped_column(String(36),primary_key=True,default=lambda:str(uuid.uuid4()))
 name:Mapped[str]=mapped_column(String(180)); email:Mapped[str]=mapped_column(String(254),unique=True,index=True)
 password_hash:Mapped[str]=mapped_column(String(256)); role:Mapped[str]=mapped_column(String(32),default="store_owner")
 store_name:Mapped[str|None]=mapped_column(String(180),nullable=True); active:Mapped[bool]=mapped_column(Boolean,default=True)
 store_id:Mapped[str|None]=mapped_column(String(36),nullable=True,index=True)
 reset_token_hash:Mapped[str|None]=mapped_column(String(64),nullable=True); reset_expires_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True),nullable=True)
 created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow)

class Promotion(Base):
 __tablename__="promotions"
 id:Mapped[str]=mapped_column(String(36),primary_key=True,default=lambda:str(uuid.uuid4()))
 code:Mapped[str]=mapped_column(String(40),unique=True,index=True); discount_percent:Mapped[int]=mapped_column(Integer)
 active:Mapped[bool]=mapped_column(Boolean,default=True); min_subtotal:Mapped[Decimal]=mapped_column(Numeric(12,2),default=0)
 starts_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True),nullable=True); ends_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True),nullable=True); tenant_id:Mapped[str|None]=mapped_column(String(36),nullable=True,index=True)
class Supplier(Base):
 __tablename__="suppliers"
 id:Mapped[str]=mapped_column(String(36),primary_key=True,default=lambda:str(uuid.uuid4()))
 name:Mapped[str]=mapped_column(String(180)); contact_name:Mapped[str|None]=mapped_column(String(180),nullable=True); phone:Mapped[str|None]=mapped_column(String(40),nullable=True); email:Mapped[str|None]=mapped_column(String(254),nullable=True); active:Mapped[bool]=mapped_column(Boolean,default=True); tenant_id:Mapped[str|None]=mapped_column(String(36),nullable=True,index=True)
class PurchaseOrder(Base):
 __tablename__="purchase_orders"
 id:Mapped[str]=mapped_column(String(36),primary_key=True,default=lambda:str(uuid.uuid4()))
 supplier_id:Mapped[str]=mapped_column(ForeignKey("suppliers.id"),index=True); product_id:Mapped[str]=mapped_column(ForeignKey("products.id"),index=True)
 quantity:Mapped[int]=mapped_column(Integer); unit_cost:Mapped[Decimal]=mapped_column(Numeric(12,2)); status:Mapped[str]=mapped_column(String(24),default="draft"); created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow); tenant_id:Mapped[str|None]=mapped_column(String(36),nullable=True,index=True)
class StoreBranch(Base):
 __tablename__="store_branches"
 id:Mapped[str]=mapped_column(String(36),primary_key=True,default=lambda:str(uuid.uuid4()))
 code:Mapped[str]=mapped_column(String(40),unique=True,index=True); name:Mapped[str]=mapped_column(String(180)); address:Mapped[str]=mapped_column(String(500),default=""); active:Mapped[bool]=mapped_column(Boolean,default=True); tenant_id:Mapped[str|None]=mapped_column(String(36),nullable=True,index=True)
class BranchInventory(Base):
 __tablename__="branch_inventory"
 id:Mapped[str]=mapped_column(String(36),primary_key=True,default=lambda:str(uuid.uuid4()))
 branch_id:Mapped[str]=mapped_column(ForeignKey("store_branches.id"),index=True); product_id:Mapped[str]=mapped_column(ForeignKey("products.id"),index=True); quantity:Mapped[int]=mapped_column(Integer,default=0); tenant_id:Mapped[str|None]=mapped_column(String(36),nullable=True,index=True)
 __table_args__=(UniqueConstraint("branch_id","product_id",name="uq_branch_product"),)
class StaffMember(Base):
 __tablename__="staff_members"
 id:Mapped[str]=mapped_column(String(36),primary_key=True,default=lambda:str(uuid.uuid4()))
 name:Mapped[str]=mapped_column(String(180)); email:Mapped[str]=mapped_column(String(254),unique=True,index=True); role:Mapped[str]=mapped_column(String(30),default="viewer"); active:Mapped[bool]=mapped_column(Boolean,default=True); tenant_id:Mapped[str|None]=mapped_column(String(36),nullable=True,index=True)
class ReturnRequest(Base):
 __tablename__="return_requests"
 id:Mapped[str]=mapped_column(String(36),primary_key=True,default=lambda:str(uuid.uuid4()))
 order_id:Mapped[str]=mapped_column(ForeignKey("orders.id"),index=True); reason:Mapped[str]=mapped_column(String(500)); status:Mapped[str]=mapped_column(String(24),default="requested"); refund_amount:Mapped[Decimal]=mapped_column(Numeric(12,2),default=0); created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow); tenant_id:Mapped[str|None]=mapped_column(String(36),nullable=True,index=True)


tenant_scope=contextvars.ContextVar("virtual_store_tenant_scope",default=None)
TENANT_MODELS=(Product,Fixture,ProductPlacement,CartItem,Order,Promotion,Supplier,PurchaseOrder,StoreBranch,BranchInventory,StaffMember,ReturnRequest,AuditEvent,SearchEvent,ProductReview,WishlistItem)
@event.listens_for(Session,"do_orm_execute")
def apply_tenant_scope(execute_state):
 tenant_id=tenant_scope.get()
 if not execute_state.is_select or tenant_id is None:return
 for model in TENANT_MODELS:
  if tenant_id=="__public__":
   execute_state.statement=execute_state.statement.options(with_loader_criteria(model,lambda cls:cls.tenant_id.is_(None),include_aliases=True))
  else:
   execute_state.statement=execute_state.statement.options(with_loader_criteria(model,lambda cls:cls.tenant_id==tenant_id,include_aliases=True))
@event.listens_for(Session,"before_flush")
def assign_tenant_on_insert(session,flush_context,instances):
 tenant_id=tenant_scope.get()
 if tenant_id and tenant_id!="__public__":
  for obj in session.new:
   if isinstance(obj,TENANT_MODELS) and getattr(obj,"tenant_id",None) is None:obj.tenant_id=tenant_id
def ensure_tenant_columns():
 from sqlalchemy import inspect, text
 definitions={
  "products":"VARCHAR(36)","fixtures":"VARCHAR(36)","product_placements":"VARCHAR(36)","cart_items":"VARCHAR(36)","orders":"VARCHAR(36)",
  "promotions":"VARCHAR(36)","suppliers":"VARCHAR(36)","purchase_orders":"VARCHAR(36)","store_branches":"VARCHAR(36)","branch_inventory":"VARCHAR(36)",
  "staff_members":"VARCHAR(36)","return_requests":"VARCHAR(36)","audit_events":"VARCHAR(36)","search_events":"VARCHAR(36)","product_reviews":"VARCHAR(36)","wishlist_items":"VARCHAR(36)"
 }
 inspector=inspect(engine)
 with engine.begin() as connection:
  for table,column_type in definitions.items():
   if not inspector.has_table(table):continue
   existing={column["name"] for column in inspector.get_columns(table)}
   if "tenant_id" not in existing:connection.execute(text(f"ALTER TABLE {table} ADD COLUMN tenant_id {column_type}"))

def get_db()->Generator[Session,None,None]:
 db=SessionLocal()
 try: yield db
 finally: db.close()
class ProductCreate(BaseModel):
 sku:str=Field(min_length=2,max_length=80); name:str=Field(min_length=2,max_length=180); description:str=Field(default="",max_length=2000)
 category:str=Field(min_length=2,max_length=80); price:Decimal=Field(gt=0,max_digits=12,decimal_places=2); currency:str=Field(default="RWF",min_length=3,max_length=3)
 stock_quantity:int=Field(default=0,ge=0,le=1000000); image_url:str|None=Field(default=None,max_length=500); color:str=Field(default="#799d79",pattern=r"^#[0-9a-fA-F]{6}$")
 brand:str=Field(default="",max_length=120); synonyms:str=Field(default="",max_length=1000); unit:str=Field(default="each",max_length=40)
 ingredients:str=Field(default="",max_length=4000); allergens:str=Field(default="",max_length=1000); nutrition:str=Field(default="",max_length=2000)
 gallery_json:str=Field(default="[]",max_length=10000); video_url:str|None=Field(default=None,max_length=500); discontinued:bool=False
class ProductPatch(BaseModel):
 name:str|None=Field(default=None,min_length=2,max_length=180); description:str|None=Field(default=None,max_length=2000)
 category:str|None=Field(default=None,min_length=2,max_length=80); price:Decimal|None=Field(default=None,gt=0,max_digits=12,decimal_places=2)
 stock_quantity:int|None=Field(default=None,ge=0,le=1000000); active:bool|None=None
 brand:str|None=Field(default=None,max_length=120); synonyms:str|None=Field(default=None,max_length=1000); unit:str|None=Field(default=None,max_length=40)
 ingredients:str|None=Field(default=None,max_length=4000); allergens:str|None=Field(default=None,max_length=1000); nutrition:str|None=Field(default=None,max_length=2000)
 gallery_json:str|None=Field(default=None,max_length=10000); video_url:str|None=Field(default=None,max_length=500); discontinued:bool|None=None
class ProductOut(BaseModel):
 model_config=ConfigDict(from_attributes=True)
 id:str; sku:str; name:str; description:str; category:str; price:Decimal; currency:str; stock_quantity:int; image_url:str|None; color:str; active:bool
 brand:str=""; synonyms:str=""; unit:str="each"; ingredients:str=""; allergens:str=""; nutrition:str=""; gallery_json:str="[]"; video_url:str|None=None; discontinued:bool=False
class FixtureCreate(BaseModel):
 code:str=Field(min_length=2,max_length=80,pattern=r"^[A-Za-z0-9_-]+$")
 name:str=Field(min_length=2,max_length=160)
 kind:str=Field(default="shelf",pattern=r"^(shelf|drawer|table|display|refrigerator|checkout)$")
 x:float=Field(default=0,ge=-20,le=20); y:float=Field(default=0,ge=0,le=5); z:float=Field(default=0,ge=-20,le=20)
class PlacementCreate(BaseModel):
 product_id:str
 shelf_level:int=Field(default=0,ge=0,le=5)
 slot:int=Field(default=0,ge=0,le=20)
class CartItemInput(BaseModel):
 product_id:str; quantity:int=Field(default=1,ge=1,le=99)
class CheckoutInput(BaseModel):
 session_id:str=Field(min_length=8,max_length=100)
 customer_phone:str=Field(min_length=7,max_length=40)
 customer_name:str|None=Field(default=None,max_length=180)
 customer_email:str|None=Field(default=None,max_length=254)
 delivery_address:str|None=Field(default=None,max_length=1000)
 delivery_instructions:str|None=Field(default=None,max_length=1000)
 is_anonymous:bool=False
def audit(db,event,entity,entity_id,details="{}"): db.add(AuditEvent(event_type=event,entity_type=entity,entity_id=entity_id,details=details))
def seed_data(db):
 if db.scalar(select(Product.id).limit(1)): return
 ps=[
 Product(sku="FRESH-BAN-001",name="Fresh Bananas",description="Ripe, locally sourced bananas.",category="Fresh produce",price=Decimal("1200"),stock_quantity=45,color="#e5c65b"),
 Product(sku="PAN-MIL-001",name="Whole Milk 1L",description="Chilled whole milk, one litre.",category="Dairy",price=Decimal("1500"),stock_quantity=32,color="#e9e7df"),
 Product(sku="PAN-BRE-001",name="Wholegrain Bread",description="Freshly baked wholegrain loaf.",category="Bakery",price=Decimal("1800"),stock_quantity=24,color="#b87945"),
 Product(sku="DRK-JUI-001",name="Orange Juice",description="Bright citrus juice, one litre.",category="Drinks",price=Decimal("2300"),stock_quantity=18,color="#e88b37"),
 Product(sku="PAN-RIC-001",name="Rice 2kg",description="Long-grain rice, two kilograms.",category="Pantry",price=Decimal("4200"),stock_quantity=40,color="#d9d2b9"),
 Product(sku="HOM-SOA-001",name="Gentle Hand Soap",description="Everyday hand soap.",category="Home care",price=Decimal("2500"),stock_quantity=27,color="#78a8a0"),
 Product(sku="SNK-COO-001",name="Oat Cookies",description="Crunchy oat cookies for sharing.",category="Snacks",price=Decimal("1700"),stock_quantity=36,color="#c88c55"),
 Product(sku="DRK-TEA-001",name="Rwandan Black Tea",description="Aromatic black tea grown in Rwanda.",category="Drinks",price=Decimal("3200"),stock_quantity=21,color="#9c7658")]
 fs=[Fixture(code="AISLE-FRESH",name="Fresh produce shelf",x=-3.1,z=-2.1),Fixture(code="AISLE-DAIRY",name="Dairy and bakery shelf",x=-3.1,z=1.5),Fixture(code="AISLE-PANTRY",name="Pantry shelf",x=0,z=-2.1),Fixture(code="AISLE-DRINKS",name="Drinks shelf",x=0,z=1.5)]
 db.add_all(ps+fs); db.flush()
 for i,p in enumerate(ps): db.add(ProductPlacement(product_id=p.id,fixture_id=fs[i%4].id,shelf_level=(i//4)%3,slot=i%4))
 db.commit()
def cart_payload(db,session_id):
 rows=list(db.scalars(select(CartItem).where(CartItem.session_id==session_id))); items=[]; subtotal=Decimal("0"); count=0
 for r in rows:
  p=r.product
  if not p.active: continue
  line=p.price*r.quantity; subtotal+=line; count+=r.quantity
  items.append({"product_id":p.id,"sku":p.sku,"name":p.name,"price":str(p.price),"currency":p.currency,"quantity":r.quantity,"line_total":str(line),"stock_quantity":p.stock_quantity})
 return {"session_id":session_id,"items":items,"item_count":count,"subtotal":str(subtotal),"currency":"RWF"}
def order_payload(o):
 return {"id":o.id,"status":o.status,"payment_status":o.payment_status,"subtotal":str(o.subtotal),"currency":o.currency,"created_at":o.created_at.isoformat(),"customer_name":o.customer_name,"customer_phone":o.customer_phone,"customer_email":o.customer_email,"delivery_address":o.delivery_address,"delivery_instructions":o.delivery_instructions,"is_anonymous":o.is_anonymous,
 "items":[{"product_id":i.product_id,"sku":i.sku,"name":i.product_name,"unit_price":str(i.unit_price),"quantity":i.quantity} for i in o.items],
 "payment":{"mode":"sandbox","next_action":f"/api/v1/payments/{o.id}/simulate-success"}}
def ensure_product_rich_columns():
 from sqlalchemy import inspect, text
 inspector=inspect(engine)
 existing={column["name"] for column in inspector.get_columns("products")} if inspector.has_table("products") else set()
 columns={"brand":"VARCHAR(120) NOT NULL DEFAULT ''","synonyms":"TEXT NOT NULL DEFAULT ''","unit":"VARCHAR(40) NOT NULL DEFAULT 'each'","ingredients":"TEXT NOT NULL DEFAULT ''","allergens":"TEXT NOT NULL DEFAULT ''","nutrition":"TEXT NOT NULL DEFAULT ''","gallery_json":"TEXT NOT NULL DEFAULT '[]'","video_url":"VARCHAR(500)","discontinued":"BOOLEAN NOT NULL DEFAULT 0","popularity":"INTEGER NOT NULL DEFAULT 0","tenant_id":"VARCHAR(36)"}
 with engine.begin() as connection:
  for name,definition in columns.items():
   if name not in existing: connection.execute(text(f"ALTER TABLE products ADD COLUMN {name} {definition}"))
def ensure_account_store_columns():
 from sqlalchemy import inspect, text
 inspector=inspect(engine)
 existing={column["name"] for column in inspector.get_columns("accounts")} if inspector.has_table("accounts") else set()
 with engine.begin() as connection:
  if "store_id" not in existing: connection.execute(text("ALTER TABLE accounts ADD COLUMN store_id VARCHAR(36)"))

def ensure_order_customer_columns():
 from sqlalchemy import inspect, text
 inspector=inspect(engine)
 existing={column["name"] for column in inspector.get_columns("orders")} if inspector.has_table("orders") else set()
 additions={"customer_name":"VARCHAR(180)","customer_phone":"VARCHAR(40) NOT NULL DEFAULT ''","customer_email":"VARCHAR(254)","delivery_address":"TEXT","delivery_instructions":"TEXT","is_anonymous":"BOOLEAN NOT NULL DEFAULT 0"}
 with engine.begin() as connection:
  for name,sql_type in additions.items():
   if name not in existing: connection.execute(text(f"ALTER TABLE orders ADD COLUMN {name} {sql_type}"))
@asynccontextmanager
async def lifespan(_):
 Base.metadata.create_all(bind=engine)
 ensure_order_customer_columns()
 ensure_account_store_columns()
 ensure_product_rich_columns()
 ensure_tenant_columns()
 with SessionLocal() as db:
  seed_data(db)
  seed_platform_admin(db)
 yield
app=FastAPI(title="Virtual Store Commerce API",version="0.2.0",description="Shared catalogue, 3D layout, cart, orders and sandbox payments.",lifespan=lifespan)
app.add_middleware(CORSMiddleware,allow_origins=os.getenv("CORS_ORIGINS","http://localhost:3000").split(","),allow_credentials=True,allow_methods=["GET","POST","PUT","PATCH","DELETE","OPTIONS"],allow_headers=["Content-Type","Authorization","Idempotency-Key","X-Admin-Key"])
_auth_attempts={}
@app.middleware("http")
async def security_middleware(request:Request,call_next):
 path=request.url.path
 if path in ("/api/v1/auth/login","/api/v1/auth/register","/api/v1/auth/forgot-password","/api/v1/auth/reset-password"):
  now=time.time();key=(request.client.host if request.client else "unknown",path)
  recent=[stamp for stamp in _auth_attempts.get(key,[]) if now-stamp<300]
  if len(recent)>=12:
   from fastapi.responses import JSONResponse
   return JSONResponse(status_code=429,content={"detail":"Too many authentication attempts. Please try again later."},headers={"Retry-After":"300"})
  recent.append(now);_auth_attempts[key]=recent
 cookie=request.cookies.get("vsc_session")
 csrf=request.cookies.get("vsc_csrf")
 if cookie and not request.headers.get("authorization") and not path.startswith("/api/v1/auth/"):
  if request.method not in ("GET","HEAD","OPTIONS"):
   header=request.headers.get("x-csrf-token")
   if not csrf or not header or not hmac.compare_digest(csrf,header):
    from fastapi.responses import JSONResponse
    return JSONResponse(status_code=403,content={"detail":"CSRF token missing or invalid"})
  if not request.headers.get("authorization"):
   request.scope["headers"].append((b"authorization",("Bearer "+cookie).encode()))
 scope_token=tenant_scope.set("__public__")
 try:
  auth_header=request.headers.get("authorization")
  token_value=auth_header or cookie
  if token_value:
   with SessionLocal() as auth_db:
    try:account=account_from_token(token_value if token_value.startswith("Bearer ") else "Bearer "+token_value,auth_db)
    except HTTPException:account=None
   if account:
    tenant_scope.set(None if account.role=="platform_admin" else (account.store_id or "__public__"))
  elif request.headers.get("x-store-id"):
   store_id=request.headers.get("x-store-id","")
   with SessionLocal() as store_db:
    store=store_db.get(StoreTenant,store_id)
    if not store or store.status!="approved":
     from fastapi.responses import JSONResponse
     return JSONResponse(status_code=404,content={"detail":"Storefront not found or not approved"})
   tenant_scope.set(store_id)
  response=await call_next(request)
  return response
 finally:
  tenant_scope.reset(scope_token)

@app.get("/health",tags=["Operations"])
def health(): return {"status":"ok","service":"virtual-store-commerce-api","database":"connected"}
@app.get("/api/v1/products",tags=["Products"])
def products(
 q:str|None=Query(default=None,max_length=100),
 category:str|None=Query(default=None,max_length=80),
 min_price:Decimal|None=Query(default=None,ge=0),
 max_price:Decimal|None=Query(default=None,ge=0),
 in_stock:bool|None=Query(default=None),
 brand:str|None=Query(default=None,max_length=120),
 sort:str=Query(default="relevance",pattern=r"^(relevance|price_asc|price_desc|newest|name|popularity)$"),
 limit:int=Query(default=60,ge=1,le=100),
 offset:int=Query(default=0,ge=0),
 db:Session=Depends(get_db)):
 import difflib
 if min_price is not None and max_price is not None and min_price>max_price:
  raise HTTPException(422,"min_price must be less than or equal to max_price")
 ps=list(db.scalars(select(Product).where(Product.active.is_(True))))
 if category: ps=[p for p in ps if p.category.casefold()==category.casefold()]
 if min_price is not None: ps=[p for p in ps if p.price>=min_price]
 if max_price is not None: ps=[p for p in ps if p.price<=max_price]
 if in_stock is not None: ps=[p for p in ps if (p.stock_quantity>0)==in_stock]
 if brand: ps=[p for p in ps if p.brand.casefold()==brand.casefold()]
 query_text=(q or "").strip().casefold()
 scored=[]
 synonyms={"strawberry":"strawberries","strawberries":"strawberry","soda":"drinks","beverage":"drinks","beverages":"drinks","milk":"dairy","bread":"bakery","soap":"home care","tea":"rwandan black tea"}
 if query_text:
  terms=query_text.split()
  for p in ps:
   fields=[p.name,p.sku,p.category,p.description,p.brand,p.synonyms]
   haystack=" ".join(fields).casefold()
   tokens=set(haystack.replace("-"," ").replace("/"," ").split())
   score=0
   if query_text in haystack: score+=10
   if query_text in p.name.casefold(): score+=12
   if query_text in p.sku.casefold(): score+=15
   if query_text in p.category.casefold(): score+=7
   for term in terms:
    if term in tokens: score+=5
    synonym=synonyms.get(term)
    if synonym and synonym in haystack: score+=4
    if len(term)>=5 and any(difflib.SequenceMatcher(None,term,token).ratio()>=0.78 for token in tokens): score+=2
   if score: scored.append((score,p))
  scored.sort(key=lambda item:(-item[0],item[1].name.casefold()))
  ps=[p for _,p in scored]
 if sort=="price_asc": ps.sort(key=lambda p:(p.price,p.name.casefold()))
 elif sort=="price_desc": ps.sort(key=lambda p:(-p.price,p.name.casefold()))
 elif sort=="newest": ps.sort(key=lambda p:p.created_at,reverse=True)
 elif sort=="name": ps.sort(key=lambda p:p.name.casefold())
 elif sort=="popularity": ps.sort(key=lambda p:(-p.popularity,p.name.casefold()))
 elif not query_text: ps.sort(key=lambda p:(p.category.casefold(),p.name.casefold()))
 total=len(ps)
 page=ps[offset:offset+limit]
 if query_text:
  db.add(SearchEvent(query=query_text[:180],result_count=total))
  db.commit()
 return {"items":[ProductOut.model_validate(p).model_dump(mode="json") for p in page],"total":total,"limit":limit,"offset":offset,"alternatives":[ProductOut.model_validate(p).model_dump(mode="json") for p in (list(db.scalars(select(Product).where(Product.active.is_(True)).order_by(Product.popularity.desc()).limit(4))) if total==0 else [])]}
@app.get("/api/v1/products/{product_id}",response_model=ProductOut,tags=["Products"])
def product_detail(product_id:str,db:Session=Depends(get_db)):
 p=db.get(Product,product_id)
 if not p or not p.active: raise HTTPException(404,"Product not found")
 return p
@app.get("/api/v1/categories",tags=["Products"])
def categories(db:Session=Depends(get_db)): return {"items":list(db.scalars(select(Product.category).where(Product.active.is_(True)).distinct().order_by(Product.category)))}
@app.get("/api/v1/store-layout",tags=["3D Store"])
def layout(db:Session=Depends(get_db)):
 fs=list(db.scalars(select(Fixture).order_by(Fixture.code))); out=[]
 for f in fs:
  ps=list(db.scalars(select(ProductPlacement).where(ProductPlacement.fixture_id==f.id)))
  out.append({"id":f.id,"code":f.code,"name":f.name,"kind":f.kind,"position":[float(f.x),float(f.y),float(f.z)],
   "products":[{"placement_id":p.id,"product_id":p.product.id,"sku":p.product.sku,"name":p.product.name,"price":str(p.product.price),"color":p.product.color,"image_url":p.product.image_url,"stock_quantity":p.product.stock_quantity,"shelf_level":p.shelf_level,"slot":p.slot} for p in ps if p.product.active]})
 return {"items":out,"total":len(out)}
@app.get("/api/v1/cart",tags=["Cart"])
def get_cart(session_id:str=Query(min_length=8,max_length=100),db:Session=Depends(get_db)): return cart_payload(db,session_id)
@app.post("/api/v1/cart/items",tags=["Cart"])
def add_cart(payload:CartItemInput,session_id:str=Query(min_length=8,max_length=100),db:Session=Depends(get_db)):
 p=db.get(Product,payload.product_id)
 if not p or not p.active: raise HTTPException(404,"Product not found")
 row=db.scalar(select(CartItem).where(CartItem.session_id==session_id,CartItem.product_id==p.id)); qty=payload.quantity+(row.quantity if row else 0)
 if qty>p.stock_quantity: raise HTTPException(409,f"Only {p.stock_quantity} units are currently in stock")
 if row: row.quantity=qty
 else: db.add(CartItem(session_id=session_id,product_id=p.id,quantity=qty))
 db.commit(); return cart_payload(db,session_id)
@app.delete("/api/v1/cart/items/{product_id}",tags=["Cart"])
def remove_cart(product_id:str,session_id:str=Query(min_length=8,max_length=100),db:Session=Depends(get_db)):
 row=db.scalar(select(CartItem).where(CartItem.session_id==session_id,CartItem.product_id==product_id))
 if row: db.delete(row); db.commit()
 return cart_payload(db,session_id)
@app.post("/api/v1/checkout",tags=["Orders"])
def checkout(payload:CheckoutInput,idempotency_key:str=Header(alias="Idempotency-Key",min_length=8,max_length=160),db:Session=Depends(get_db)):
 if not payload.is_anonymous and (not payload.customer_name or not payload.customer_name.strip() or not payload.delivery_address or not payload.delivery_address.strip()): raise HTTPException(422,"Name and delivery address are required unless you choose anonymous checkout")
 old=db.scalar(select(Order).where(Order.idempotency_key==idempotency_key))
 if old: return order_payload(old)
 cart=list(db.scalars(select(CartItem).where(CartItem.session_id==payload.session_id)))
 if not cart: raise HTTPException(400,"Your cart is empty")
 basket=[]; subtotal=Decimal("0")
 for row in cart:
  p=db.scalar(select(Product).where(Product.id==row.product_id).with_for_update())
  if not p or not p.active: raise HTTPException(409,"A product in your cart is no longer available")
  if row.quantity>p.stock_quantity: raise HTTPException(409,f"Insufficient stock for {p.name}")
  basket.append((p,row.quantity)); subtotal+=p.price*row.quantity
 order=Order(session_id=payload.session_id,idempotency_key=idempotency_key,subtotal=subtotal,currency="RWF",customer_name=(payload.customer_name.strip() if payload.customer_name else None),customer_phone=payload.customer_phone.strip(),customer_email=(payload.customer_email.strip() if payload.customer_email else None),delivery_address=(payload.delivery_address.strip() if payload.delivery_address else None),delivery_instructions=(payload.delivery_instructions.strip() if payload.delivery_instructions else None),is_anonymous=payload.is_anonymous); db.add(order); db.flush()
 for p,qty in basket:
  p.stock_quantity-=qty; db.add(OrderItem(order_id=order.id,product_id=p.id,sku=p.sku,product_name=p.name,unit_price=p.price,quantity=qty))
  audit(db,"INVENTORY_RESERVED","product",p.id,f'{{"quantity":{qty},"order_id":"{order.id}"}}')
 for row in cart: db.delete(row)
 audit(db,"ORDER_CREATED","order",order.id,f'{{"subtotal":"{subtotal}","status":"pending_payment"}}')
 try: db.commit()
 except IntegrityError:
  db.rollback(); old=db.scalar(select(Order).where(Order.idempotency_key==idempotency_key))
  if old: return order_payload(old)
  raise HTTPException(409,"Checkout conflict; retry with the same idempotency key")
 db.refresh(order); return order_payload(order)
@app.get("/api/v1/orders/{order_id}",tags=["Orders"])
def get_order(order_id:str,session_id:str=Query(min_length=8,max_length=100),db:Session=Depends(get_db)):
 o=db.get(Order,order_id)
 if not o or o.session_id!=session_id: raise HTTPException(404,"Order not found")
 return order_payload(o)
@app.get("/api/v1/orders",tags=["Orders"])
def list_orders(session_id:str=Query(min_length=8,max_length=100),db:Session=Depends(get_db)):
 os_=list(db.scalars(select(Order).where(Order.session_id==session_id).order_by(Order.created_at.desc()))); return {"items":[order_payload(o) for o in os_],"total":len(os_)}
@app.post("/api/v1/payments/{order_id}/simulate-success",tags=["Sandbox Payments"])
def simulate_payment(order_id:str,db:Session=Depends(get_db)):
 o=db.scalar(select(Order).where(Order.id==order_id).with_for_update())
 if not o: raise HTTPException(404,"Order not found")
 if o.payment_status=="paid": return {"order_id":o.id,"payment_status":"paid","message":"Payment already confirmed; no duplicate action taken"}
 if o.status!="pending_payment": raise HTTPException(409,"This order can no longer be paid")
 o.payment_status="paid"; o.status="confirmed"; audit(db,"SANDBOX_PAYMENT_SUCCEEDED","order",o.id,'{"provider":"local-sandbox"}'); db.commit()
 return {"order_id":o.id,"payment_status":o.payment_status,"order_status":o.status,"mode":"sandbox"}
@app.post("/api/v1/orders/{order_id}/cancel",tags=["Orders"])
def cancel_order(order_id:str,db:Session=Depends(get_db)):
 o=db.scalar(select(Order).where(Order.id==order_id).with_for_update())
 if not o: raise HTTPException(404,"Order not found")
 if o.status=="cancelled": return {"order_id":o.id,"status":"cancelled","message":"Already cancelled"}
 if o.payment_status=="paid": raise HTTPException(409,"Paid orders need a refund workflow")
 for item in o.items:
  p=db.get(Product,item.product_id)
  if p: p.stock_quantity+=item.quantity
 o.status="cancelled"; audit(db,"ORDER_CANCELLED_STOCK_RELEASED","order",o.id); db.commit()
 return {"order_id":o.id,"status":o.status}
def require_admin(request:Request,x_admin_key:str|None=Header(default=None,alias="X-Admin-Key"),authorization:str|None=Header(default=None),session_cookie:str|None=Cookie(default=None,alias="vsc_session"),csrf_cookie:str|None=Cookie(default=None,alias="vsc_csrf"),csrf_header:str|None=Header(default=None,alias="X-CSRF-Token"),db:Session=Depends(get_db)):
 if os.getenv("APP_ENV","development").lower()!="production" and x_admin_key and hmac.compare_digest(x_admin_key,os.getenv("ADMIN_API_KEY","local-dev-admin-change-me")): return True
 if (authorization and authorization.startswith("Bearer ")) or session_cookie:
  if not authorization and request.method not in ("GET","HEAD","OPTIONS"):
   if not csrf_cookie or not csrf_header or not hmac.compare_digest(csrf_cookie,csrf_header): raise HTTPException(403,"CSRF token missing or invalid")
  account=account_from_token(authorization or ("Bearer "+session_cookie if session_cookie else None),db)
  if account.role in ("store_owner","store_manager","store_staff"):
   if account.store_id:
    tenant=db.get(StoreTenant,account.store_id)
    if not tenant or tenant.status!="approved": raise HTTPException(403,"Store access is unavailable until the platform approves this store")
   path=request.url.path;method=request.method
   if account.role=="store_manager" and (path.startswith("/api/v1/admin/staff") or path.endswith("/refund")):
    raise HTTPException(403,"Store manager role cannot administer staff accounts or approve refunds")
   if account.role=="store_staff":
    safe_read=method=="GET" and (path.endswith("/summary") or path.endswith("/orders") or path.endswith("/products") or path.endswith("/audit-events"))
    fulfilment=method=="POST" and path.startswith("/api/v1/admin/orders/") and path.endswith("/status")
    if not (safe_read or fulfilment):raise HTTPException(403,"Store staff role does not have permission for this action")
   return True
 raise HTTPException(401,"Sign in with an authorized store or platform account, or provide a valid development admin key")
@app.post("/api/v1/admin/products",response_model=ProductOut,status_code=status.HTTP_201_CREATED,tags=["Retailer Admin"],dependencies=[Depends(require_admin)])
def create_product(payload:ProductCreate,db:Session=Depends(get_db)):
 p=Product(**payload.model_dump()); db.add(p)
 try:
  db.flush()
  fixtures=list(db.scalars(select(Fixture).order_by(Fixture.code)))
  if fixtures:
   all_placements=list(db.scalars(select(ProductPlacement.id))); fixture=fixtures[len(all_placements)%len(fixtures)]; placements=list(db.scalars(select(ProductPlacement).where(ProductPlacement.fixture_id==fixture.id))); slot=len(placements)
   db.add(ProductPlacement(product_id=p.id,fixture_id=fixture.id,shelf_level=(slot//6)%3,slot=slot%6))
  audit(db,"PRODUCT_CREATED","product",p.id,f'{{"sku":"{p.sku}"}}'); db.commit(); db.refresh(p)
 except IntegrityError: db.rollback(); raise HTTPException(409,"That SKU already exists")
 return p
@app.patch("/api/v1/admin/products/{product_id}",response_model=ProductOut,tags=["Retailer Admin"],dependencies=[Depends(require_admin)])
def update_product(product_id:str,payload:ProductPatch,db:Session=Depends(get_db)):
 p=db.get(Product,product_id)
 if not p: raise HTTPException(404,"Product not found")
 changes=payload.model_dump(exclude_unset=True)
 for field,value in changes.items(): setattr(p,field,value)
 audit(db,"PRODUCT_UPDATED","product",p.id,str(changes)); db.commit(); db.refresh(p); return p
@app.post("/api/v1/admin/fixtures",status_code=status.HTTP_201_CREATED,tags=["Retailer Admin"],dependencies=[Depends(require_admin)])
def create_fixture(payload:FixtureCreate,db:Session=Depends(get_db)):
 f=Fixture(**payload.model_dump()); db.add(f)
 try:
  db.flush(); audit(db,"FIXTURE_CREATED","fixture",f.id,f'{{"code":"{f.code}","kind":"{f.kind}"}}'); db.commit(); db.refresh(f)
 except IntegrityError:
  db.rollback(); raise HTTPException(409,"That fixture code already exists")
 return {"id":f.id,"code":f.code,"name":f.name,"kind":f.kind,"position":[float(f.x),float(f.y),float(f.z)],"products":[]}
@app.post("/api/v1/admin/fixtures/{fixture_id}/items",status_code=status.HTTP_201_CREATED,tags=["Retailer Admin"],dependencies=[Depends(require_admin)])
def place_fixture_item(fixture_id:str,payload:PlacementCreate,db:Session=Depends(get_db)):
 f=db.get(Fixture,fixture_id); p=db.get(Product,payload.product_id)
 if not f: raise HTTPException(404,"Fixture not found")
 if not p or not p.active: raise HTTPException(404,"Active product not found")
 row=ProductPlacement(product_id=p.id,fixture_id=f.id,shelf_level=payload.shelf_level,slot=payload.slot)
 db.add(row)
 try:
  db.flush(); audit(db,"PRODUCT_PLACED_IN_FIXTURE","placement",row.id,f'{{"fixture_id":"{f.id}","product_id":"{p.id}","shelf_level":{row.shelf_level},"slot":{row.slot}}}'); db.commit(); db.refresh(row)
 except IntegrityError:
  db.rollback(); raise HTTPException(409,"That product already occupies this exact fixture slot")
 return {"id":row.id,"fixture_id":f.id,"product_id":p.id,"shelf_level":row.shelf_level,"slot":row.slot}
@app.delete("/api/v1/admin/fixtures/{fixture_id}/items/{placement_id}",tags=["Retailer Admin"],dependencies=[Depends(require_admin)])
def remove_fixture_item(fixture_id:str,placement_id:str,db:Session=Depends(get_db)):
 row=db.get(ProductPlacement,placement_id)
 if not row or row.fixture_id!=fixture_id: raise HTTPException(404,"Placement not found")
 audit(db,"PRODUCT_REMOVED_FROM_FIXTURE","placement",row.id,f'{{"fixture_id":"{fixture_id}","product_id":"{row.product_id}"}}'); db.delete(row); db.commit()
 return {"removed":True,"placement_id":placement_id}
@app.get("/api/v1/admin/summary",tags=["Retailer Admin"],dependencies=[Depends(require_admin)])
def admin_summary(db:Session=Depends(get_db)):
 ps=list(db.scalars(select(Product))); orders=list(db.scalars(select(Order)))
 return {"product_count":len(ps),"active_product_count":sum(p.active for p in ps),"units_in_stock":sum(p.stock_quantity for p in ps),"order_count":len(orders),"pending_payment_count":sum(o.status=="pending_payment" for o in orders),"confirmed_order_count":sum(o.status=="confirmed" for o in orders)}
@app.get("/api/v1/admin/audit-events",tags=["Retailer Admin"],dependencies=[Depends(require_admin)])
def audit_events(limit:int=Query(default=50,ge=1,le=200),db:Session=Depends(get_db)):
 es=list(db.scalars(select(AuditEvent).order_by(AuditEvent.created_at.desc()).limit(limit)))
 return {"items":[{"id":e.id,"event_type":e.event_type,"entity_type":e.entity_type,"entity_id":e.entity_id,"details":e.details,"created_at":e.created_at.isoformat()} for e in es],"total":len(es)}


# Advanced retailer operations. All writes use the same canonical product/order records.
class CsvImportInput(BaseModel):
 csv_text:str=Field(min_length=1,max_length=2_000_000)
class PromotionInput(BaseModel):
 code:str=Field(min_length=3,max_length=40,pattern=r"^[A-Za-z0-9_-]+$")
 discount_percent:int=Field(ge=1,le=90); min_subtotal:Decimal=Field(default=Decimal("0"),ge=0)
class SupplierInput(BaseModel):
 name:str=Field(min_length=2,max_length=180); contact_name:str|None=None; phone:str|None=None; email:str|None=None
class PurchaseOrderInput(BaseModel):
 supplier_id:str; product_id:str; quantity:int=Field(ge=1,le=100000); unit_cost:Decimal=Field(gt=0)
class BranchInput(BaseModel):
 code:str=Field(min_length=2,max_length=40,pattern=r"^[A-Za-z0-9_-]+$"); name:str=Field(min_length=2,max_length=180); address:str=Field(default="",max_length=500)
class BranchStockInput(BaseModel):
 product_id:str; quantity:int=Field(ge=0,le=1000000)
class StaffInput(BaseModel):
 name:str=Field(min_length=2,max_length=180); email:str=Field(min_length=5,max_length=254); role:str=Field(default="viewer",pattern=r"^(viewer|inventory|manager)$")
class ReturnInput(BaseModel):
 order_id:str; reason:str=Field(min_length=5,max_length=500)
@app.post("/api/v1/admin/products/import-csv",tags=["Retailer Admin"],dependencies=[Depends(require_admin)])
def import_products_csv(payload:CsvImportInput,db:Session=Depends(get_db)):
 import csv,io
 reader=csv.DictReader(io.StringIO(payload.csv_text))
 required={"sku","name","category","price","stock_quantity"}
 if not reader.fieldnames or not required.issubset(set(reader.fieldnames)): raise HTTPException(422,"CSV headers must include sku,name,category,price,stock_quantity; description and color are optional")
 created=updated=0; errors=[]
 for line,row in enumerate(reader,start=2):
  try:
   sku=(row.get("sku") or "").strip(); name=(row.get("name") or "").strip()
   if len(sku)<2 or len(name)<2: raise ValueError("sku and name are required")
   price=Decimal(row["price"]); stock=int(row["stock_quantity"])
   if price<=0 or stock<0: raise ValueError("price must be positive and stock cannot be negative")
   p=db.scalar(select(Product).where(Product.sku==sku))
   if p:
    p.name=name;p.category=(row.get("category") or "General").strip();p.price=price;p.stock_quantity=stock;p.description=(row.get("description") or "").strip();p.color=(row.get("color") or p.color).strip();updated+=1
   else:
    p=Product(sku=sku,name=name,category=(row.get("category") or "General").strip(),price=price,stock_quantity=stock,description=(row.get("description") or "").strip(),color=(row.get("color") or "#799d79").strip());db.add(p);created+=1
  except (ValueError,KeyError,InvalidOperation) as exc:
   errors.append({"line":line,"error":str(exc)})
  except IntegrityError:
   db.rollback();errors.append({"line":line,"error":"SKU conflicts with an existing record"})
 db.commit();audit(db,"PRODUCTS_CSV_IMPORTED","catalogue","csv-import",str({"created":created,"updated":updated,"errors":len(errors)}));db.commit()
 return {"created":created,"updated":updated,"error_count":len(errors),"errors":errors[:100]}
@app.post("/api/v1/admin/promotions",tags=["Retailer Admin"],dependencies=[Depends(require_admin)])
def create_promotion(payload:PromotionInput,db:Session=Depends(get_db)):
 code=payload.code.upper()
 if db.scalar(select(Promotion.id).where(Promotion.code==code)): raise HTTPException(409,"Promotion code already exists")
 p=Promotion(code=code,discount_percent=payload.discount_percent,min_subtotal=payload.min_subtotal);db.add(p);db.commit();db.refresh(p)
 audit(db,"PROMOTION_CREATED","promotion",p.id);db.commit()
 return {"id":p.id,"code":p.code,"discount_percent":p.discount_percent,"min_subtotal":str(p.min_subtotal),"active":p.active}
@app.get("/api/v1/promotions/{code}",tags=["Promotions"])
def validate_promotion(code:str,subtotal:Decimal=Query(default=Decimal("0"),ge=0),db:Session=Depends(get_db)):
 p=db.scalar(select(Promotion).where(Promotion.code==code.upper(),Promotion.active.is_(True)))
 if not p: raise HTTPException(404,"Promotion code is invalid or inactive")
 if subtotal<p.min_subtotal: raise HTTPException(422,f"Minimum basket subtotal is {p.min_subtotal}")
 discount=(subtotal*Decimal(p.discount_percent)/Decimal(100)).quantize(Decimal("0.01"))
 return {"code":p.code,"discount_percent":p.discount_percent,"subtotal":str(subtotal),"discount":str(discount),"total":str(subtotal-discount)}
@app.post("/api/v1/admin/suppliers",tags=["Retailer Admin"],dependencies=[Depends(require_admin)])
def create_supplier(payload:SupplierInput,db:Session=Depends(get_db)):
 s=Supplier(**payload.model_dump());db.add(s);db.commit();db.refresh(s);audit(db,"SUPPLIER_CREATED","supplier",s.id);db.commit()
 return {"id":s.id,"name":s.name,"contact_name":s.contact_name,"phone":s.phone,"email":s.email,"active":s.active}
@app.get("/api/v1/admin/suppliers",tags=["Retailer Admin"],dependencies=[Depends(require_admin)])
def list_suppliers(db:Session=Depends(get_db)):
 return {"items":[{"id":s.id,"name":s.name,"contact_name":s.contact_name,"phone":s.phone,"email":s.email,"active":s.active} for s in db.scalars(select(Supplier).order_by(Supplier.name))]}
@app.post("/api/v1/admin/purchase-orders",tags=["Retailer Admin"],dependencies=[Depends(require_admin)])
def create_purchase_order(payload:PurchaseOrderInput,db:Session=Depends(get_db)):
 if not db.get(Supplier,payload.supplier_id): raise HTTPException(404,"Supplier not found")
 if not db.get(Product,payload.product_id): raise HTTPException(404,"Product not found")
 po=PurchaseOrder(**payload.model_dump());db.add(po);db.commit();db.refresh(po);audit(db,"PURCHASE_ORDER_CREATED","purchase_order",po.id);db.commit()
 return {"id":po.id,"supplier_id":po.supplier_id,"product_id":po.product_id,"quantity":po.quantity,"unit_cost":str(po.unit_cost),"status":po.status}
@app.post("/api/v1/admin/purchase-orders/{purchase_order_id}/receive",tags=["Retailer Admin"],dependencies=[Depends(require_admin)])
def receive_purchase_order(purchase_order_id:str,db:Session=Depends(get_db)):
 po=db.get(PurchaseOrder,purchase_order_id)
 if not po: raise HTTPException(404,"Purchase order not found")
 if po.status=="received": raise HTTPException(409,"Purchase order was already received")
 product=db.get(Product,po.product_id);product.stock_quantity+=po.quantity;po.status="received";audit(db,"PURCHASE_ORDER_RECEIVED","purchase_order",po.id,str({"quantity":po.quantity}));db.commit()
 return {"id":po.id,"status":po.status,"new_stock_quantity":product.stock_quantity}
@app.post("/api/v1/admin/branches",tags=["Retailer Admin"],dependencies=[Depends(require_admin)])
def create_branch(payload:BranchInput,db:Session=Depends(get_db)):
 b=StoreBranch(**payload.model_dump());db.add(b)
 try: db.commit()
 except IntegrityError: db.rollback();raise HTTPException(409,"Branch code already exists")
 db.refresh(b);return {"id":b.id,"code":b.code,"name":b.name,"address":b.address,"active":b.active}
@app.get("/api/v1/admin/branches",tags=["Retailer Admin"],dependencies=[Depends(require_admin)])
def list_branches(db:Session=Depends(get_db)):
 return {"items":[{"id":b.id,"code":b.code,"name":b.name,"address":b.address,"active":b.active} for b in db.scalars(select(StoreBranch).order_by(StoreBranch.name))]}
@app.put("/api/v1/admin/branches/{branch_id}/inventory",tags=["Retailer Admin"],dependencies=[Depends(require_admin)])
def set_branch_inventory(branch_id:str,payload:BranchStockInput,db:Session=Depends(get_db)):
 if not db.get(StoreBranch,branch_id):raise HTTPException(404,"Branch not found")
 if not db.get(Product,payload.product_id):raise HTTPException(404,"Product not found")
 row=db.scalar(select(BranchInventory).where(BranchInventory.branch_id==branch_id,BranchInventory.product_id==payload.product_id))
 if row:row.quantity=payload.quantity
 else:row=BranchInventory(branch_id=branch_id,product_id=payload.product_id,quantity=payload.quantity);db.add(row)
 db.commit();return {"branch_id":branch_id,"product_id":payload.product_id,"quantity":payload.quantity}
@app.get("/api/v1/admin/branches/{branch_id}/inventory",tags=["Retailer Admin"],dependencies=[Depends(require_admin)])
def get_branch_inventory(branch_id:str,db:Session=Depends(get_db)):
 if not db.get(StoreBranch,branch_id):raise HTTPException(404,"Branch not found")
 rows=list(db.scalars(select(BranchInventory).where(BranchInventory.branch_id==branch_id)))
 return {"items":[{"product_id":r.product_id,"name":db.get(Product,r.product_id).name,"quantity":r.quantity} for r in rows]}
@app.post("/api/v1/admin/staff",tags=["Retailer Admin"],dependencies=[Depends(require_admin)])
def add_staff(payload:StaffInput,db:Session=Depends(get_db)):
 s=StaffMember(name=payload.name,email=payload.email.lower(),role=payload.role)
 db.add(s)
 try:db.commit()
 except IntegrityError:db.rollback();raise HTTPException(409,"Staff email already exists")
 db.refresh(s);audit(db,"STAFF_MEMBER_CREATED","staff_member",s.id);db.commit()
 return {"id":s.id,"name":s.name,"email":s.email,"role":s.role,"active":s.active}
@app.get("/api/v1/admin/staff",tags=["Retailer Admin"],dependencies=[Depends(require_admin)])
def list_staff(db:Session=Depends(get_db)):
 return {"items":[{"id":s.id,"name":s.name,"email":s.email,"role":s.role,"active":s.active} for s in db.scalars(select(StaffMember).order_by(StaffMember.name))]}
@app.post("/api/v1/admin/returns",tags=["Retailer Admin"],dependencies=[Depends(require_admin)])
def request_return(payload:ReturnInput,db:Session=Depends(get_db)):
 o=db.get(Order,payload.order_id)
 if not o:raise HTTPException(404,"Order not found")
 if o.payment_status!="paid":raise HTTPException(409,"Only paid orders can enter the refund workflow")
 if o.status=="cancelled":raise HTTPException(409,"Cancelled orders cannot be returned")
 existing=db.scalar(select(ReturnRequest.id).where(ReturnRequest.order_id==o.id,ReturnRequest.status.in_(["requested","approved","refunded"])))
 if existing:raise HTTPException(409,"A return/refund request already exists for this order")
 r=ReturnRequest(order_id=o.id,reason=payload.reason,refund_amount=o.subtotal);db.add(r);db.commit();db.refresh(r);audit(db,"RETURN_REQUESTED","return",r.id);db.commit()
 return {"id":r.id,"order_id":r.order_id,"reason":r.reason,"status":r.status,"refund_amount":str(r.refund_amount)}
@app.get("/api/v1/admin/returns",tags=["Retailer Admin"],dependencies=[Depends(require_admin)])
def list_returns(db:Session=Depends(get_db)):
 return {"items":[{"id":r.id,"order_id":r.order_id,"reason":r.reason,"status":r.status,"refund_amount":str(r.refund_amount),"created_at":r.created_at.isoformat()} for r in db.scalars(select(ReturnRequest).order_by(ReturnRequest.created_at.desc()))]}
@app.post("/api/v1/admin/returns/{return_id}/refund",tags=["Retailer Admin"],dependencies=[Depends(require_admin)])
def approve_refund(return_id:str,db:Session=Depends(get_db)):
 r=db.get(ReturnRequest,return_id)
 if not r:raise HTTPException(404,"Return request not found")
 if r.status=="refunded":return {"id":r.id,"status":"refunded","message":"Already marked refunded"}
 if r.status not in ("requested","approved"):raise HTTPException(409,"Return cannot be refunded in its current state")
 r.status="refunded";o=db.get(Order,r.order_id);o.payment_status="refunded";audit(db,"REFUND_RECORDED","return",r.id,str({"amount":str(r.refund_amount),"mode":"manual-record"}));db.commit()
 return {"id":r.id,"status":r.status,"refund_amount":str(r.refund_amount),"mode":"manual-record"}


class RegisterInput(BaseModel):
 name:str=Field(min_length=2,max_length=180); email:str=Field(min_length=5,max_length=254); password:str=Field(min_length=10,max_length=128); store_name:str|None=Field(default=None,max_length=180)
class LoginInput(BaseModel):
 email:str; password:str
class ForgotPasswordInput(BaseModel):
 email:str
class ResetPasswordInput(BaseModel):
 token:str=Field(min_length=20,max_length=256); password:str=Field(min_length=10,max_length=128)
def seed_platform_admin(db:Session):
 email=os.getenv("PLATFORM_ADMIN_EMAIL","").strip().lower()
 password=os.getenv("PLATFORM_ADMIN_PASSWORD","")
 if not email or not password:return
 account=db.scalar(select(Account).where(Account.email==email))
 if account:return
 account=Account(name=os.getenv("PLATFORM_ADMIN_NAME","Platform Administrator"),email=email,password_hash=password_digest(password),role="platform_admin",store_name=None)
 db.add(account);db.commit()
def password_digest(password:str,salt:bytes|None=None)->str:
 salt=salt or secrets.token_bytes(16)
 digest=hashlib.scrypt(password.encode(),salt=salt,n=2**14,r=8,p=1,dklen=32)
 return base64.urlsafe_b64encode(salt).decode()+"."+base64.urlsafe_b64encode(digest).decode()
def password_matches(password:str,stored:str)->bool:
 try:
  salt_s,digest_s=stored.split(".",1);salt=base64.urlsafe_b64decode(salt_s);expected=base64.urlsafe_b64decode(digest_s)
  return hmac.compare_digest(hashlib.scrypt(password.encode(),salt=salt,n=2**14,r=8,p=1,dklen=32),expected)
 except Exception:return False
def issue_account_token(account:Account)->str:
 if os.getenv("APP_ENV","development").lower()=="production" and (not os.getenv("AUTH_SECRET") or os.getenv("AUTH_SECRET")=="dev-only-change-this-secret"): raise HTTPException(503,"AUTH_SECRET must be configured before production authentication is enabled")
 expires=str(int(datetime.now(timezone.utc).timestamp())+60*60*12)
 payload=f"{account.id}.{account.role}.{expires}"
 sig=hmac.new(os.getenv("AUTH_SECRET","dev-only-change-this-secret").encode(),payload.encode(),hashlib.sha256).hexdigest()
 return base64.urlsafe_b64encode(f"{payload}.{sig}".encode()).decode()
def account_from_token(authorization:str|None,db:Session)->Account:
 if not authorization or not authorization.startswith("Bearer "):raise HTTPException(401,"Sign in required")
 try:
  raw=base64.urlsafe_b64decode(authorization[7:].encode()).decode();account_id,role,expires,sig=raw.rsplit(".",3);payload=f"{account_id}.{role}.{expires}"
  expected=hmac.new(os.getenv("AUTH_SECRET","dev-only-change-this-secret").encode(),payload.encode(),hashlib.sha256).hexdigest()
  if not hmac.compare_digest(sig,expected) or int(expires)<int(datetime.now(timezone.utc).timestamp()):raise ValueError()
  account=db.get(Account,account_id)
  if not account or not account.active or account.role!=role:raise ValueError()
  return account
 except Exception:raise HTTPException(401,"Session is invalid or expired")
@app.post("/api/v1/auth/register",tags=["Authentication"])
def register_account(payload:RegisterInput,response:Response,db:Session=Depends(get_db)):
 email=payload.email.strip().lower()
 if db.scalar(select(Account.id).where(Account.email==email)):raise HTTPException(409,"An account with this email already exists")
 account=Account(name=payload.name.strip(),email=email,password_hash=password_digest(payload.password),role="store_owner",store_name=payload.store_name)
 db.add(account)
 try:
  db.flush()
  slug_base=__import__("re").sub(r"[^a-z0-9]+","-",payload.store_name.strip().lower()).strip("-") or "store"
  slug=f"{slug_base}-{account.id[:8]}"
  tenant=StoreTenant(name=payload.store_name.strip(),slug=slug,owner_account_id=account.id,status="pending")
  db.add(tenant);db.flush();account.store_id=tenant.id
  audit(db,"STORE_SUBMITTED_FOR_APPROVAL","store",tenant.id,f'{{"owner_account_id":"{account.id}"}}' )
  db.commit()
 except IntegrityError:db.rollback();raise HTTPException(409,"An account with this email already exists")
 db.refresh(account);audit(db,"ACCOUNT_REGISTERED","account",account.id);db.commit()
 token=issue_account_token(account);csrf=secrets.token_urlsafe(32);production=os.getenv("APP_ENV","development").lower()=="production"
 response.set_cookie("vsc_session",token,httponly=True,secure=production,samesite="lax",max_age=43200,path="/")
 response.set_cookie("vsc_csrf",csrf,httponly=False,secure=production,samesite="lax",max_age=43200,path="/")
 return {"token":token,"csrf_token":csrf,"account":{"id":account.id,"name":account.name,"email":account.email,"role":account.role,"store_name":account.store_name,"store_id":account.store_id,"store_status":db.get(StoreTenant,account.store_id).status if account.store_id else None}}
@app.post("/api/v1/auth/login",tags=["Authentication"])
def login_account(payload:LoginInput,response:Response,db:Session=Depends(get_db)):
 account=db.scalar(select(Account).where(Account.email==payload.email.strip().lower()))
 if not account or not account.active or not password_matches(payload.password,account.password_hash):raise HTTPException(401,"Email or password is incorrect")
 token=issue_account_token(account); csrf=secrets.token_urlsafe(32); production=os.getenv("APP_ENV","development").lower()=="production"
 response.set_cookie("vsc_session",token,httponly=True,secure=production,samesite="lax",max_age=43200,path="/")
 response.set_cookie("vsc_csrf",csrf,httponly=False,secure=production,samesite="lax",max_age=43200,path="/")
 return {"token":token,"csrf_token":csrf,"account":{"id":account.id,"name":account.name,"email":account.email,"role":account.role,"store_name":account.store_name,"store_id":account.store_id,"store_status":db.get(StoreTenant,account.store_id).status if account.store_id else None}}
@app.get("/api/v1/auth/me",tags=["Authentication"])
def account_me(authorization:str|None=Header(default=None),session_cookie:str|None=Cookie(default=None,alias="vsc_session"),db:Session=Depends(get_db)):
 a=account_from_token(authorization or ("Bearer "+session_cookie if session_cookie else None),db)
 tenant=db.get(StoreTenant,a.store_id) if a.store_id else None
 return {"id":a.id,"name":a.name,"email":a.email,"role":a.role,"store_name":a.store_name,"store_id":a.store_id,"store_status":tenant.status if tenant else None}
@app.post("/api/v1/auth/forgot-password",tags=["Authentication"])
def forgot_password(payload:ForgotPasswordInput,db:Session=Depends(get_db)):
 a=db.scalar(select(Account).where(Account.email==payload.email.strip().lower()))
 response={"message":"If an account exists for that email, password reset instructions will be sent."}
 if a:
  token=secrets.token_urlsafe(32);a.reset_token_hash=hashlib.sha256(token.encode()).hexdigest();a.reset_expires_at=datetime.now(timezone.utc).replace(tzinfo=None)+__import__("datetime").timedelta(minutes=30);db.commit()
  smtp_host=os.getenv("SMTP_HOST");smtp_from=os.getenv("SMTP_FROM");frontend=os.getenv("FRONTEND_BASE_URL","http://localhost:3000").rstrip("/")
  if smtp_host and smtp_from:
   message=EmailMessage();message["Subject"]="Reset your Virtual Store Commerce password";message["From"]=smtp_from;message["To"]=a.email
   message.set_content("Use this one-time link within 30 minutes to reset your password: "+frontend+"/reset-password?token="+token+"\nIf you did not request this, you can ignore this email.")
   with smtplib.SMTP(smtp_host,int(os.getenv("SMTP_PORT","587")),timeout=10) as server:
    if os.getenv("SMTP_STARTTLS","true").lower()=="true":server.starttls()
    if os.getenv("SMTP_USERNAME"):server.login(os.getenv("SMTP_USERNAME"),os.getenv("SMTP_PASSWORD",""))
    server.send_message(message)
  elif os.getenv("APP_ENV","development").lower()!="production":
   response["development_reset_token"]=token
 return response
@app.post("/api/v1/auth/reset-password",tags=["Authentication"])
def reset_password(payload:ResetPasswordInput,db:Session=Depends(get_db)):
 token_hash=hashlib.sha256(payload.token.encode()).hexdigest()
 a=db.scalar(select(Account).where(Account.reset_token_hash==token_hash))
 if not a or not a.reset_expires_at or a.reset_expires_at<datetime.now(timezone.utc).replace(tzinfo=None):raise HTTPException(400,"Reset link is invalid or expired")
 a.password_hash=password_digest(payload.password);a.reset_token_hash=None;a.reset_expires_at=None;db.commit()
 return {"message":"Password reset successfully. Please sign in with your new password."}


@app.get("/api/v1/platform/summary",tags=["Platform Administration"])
def platform_summary(authorization:str|None=Header(default=None),db:Session=Depends(get_db)):
 account=account_from_token(authorization,db)
 if account.role!="platform_admin":raise HTTPException(403,"Platform administrator role required")
 return {"product_count":db.scalar(select(func.count(Product.id)) ) or 0,"active_product_count":db.scalar(select(func.count(Product.id)).where(Product.active.is_(True))) or 0,"order_count":db.scalar(select(func.count(Order.id))) or 0,"account_count":db.scalar(select(func.count(Account.id))) or 0,"store_owner_count":db.scalar(select(func.count(Account.id)).where(Account.role.in_(["store_owner","store_manager"]))) or 0,"staff_count":db.scalar(select(func.count(StaffMember.id))) or 0}


# Platform control plane: tenant review, account administration, and auditable status changes.
class StoreReviewInput(BaseModel):
 status:str=Field(pattern=r"^(approved|rejected|suspended|pending)$")
 notes:str=Field(default="",max_length=2000)
class AccountAdminInput(BaseModel):
 active:bool|None=None
 role:str|None=Field(default=None,pattern=r"^(store_owner|store_manager|store_staff|platform_admin)$")
class StoreAdminInput(BaseModel):
 name:str|None=Field(default=None,min_length=2,max_length=180)
 plan:str|None=Field(default=None,pattern=r"^(starter|growth|business|enterprise)$")
 notes:str|None=Field(default=None,max_length=2000)
def require_platform_admin(authorization:str|None=Header(default=None),db:Session=Depends(get_db))->Account:
 account=account_from_token(authorization,db)
 if account.role!="platform_admin":raise HTTPException(403,"Platform administrator role required")
 return account
@app.get("/api/v1/platform/stores",tags=["Platform Administration"])
def platform_stores(status_filter:str|None=Query(default=None,alias="status"),authorization:str|None=Header(default=None),db:Session=Depends(get_db)):
 require_platform_admin(authorization,db)
 q=select(StoreTenant).order_by(StoreTenant.created_at.desc())
 if status_filter:
  if status_filter not in ("pending","approved","rejected","suspended"):raise HTTPException(422,"Unsupported store status")
  q=q.where(StoreTenant.status==status_filter)
 rows=list(db.scalars(q))
 return {"items":[{"id":s.id,"name":s.name,"slug":s.slug,"owner_account_id":s.owner_account_id,"owner_email":db.scalar(select(Account.email).where(Account.id==s.owner_account_id)),"status":s.status,"plan":s.plan,"notes":s.notes,"created_at":s.created_at.isoformat(),"reviewed_at":s.reviewed_at.isoformat() if s.reviewed_at else None} for s in rows],"total":len(rows)}
@app.patch("/api/v1/platform/stores/{store_id}",tags=["Platform Administration"])
def update_platform_store(store_id:str,payload:StoreAdminInput,authorization:str|None=Header(default=None),db:Session=Depends(get_db)):
 actor=require_platform_admin(authorization,db);store=db.get(StoreTenant,store_id)
 if not store:raise HTTPException(404,"Store not found")
 for field,value in payload.model_dump(exclude_unset=True).items():setattr(store,field,value)
 audit(db,"PLATFORM_STORE_UPDATED","store",store.id,str(payload.model_dump(exclude_unset=True)));db.commit()
 return {"id":store.id,"name":store.name,"slug":store.slug,"status":store.status,"plan":store.plan,"notes":store.notes}
@app.post("/api/v1/platform/stores/{store_id}/review",tags=["Platform Administration"])
def review_platform_store(store_id:str,payload:StoreReviewInput,authorization:str|None=Header(default=None),db:Session=Depends(get_db)):
 actor=require_platform_admin(authorization,db);store=db.get(StoreTenant,store_id)
 if not store:raise HTTPException(404,"Store not found")
 store.status=payload.status;store.notes=payload.notes;store.reviewed_at=utcnow();store.reviewed_by=actor.id
 audit(db,"STORE_STATUS_CHANGED","store",store.id,f'{{"status":"{payload.status}","reviewed_by":"{actor.id}"}}')
 db.commit()
 return {"id":store.id,"status":store.status,"reviewed_at":store.reviewed_at.isoformat()}
@app.get("/api/v1/platform/accounts",tags=["Platform Administration"])
def platform_accounts(authorization:str|None=Header(default=None),db:Session=Depends(get_db)):
 require_platform_admin(authorization,db)
 rows=list(db.scalars(select(Account).order_by(Account.created_at.desc())))
 return {"items":[{"id":a.id,"name":a.name,"email":a.email,"role":a.role,"active":a.active,"store_id":a.store_id,"store_name":a.store_name,"created_at":a.created_at.isoformat()} for a in rows],"total":len(rows)}
@app.patch("/api/v1/platform/accounts/{account_id}",tags=["Platform Administration"])
def update_platform_account(account_id:str,payload:AccountAdminInput,authorization:str|None=Header(default=None),db:Session=Depends(get_db)):
 actor=require_platform_admin(authorization,db);target=db.get(Account,account_id)
 if not target:raise HTTPException(404,"Account not found")
 changes=payload.model_dump(exclude_unset=True)
 if target.id==actor.id and changes.get("active") is False:raise HTTPException(409,"You cannot deactivate your own active administrator account")
 if changes.get("role")=="platform_admin" and target.role!="platform_admin":
  if not os.getenv("ALLOW_PLATFORM_ADMIN_PROMOTION","").lower()=="true":raise HTTPException(403,"Platform administrator promotion is disabled; set ALLOW_PLATFORM_ADMIN_PROMOTION=true for a controlled operation")
 for field,value in changes.items():setattr(target,field,value)
 audit(db,"PLATFORM_ACCOUNT_UPDATED","account",target.id,str(changes));db.commit()
 return {"id":target.id,"email":target.email,"role":target.role,"active":target.active}
@app.get("/api/v1/platform/audit-events",tags=["Platform Administration"])
def platform_audit_events(limit:int=Query(default=100,ge=1,le=500),authorization:str|None=Header(default=None),db:Session=Depends(get_db)):
 require_platform_admin(authorization,db)
 rows=list(db.scalars(select(AuditEvent).order_by(AuditEvent.created_at.desc()).limit(limit)))
 return {"items":[{"id":e.id,"event_type":e.event_type,"entity_type":e.entity_type,"entity_id":e.entity_id,"details":e.details,"created_at":e.created_at.isoformat()} for e in rows],"total":len(rows)}

# Discovery, customer engagement, fulfilment tracking, and receipt APIs.
class ReviewInput(BaseModel):
 session_id:str=Field(min_length=8,max_length=100)
 rating:int=Field(ge=1,le=5)
 title:str=Field(default="",max_length=180)
 body:str=Field(default="",max_length=2000)
class WishlistInput(BaseModel):
 session_id:str=Field(min_length=8,max_length=100)
 product_id:str
class OrderStatusInput(BaseModel):
 status:str=Field(pattern=r"^(confirmed|picking|packed|dispatched|delivered|failed_delivery|cancelled)$")
 expected_delivery_window:str|None=Field(default=None,max_length=120)
 proof_of_delivery:str|None=Field(default=None,max_length=1000)
@app.get("/api/v1/search/suggestions",tags=["Product Discovery"])
def search_suggestions(q:str=Query(min_length=1,max_length=100),limit:int=Query(default=6,ge=1,le=12),db:Session=Depends(get_db)):
 term=q.strip().casefold()
 products=list(db.scalars(select(Product).where(Product.active.is_(True))))
 matches=[]
 for p in products:
  fields=[p.name,p.sku,p.category,p.brand,*[s.strip() for s in p.synonyms.split(",") if s.strip()]]
  if any(term in field.casefold() for field in fields):matches.append({"type":"product","label":p.name,"product_id":p.id,"sku":p.sku,"category":p.category})
 categories=sorted({p.category for p in products if term in p.category.casefold()})
 matches.extend({"type":"category","label":x,"category":x} for x in categories)
 unique=[];seen=set()
 for item in matches:
  key=(item["type"],item["label"].casefold())
  if key not in seen:seen.add(key);unique.append(item)
 return {"items":unique[:limit]}
@app.get("/api/v1/search/analytics",tags=["Product Discovery"],dependencies=[Depends(require_admin)])
def search_analytics(limit:int=Query(default=20,ge=1,le=100),db:Session=Depends(get_db)):
 rows=list(db.scalars(select(SearchEvent).order_by(SearchEvent.created_at.desc()).limit(1000)))
 popular={};empty={}
 for row in rows:
  popular[row.query]=popular.get(row.query,0)+1
  if row.result_count==0:empty[row.query]=empty.get(row.query,0)+1
 return {"popular":[{"query":k,"count":v} for k,v in sorted(popular.items(),key=lambda x:(-x[1],x[0]))[:limit]],"no_results":[{"query":k,"count":v} for k,v in sorted(empty.items(),key=lambda x:(-x[1],x[0]))[:limit]],"tracked_searches":len(rows)}
@app.get("/api/v1/products/{product_id}/reviews",tags=["Product Discovery"])
def product_reviews(product_id:str,db:Session=Depends(get_db)):
 if not db.get(Product,product_id):raise HTTPException(404,"Product not found")
 rows=list(db.scalars(select(ProductReview).where(ProductReview.product_id==product_id).order_by(ProductReview.created_at.desc())))
 return {"items":[{"id":r.id,"rating":r.rating,"title":r.title,"body":r.body,"created_at":r.created_at.isoformat()} for r in rows],"total":len(rows),"average_rating":round(sum(r.rating for r in rows)/len(rows),2) if rows else None}
@app.post("/api/v1/products/{product_id}/reviews",tags=["Product Discovery"])
def create_product_review(product_id:str,payload:ReviewInput,db:Session=Depends(get_db)):
 if not db.get(Product,product_id):raise HTTPException(404,"Product not found")
 row=db.scalar(select(ProductReview).where(ProductReview.product_id==product_id,ProductReview.session_id==payload.session_id))
 if row:row.rating=payload.rating;row.title=payload.title;row.body=payload.body
 else:row=ProductReview(product_id=product_id,session_id=payload.session_id,rating=payload.rating,title=payload.title,body=payload.body);db.add(row)
 try:db.commit()
 except IntegrityError:db.rollback();raise HTTPException(409,"Review could not be saved")
 return {"id":row.id,"product_id":product_id,"rating":row.rating,"title":row.title,"body":row.body}
@app.get("/api/v1/wishlist",tags=["Customer Accounts"])
def get_wishlist(session_id:str=Query(min_length=8,max_length=100),db:Session=Depends(get_db)):
 rows=list(db.scalars(select(WishlistItem).where(WishlistItem.session_id==session_id).order_by(WishlistItem.created_at.desc())))
 return {"items":[ProductOut.model_validate(p).model_dump(mode="json") for r in rows if (p:=db.get(Product,r.product_id))],"total":len(rows)}
@app.post("/api/v1/wishlist",tags=["Customer Accounts"])
def add_wishlist(payload:WishlistInput,db:Session=Depends(get_db)):
 product=db.get(Product,payload.product_id)
 if not product or not product.active:raise HTTPException(404,"Product not found")
 row=db.scalar(select(WishlistItem).where(WishlistItem.session_id==payload.session_id,WishlistItem.product_id==payload.product_id))
 if not row:db.add(WishlistItem(session_id=payload.session_id,product_id=payload.product_id));db.commit()
 return get_wishlist(payload.session_id,db)
@app.delete("/api/v1/wishlist/{product_id}",tags=["Customer Accounts"])
def remove_wishlist(product_id:str,session_id:str=Query(min_length=8,max_length=100),db:Session=Depends(get_db)):
 row=db.scalar(select(WishlistItem).where(WishlistItem.session_id==session_id,WishlistItem.product_id==product_id))
 if row:db.delete(row);db.commit()
 return get_wishlist(session_id,db)
@app.post("/api/v1/admin/orders/{order_id}/status",tags=["Retailer Admin"],dependencies=[Depends(require_admin)])
def update_order_status(order_id:str,payload:OrderStatusInput,db:Session=Depends(get_db)):
 order=db.get(Order,order_id)
 if not order:raise HTTPException(404,"Order not found")
 allowed={"pending_payment":{"confirmed","cancelled"},"confirmed":{"picking","cancelled"},"picking":{"packed","cancelled"},"packed":{"dispatched","cancelled"},"dispatched":{"delivered","failed_delivery"},"failed_delivery":{"dispatched","cancelled"}}
 if payload.status==order.status:return {"order_id":order.id,"status":order.status,"message":"No status change"}
 if payload.status not in allowed.get(order.status,set()):raise HTTPException(409,f"Cannot change order status from {order.status} to {payload.status}")
 if payload.status=="confirmed" and order.payment_status!="paid":raise HTTPException(409,"Only paid orders can be confirmed")
 order.status=payload.status
 audit(db,"ORDER_FULFILMENT_STATUS_CHANGED","order",order.id,str({"status":payload.status,"expected_delivery_window":payload.expected_delivery_window,"proof_of_delivery":bool(payload.proof_of_delivery)}))
 db.commit()
 return {"order_id":order.id,"status":order.status,"expected_delivery_window":payload.expected_delivery_window,"proof_of_delivery":payload.proof_of_delivery}
@app.get("/api/v1/orders/{order_id}/receipt",tags=["Orders"])
def order_receipt(order_id:str,session_id:str=Query(min_length=8,max_length=100),db:Session=Depends(get_db)):
 order=db.get(Order,order_id)
 if not order or order.session_id!=session_id:raise HTTPException(404,"Order not found")
 return {"receipt_number":"VSC-"+order.id[:8].upper(),"issued_at":order.created_at.isoformat(),"currency":order.currency,"subtotal":str(order.subtotal),"payment_status":order.payment_status,"order_status":order.status,"customer":{"name":order.customer_name,"phone":order.customer_phone,"email":order.customer_email,"address":order.delivery_address},"items":[{"sku":i.sku,"name":i.product_name,"unit_price":str(i.unit_price),"quantity":i.quantity,"line_total":str(i.unit_price*i.quantity)} for i in order.items]}
