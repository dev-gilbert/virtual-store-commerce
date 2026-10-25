"use client";
export const API_BASE=process.env.NEXT_PUBLIC_API_BASE_URL??"http://localhost:8000";
export function getSessionId(){if(typeof window==="undefined")return "server-session-placeholder";const key="virtual-store-session-id";let id=window.localStorage.getItem(key);if(!id){id=window.crypto?.randomUUID?.()??`guest-${Date.now()}-${Math.random().toString(36).slice(2)}`;window.localStorage.setItem(key,id)}return id}
function csrfToken(){if(typeof document==="undefined")return "";const match=document.cookie.match(/(?:^|; )vsc_csrf=([^;]+)/);return match?decodeURIComponent(match[1]):""}
export async function api<T>(path:string,init?:RequestInit):Promise<T>{const method=(init?.method??"GET").toUpperCase();const csrf=csrfToken();const r=await fetch(`${API_BASE}${path}`,{...init,credentials:"include",headers:{"Content-Type":"application/json",...(process.env.NEXT_PUBLIC_STORE_ID?{"X-Store-ID":process.env.NEXT_PUBLIC_STORE_ID}:{}),...(method!=="GET"&&method!=="HEAD"&&csrf?{"X-CSRF-Token":csrf}:{}),...(init?.headers??{})},cache:"no-store"});const data=await r.json().catch(()=>({}));if(!r.ok)throw new Error(typeof data.detail==="string"?data.detail:"The request could not be completed.");return data as T}
export type Product={id:string;sku:string;name:string;description:string;category:string;price:string|number;currency:string;stock_quantity:number;image_url?:string|null;color:string;active:boolean;brand?:string;synonyms?:string;unit?:string;ingredients?:string;allergens?:string;nutrition?:string;gallery_json?:string;video_url?:string|null;discontinued?:boolean};
export type Cart={session_id:string;items:{product_id:string;sku:string;name:string;price:string;currency:string;quantity:number;line_total:string;stock_quantity:number}[];item_count:number;subtotal:string;currency:string};

export type ProductSearchOptions={q?:string;category?:string;min_price?:string;max_price?:string;in_stock?:boolean;sort?:"relevance"|"price_asc"|"price_desc"|"newest"|"name"|"popularity";limit?:number;offset?:number};
export type ProductSearchResult={items:Product[];total:number;limit:number;offset:number};
export function productSearchPath(options:ProductSearchOptions={}){const params=new URLSearchParams();for(const [key,value] of Object.entries(options)){if(value!==undefined&&value!==null&&value!=="")params.set(key,String(value))}return `/api/v1/products?${params.toString()}`}
export async function searchProducts(options:ProductSearchOptions={}){return api<ProductSearchResult&{alternatives?:Product[]}>(productSearchPath(options))}
export type SearchSuggestion={type:string;label:string;product_id?:string;sku?:string;category?:string};
export async function getSearchSuggestions(q:string){return api<{items:SearchSuggestion[]}>(`/api/v1/search/suggestions?q=${encodeURIComponent(q)}`)}

export type Order={id:string;status:string;payment_status:string;subtotal:string;currency:string;created_at:string;customer_name:string|null;customer_phone:string;customer_email:string|null;delivery_address:string|null;delivery_instructions:string|null;is_anonymous:boolean;items:{product_id:string;sku:string;name:string;unit_price:string;quantity:number}[]};
export async function listOrders(){return api<{items:Order[];total:number}>(`/api/v1/orders?session_id=${encodeURIComponent(getSessionId())}`)}
