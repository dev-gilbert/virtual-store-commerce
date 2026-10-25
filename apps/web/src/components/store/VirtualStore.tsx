"use client";
import {useCallback,useEffect,useState} from "react";
import {Canvas} from "@react-three/fiber";
import {Html,OrbitControls,useTexture} from "@react-three/drei";
import {api,getSessionId,type Product} from "@/lib/commerce";
type Placed={placement_id:string;product_id:string;sku:string;name:string;price:string;color:string;image_url?:string|null;stock_quantity:number;shelf_level:number;slot:number};
type Fixture={id:string;code:string;name:string;kind:string;position:number[];products:Placed[]};type Layout={items:Fixture[];total:number};
const productImages=[
 "https://images.unsplash.com/photo-1571771894821-ce9b6c11b08e?w=256&h=256&fit=crop",
 "https://images.unsplash.com/photo-1563636619-e9143da7973b?w=256&h=256&fit=crop",
 "https://images.unsplash.com/photo-1509440159596-0249088772ff?w=256&h=256&fit=crop",
 "https://images.unsplash.com/photo-1600271886742-f049cd451bba?w=256&h=256&fit=crop",
 "https://images.unsplash.com/photo-1586201375761-83865001e31c?w=256&h=256&fit=crop",
 "https://images.unsplash.com/photo-1608248543803-ba4f8c70ae0b?w=256&h=256&fit=crop",
 "https://images.unsplash.com/photo-1499636136210-6f4ee915583e?w=256&h=256&fit=crop",
 "https://images.unsplash.com/photo-1594631252845-29fc4cc8cde9?w=256&h=256&fit=crop"
];
function ProductBox({p,onSelect,position}:{p:Placed;onSelect:(id:string)=>void;position:[number,number,number]}) {
 const fallback=productImages[Math.abs(p.sku.split("").reduce((n,c)=>n+c.charCodeAt(0),0))%productImages.length];
 const image=p.image_url||fallback;
 const texture=useTexture(image);
 return <group position={position} onClick={e=>{e.stopPropagation();onSelect(p.product_id)}}>
  <mesh castShadow><boxGeometry args={[.25,.3,.22]}/><meshStandardMaterial color={p.color||"#d6d0c0"} roughness={.8}/></mesh>
  <mesh position={[0,0,.113]}><planeGeometry args={[.19,.23]}/><meshBasicMaterial map={texture} toneMapped={false}/></mesh>
  <Html distanceFactor={12} position={[0,.22,.1]} center style={{pointerEvents:"none"}}><div className="product-hotspot-label"><strong>{p.name}</strong><span>{Number(p.price).toLocaleString()} RWF</span></div></Html>
 </group>
}
function FixtureView({fixture,onSelect}:{fixture:Fixture;onSelect:(id:string)=>void}) {
 const [open,setOpen]=useState(fixture.kind!=="drawer");
 const drawer=fixture.kind==="drawer",cold=fixture.kind==="refrigerator",counter=fixture.kind==="checkout"||fixture.kind==="table",display=fixture.kind==="display";
 const items=fixture.products;
 return <group position={fixture.position as [number,number,number]}>
 {drawer?<><mesh position={[0,.38,0]} castShadow><boxGeometry args={[1.65,.76,1.05]}/><meshStandardMaterial color="#887d70"/></mesh><mesh position={[0,.79,open?-.22:.18]} castShadow><boxGeometry args={[1.4,.1,.84]}/><meshStandardMaterial color="#c4ae91"/></mesh><mesh position={[0,.52,open?-.25:0]}><boxGeometry args={[1.25,.07,.68]}/><meshStandardMaterial color="#e3d5c0"/></mesh><mesh position={[0,.86,.52]} onClick={e=>{e.stopPropagation();setOpen(v=>!v)}}><boxGeometry args={[1.4,.12,.08]}/><meshStandardMaterial color="#b9a184"/></mesh>{open&&items.map((p,i)=><ProductBox key={p.placement_id} p={p} onSelect={onSelect} position={[-.48+(i%4)*.31,.66+Math.floor(i/4)*.25,-.1]}/>)}</>:cold?<><mesh position={[0,.9,0]} castShadow><boxGeometry args={[1.5,1.8,.9]}/><meshStandardMaterial color="#c7d9d9" metalness={0.1} roughness={0.35} transparent opacity={.38}/></mesh><mesh position={[0,.9,.47]}><boxGeometry args={[1.4,1.7,.035]}/><meshStandardMaterial color="#e7f3f1" transparent opacity={.35}/></mesh>{[.25,.68,1.11,1.54].map(y=><mesh key={y} position={[0,y,.12]}><boxGeometry args={[1.3,.035,.72]}/><meshStandardMaterial color="#a4babb" metalness={0.2}/></mesh>)}{items.map((p,i)=><ProductBox key={p.placement_id} p={p} onSelect={onSelect} position={[-.48+(i%4)*.31,.38+Math.min(3,p.shelf_level)*.4,.22]}/>)}</>:counter||display?<><mesh position={[0,.62,0]} castShadow><boxGeometry args={[1.75,.18,.95]}/><meshStandardMaterial color={display?"#d9d4c8":"#b9a78c"}/></mesh>{[-.7,.7].map(x=><mesh key={x} position={[x,.31,0]}><boxGeometry args={[.1,.58,.8]}/><meshStandardMaterial color="#8a8378"/></mesh>)}{items.map((p,i)=><ProductBox key={p.placement_id} p={p} onSelect={onSelect} position={[-.58+(i%4)*.36,.83+Math.floor(i/4)*.28,.1]}/>)}</>:<>{[-.9,.9].map(x=><mesh key={x} position={[x,.9,0]} castShadow><boxGeometry args={[.08,1.8,.72]}/><meshStandardMaterial color="#777b7c" metalness:.25 roughness:.55/></mesh>)}{[.35,.8,1.25,1.7].map(y=><mesh key={y} position={[0,y,0]}><boxGeometry args={[1.9,.07,.82]}/><meshStandardMaterial color="#d8d5ce"/></mesh>)}{items.map((p,i)=><ProductBox key={p.placement_id} p={p} onSelect={onSelect} position={[-.68+(i%6)*.27,.51+Math.min(3,p.shelf_level)*.4,.14]}/>)}</>}
 <Html position={[0,2.15,0]} center distanceFactor={15} style={{pointerEvents:"none"}}><div className="fixture-name-tag">{fixture.name}</div></Html>
 </group>
}
function Scene({layout,onSelect}:{layout:Layout;onSelect:(id:string)=>void}){return <><color attach="background" args={["#e9e7e1"]}/><ambientLight intensity={1.15}/><hemisphereLight args={["#fff","#b9b3a8",1.2]}/><directionalLight position={[6,10,5]} intensity={2.1} castShadow/><mesh rotation={[-Math.PI/2,0,0]} position={[0,-.06,0]} receiveShadow><planeGeometry args={[32,32]}/><meshStandardMaterial color="#c9c7c0"/></mesh><mesh position={[0,2.5,-5]}><boxGeometry args={[14,5,.18]}/><meshStandardMaterial color="#f4f1ea"/></mesh>{layout.items.map(f=><FixtureView key={f.id} fixture={f} onSelect={onSelect}/>)}<OrbitControls makeDefault target={[0,1,0]} minDistance={3} maxDistance={17} maxPolarAngle={Math.PI/2-.04} enableDamping dampingFactor={.08}/></>}
export default function VirtualStore(){const [layout,setLayout]=useState<Layout>({items:[],total:0}),[products,setProducts]=useState<Product[]>([]),[selected,setSelected]=useState<Product|null>(null),[message,setMessage]=useState("Loading store layout…"),[adding,setAdding]=useState(false),[cartCount,setCartCount]=useState(0);
 const refreshCart=useCallback(async()=>{const c=await api<{item_count:number}>(`/api/v1/cart?session_id=${encodeURIComponent(getSessionId())}`);setCartCount(c.item_count)},[]);
 useEffect(()=>{Promise.all([api<Layout>("/api/v1/store-layout"),api<{items:Product[]}>("/api/v1/products"),refreshCart()]).then(([l,p])=>{setLayout(l);setProducts(p.items);setMessage("")}).catch((e:Error)=>setMessage(`Cannot load 3D store: ${e.message}. Start FastAPI on port 8000.`))},[refreshCart]);
 const select=useCallback((id:string)=>{const p=products.find(x=>x.id===id);if(p)setSelected(p)},[products]);
 async function add(){if(!selected||adding)return;setAdding(true);try{const r=await api<{item_count:number}>(`/api/v1/cart/items?session_id=${encodeURIComponent(getSessionId())}`,{method:"POST",body:JSON.stringify({product_id:selected.id,quantity:1})});setCartCount(r.item_count);setMessage(`${selected.name} added to your basket.`);setSelected(null)}catch(e){setMessage((e as Error).message)}finally{setAdding(false)}}
 return <div className="virtual-store-frame"><div className="virtual-store-canvas" aria-label="Interactive 3D supermarket; click products to add them to your basket"><Canvas shadows dpr={[1,1.5]} camera={{position:[8,6,10],fov:42,near:.1,far:100}} gl={{antialias:true,powerPreference:"high-performance"}}><Scene layout={layout} onSelect={select}/></Canvas><div className="scene-hint">Drag to look around · Scroll to zoom · Click a product to inspect it</div><a className="scene-cart-link" href="/shop" aria-label={`Shopping cart, ${cartCount} items`}><span>🛒</span><strong>Basket</strong><b>{cartCount}</b></a>{selected&&<div className="scene-product-card"><button type="button" className="scene-product-close" onClick={()=>setSelected(null)} aria-label="Close product details">×</button><span className="scene-product-swatch" style={{background:selected.color}}/>{selected.image_url&&<img className="scene-product-image" src={selected.image_url} alt={selected.name}/>}<div><strong>{selected.name}</strong><p>{new Intl.NumberFormat("en-RW",{style:"currency",currency:selected.currency,maximumFractionDigits:0}).format(Number(selected.price))}</p><small>{selected.stock_quantity} in stock</small></div><button className="scene-add-button" type="button" onClick={add} disabled={adding||selected.stock_quantity<1}>{adding?"Adding…":"Add +"}</button></div>}</div>{message&&<p className="store-feedback" role="status">{message}</p>}</div>}
