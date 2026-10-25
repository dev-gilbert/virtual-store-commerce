"use client";
import {useCallback,useEffect,useState} from "react";
import Link from "next/link";
import {api} from "@/lib/commerce";
type Fixture={id:string;code:string;name:string;kind:string;position:number[];products:{product_id:string;name:string;sku:string;price:string;stock_quantity:number;shelf_level:number;slot:number}[]};
type Layout={items:Fixture[];total:number};
export default function StoreMapPage(){
 const [layout,setLayout]=useState<Layout|null>(null),[error,setError]=useState("");
 const load=useCallback(async()=>{try{setLayout(await api<Layout>("/api/v1/store-layout"));setError("")}catch(e){setError((e as Error).message)}},[]);
 useEffect(()=>{Promise.resolve().then(()=>load())},[load]);
 const products=layout?.items.flatMap(f=>f.products.map(p=>({...p,aisle:f.name})))??[];
 return <main className="page-shell store-map-page"><Link className="back-link" href="/shop">← Back to shop</Link><header className="page-heading"><p className="eyebrow">FIND YOUR WAY</p><h1>The store, <span>mapped out.</span></h1><p className="page-intro">Use this aisle directory to find products in the virtual supermarket. Locations come from the store layout, not guessed directions.</p></header>{error&&<p className="inline-message" role="status">{error}</p>}{!layout&&!error?<div className="orders-empty">Loading aisle directory…</div>:layout&&<><section className="store-map-board" aria-label="Store fixture map"><div className="map-entrance">ENTRANCE</div>{layout.items.map(f=>{const x=Number(f.position[0]??0),z=Number(f.position[2]??0);return <article className="map-fixture" key={f.id} style={{left:"calc(50% + "+(x*7)+"%)",top:"calc(48% + "+(z*7)+"%)"}}><strong>{f.name}</strong><small>{f.products.length} listed products</small></article>})}<div className="map-legend">Aisle markers reflect current fixture positions</div></section><div className="map-directory-head"><h2>Aisle directory</h2><span>{products.length} placed products</span></div><div className="map-directory">{layout.items.map(f=><section className="map-aisle-card" key={f.id}><div><p className="eyebrow">{f.kind.toUpperCase()} · {f.code}</p><h3>{f.name}</h3></div>{f.products.length?<ul>{f.products.map(p=><li key={p.product_id}><Link href={"/products/"+p.product_id}>{p.name}</Link><span>{p.stock_quantity>0?"In stock":"Unavailable"}</span></li>)}</ul>:<p className="order-meta">No products assigned to this fixture yet.</p>}</section>)}</div></>}</main>
}
