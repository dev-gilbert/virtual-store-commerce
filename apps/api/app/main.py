from __future__ import annotations
import os, uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from decimal import Decimal
from typing import Generator
from fastapi import Depends, FastAPI, Header, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, create_engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, sessionmaker

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
 created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow)
class Fixture(Base):
 __tablename__="fixtures"
 id:Mapped[str]=mapped_column(String(36),primary_key=True,default=lambda:str(uuid.uuid4()))
 code:Mapped[str]=mapped_column(String(80),unique=True); name:Mapped[str]=mapped_column(String(160)); kind:Mapped[str]=mapped_column(String(40),default="shelf")
 x:Mapped[float]=mapped_column(Numeric(8,3),default=0); y:Mapped[float]=mapped_column(Numeric(8,3),default=0); z:Mapped[float]=mapped_column(Numeric(8,3),default=0)
class ProductPlacement(Base):
 __tablename__="product_placements"
 id:Mapped[str]=mapped_column(String(36),primary_key=True,default=lambda:str(uuid.uuid4()))
 product_id:Mapped[str]=mapped_column(ForeignKey("products.id",ondelete="CASCADE"),index=True); fixture_id:Mapped[str]=mapped_column(ForeignKey("fixtures.id",ondelete="CASCADE"),index=True)
 shelf_level:Mapped[int]=mapped_column(Integer,default=0); slot:Mapped[int]=mapped_column(Integer,default=0)
 product:Mapped[Product]=relationship()
 __table_args__=(UniqueConstraint("product_id","fixture_id","shelf_level","slot",name="uq_product_fixture_slot"),)
class CartItem(Base):
 __tablename__="cart_items"
 id:Mapped[str]=mapped_column(String(36),primary_key=True,default=lambda:str(uuid.uuid4()))
 session_id:Mapped[str]=mapped_column(String(100),index=True); product_id:Mapped[str]=mapped_column(ForeignKey("products.id",ondelete="CASCADE"),index=True)
 quantity:Mapped[int]=mapped_column(Integer,default=1); product:Mapped[Product]=relationship()
 __table_args__=(UniqueConstraint("session_id","product_id",name="uq_cart_session_product"),)
class Order(Base):
 __tablename__="orders"
 id:Mapped[str]=mapped_column(String(36),primary_key=True,default=lambda:str(uuid.uuid4()))
 session_id:Mapped[str]=mapped_column(String(100),index=True); idempotency_key:Mapped[str]=mapped_column(String(160),unique=True,index=True)
 status:Mapped[str]=mapped_column(String(30),default="pending_payment"); payment_status:Mapped[str]=mapped_column(String(30),default="unpaid")
 subtotal:Mapped[Decimal]=mapped_column(Numeric(12,2)); currency:Mapped[str]=mapped_column(String(3),default="RWF")
 created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow)
 items:Mapped[list["OrderItem"]]=relationship(back_populates="order",cascade="all, delete-orphan")
class OrderItem(Base):
 __tablename__="order_items"
 id:Mapped[str]=mapped_column(String(36),primary_key=True,default=lambda:str(uuid.uuid4()))
 order_id:Mapped[str]=mapped_column(ForeignKey("orders.id",ondelete="CASCADE"),index=True); product_id:Mapped[str]=mapped_column(String(36))
 sku:Mapped[str]=mapped_column(String(80)); product_name:Mapped[str]=mapped_column(String(180)); unit_price:Mapped[Decimal]=mapped_column(Numeric(12,2)); quantity:Mapped[int]=mapped_column(Integer)
 order:Mapped[Order]=relationship(back_populates="items")
class AuditEvent(Base):
 __tablename__="audit_events"
 id:Mapped[str]=mapped_column(String(36),primary_key=True,default=lambda:str(uuid.uuid4())); event_type:Mapped[str]=mapped_column(String(100),index=True)
 entity_type:Mapped[str]=mapped_column(String(80)); entity_id:Mapped[str]=mapped_column(String(36),index=True); details:Mapped[str]=mapped_column(Text,default="{}")
 created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow)
def get_db()->Generator[Session,None,None]:
 db=SessionLocal()
 try: yield db
 finally: db.close()
class ProductCreate(BaseModel):
 sku:str=Field(min_length=2,max_length=80); name:str=Field(min_length=2,max_length=180); description:str=Field(default="",max_length=2000)
 category:str=Field(min_length=2,max_length=80); price:Decimal=Field(gt=0,max_digits=12,decimal_places=2); currency:str=Field(default="RWF",min_length=3,max_length=3)
 stock_quantity:int=Field(default=0,ge=0,le=1000000); image_url:str|None=Field(default=None,max_length=500); color:str=Field(default="#799d79",pattern=r"^#[0-9a-fA-F]{6}$")
class ProductPatch(BaseModel):
 name:str|None=Field(default=None,min_length=2,max_length=180); description:str|None=Field(default=None,max_length=2000)
 category:str|None=Field(default=None,min_length=2,max_length=80); price:Decimal|None=Field(default=None,gt=0,max_digits=12,decimal_places=2)
 stock_quantity:int|None=Field(default=None,ge=0,le=1000000); active:bool|None=None
class ProductOut(BaseModel):
 model_config=ConfigDict(from_attributes=True)
 id:str; sku:str; name:str; description:str; category:str; price:Decimal; currency:str; stock_quantity:int; image_url:str|None; color:str; active:bool
