"use client";
export const API_BASE=process.env.NEXT_PUBLIC_API_BASE_URL??"http://localhost:8000";
export function getSessionId(){if(typeof window==="undefined")return "server-session-placeholder";const key="virtual-store-session-id";let id=window.localStorage.getItem(key);if(!id){id=window.crypto?.randomUUID?.()??`guest-${Date.now()}-${Math.random().toString(36).slice(2)}`;window.localStorage.setItem(key,id)}return id}
export async function api<T>(path:string,init?:RequestInit):Promise<T>{const r=await fetch(`${API_BASE}${path}`,{...init,headers:{"Content-Type":"application/json",...(init?.headers??{})},cache:"no-store"});const data=await r.json().catch(()=>({}));if(!r.ok)throw new Error(typeof data.detail==="string"?data.detail:"The request could not be completed.");return data as T}
export type Product={id:string;sku:string;name:string;description:string;category:string;price:string|number;currency:string;stock_quantity:number;image_url?:string|null;color:string;active:boolean};
export type Cart={session_id:string;items:{product_id:string;sku:string;name:string;price:string;currency:string;quantity:number;line_total:string;stock_quantity:number}[];item_count:number;subtotal:string;currency:string};

export type ProductSearchOptions={q?:string;category?:string;min_price?:string;max_price?:string;in_stock?:boolean;sort?:"relevance"|"price_asc"|"price_desc"|"newest"|"name";limit?:number;offset?:number};
export type ProductSearchResult={items:Product[];total:number;limit:number;offset:number};
export function productSearchPath(options:ProductSearchOptions={}){const params=new URLSearchParams();for(const [key,value] of Object.entries(options)){if(value!==undefined&&value!==null&&value!=="")params.set(key,String(value))}return `/api/v1/products?${params.toString()}`}
export async function searchProducts(options:ProductSearchOptions={}){return api<ProductSearchResult>(productSearchPath(options))}