class CartItemInput(BaseModel):
 product_id:str; quantity:int=Field(default=1,ge=1,le=99)
class CheckoutInput(BaseModel): session_id:str=Field(min_length=8,max_length=100)
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
 return {"id":o.id,"status":o.status,"payment_status":o.payment_status,"subtotal":str(o.subtotal),"currency":o.currency,"created_at":o.created_at.isoformat(),
 "items":[{"product_id":i.product_id,"sku":i.sku,"name":i.product_name,"unit_price":str(i.unit_price),"quantity":i.quantity} for i in o.items],
 "payment":{"mode":"sandbox","next_action":f"/api/v1/payments/{o.id}/simulate-success"}}
@asynccontextmanager
async def lifespan(_):
 Base.metadata.create_all(bind=engine)
 with SessionLocal() as db: seed_data(db)
 yield
app=FastAPI(title="Virtual Store Commerce API",version="0.2.0",description="Shared catalogue, 3D layout, cart, orders and sandbox payments.",lifespan=lifespan)
app.add_middleware(CORSMiddleware,allow_origins=os.getenv("CORS_ORIGINS","http://localhost:3000").split(","),allow_credentials=True,allow_methods=["GET","POST","PATCH","DELETE","OPTIONS"],allow_headers=["Content-Type","Authorization","Idempotency-Key","X-Admin-Key"])
@app.get("/health",tags=["Operations"])
def health(): return {"status":"ok","service":"virtual-store-commerce-api","database":"connected"}
@app.get("/api/v1/products",tags=["Products"])
def products(q:str|None=Query(default=None,max_length=100),category:str|None=Query(default=None,max_length=80),db:Session=Depends(get_db)):
 query=select(Product).where(Product.active.is_(True)).order_by(Product.category,Product.name)
 if q: query=query.where((Product.name.ilike(f"%{q}%"))|(Product.description.ilike(f"%{q}%"))|(Product.sku.ilike(f"%{q}%")))
 if category: query=query.where(Product.category==category)
 ps=list(db.scalars(query)); return {"items":[ProductOut.model_validate(p).model_dump(mode="json") for p in ps],"total":len(ps)}
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
   "products":[{"placement_id":p.id,"product_id":p.product.id,"sku":p.product.sku,"name":p.product.name,"price":str(p.product.price),"color":p.product.color,"stock_quantity":p.product.stock_quantity,"shelf_level":p.shelf_level,"slot":p.slot} for p in ps if p.product.active]})
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
 order=Order(session_id=payload.session_id,idempotency_key=idempotency_key,subtotal=subtotal,currency="RWF"); db.add(order); db.flush()
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
def get_order(order_id:str,db:Session=Depends(get_db)):
 o=db.get(Order,order_id)
 if not o: raise HTTPException(404,"Order not found")
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
def require_admin(x_admin_key:str|None=Header(default=None,alias="X-Admin-Key")):
 if not x_admin_key or x_admin_key!=os.getenv("ADMIN_API_KEY","local-dev-admin-change-me"): raise HTTPException(401,"A valid X-Admin-Key is required")
@app.post("/api/v1/admin/products",response_model=ProductOut,status_code=status.HTTP_201_CREATED,tags=["Retailer Admin"],dependencies=[Depends(require_admin)])
def create_product(payload:ProductCreate,db:Session=Depends(get_db)):
 p=Product(**payload.model_dump()); db.add(p)
 try:
  db.flush(); audit(db,"PRODUCT_CREATED","product",p.id,f'{{"sku":"{p.sku}"}}'); db.commit(); db.refresh(p)
 except IntegrityError: db.rollback(); raise HTTPException(409,"That SKU already exists")
 return p
@app.patch("/api/v1/admin/products/{product_id}",response_model=ProductOut,tags=["Retailer Admin"],dependencies=[Depends(require_admin)])
def update_product(product_id:str,payload:ProductPatch,db:Session=Depends(get_db)):
 p=db.get(Product,product_id)
 if not p: raise HTTPException(404,"Product not found")
 changes=payload.model_dump(exclude_unset=True)
 for field,value in changes.items(): setattr(p,field,value)
 audit(db,"PRODUCT_UPDATED","product",p.id,str(changes)); db.commit(); db.refresh(p); return p
@app.get("/api/v1/admin/summary",tags=["Retailer Admin"],dependencies=[Depends(require_admin)])
def admin_summary(db:Session=Depends(get_db)):
 ps=list(db.scalars(select(Product))); orders=list(db.scalars(select(Order)))
 return {"product_count":len(ps),"active_product_count":sum(p.active for p in ps),"units_in_stock":sum(p.stock_quantity for p in ps),"order_count":len(orders),"pending_payment_count":sum(o.status=="pending_payment" for o in orders),"confirmed_order_count":sum(o.status=="confirmed" for o in orders)}
@app.get("/api/v1/admin/audit-events",tags=["Retailer Admin"],dependencies=[Depends(require_admin)])
def audit_events(limit:int=Query(default=50,ge=1,le=200),db:Session=Depends(get_db)):
 es=list(db.scalars(select(AuditEvent).order_by(AuditEvent.created_at.desc()).limit(limit)))
 return {"items":[{"id":e.id,"event_type":e.event_type,"entity_type":e.entity_type,"entity_id":e.entity_id,"details":e.details,"created_at":e.created_at.isoformat()} for e in es],"total":len(es)}
