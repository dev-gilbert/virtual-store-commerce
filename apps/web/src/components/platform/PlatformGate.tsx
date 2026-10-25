"use client";
import {useEffect,useState} from "react";
import Link from "next/link";
import {api} from "@/lib/commerce";
import PlatformDashboard from "@/components/platform/PlatformDashboard";
export default function PlatformGate(){const [status,setStatus]=useState<"checking"|"allowed"|"denied">("checking");useEffect(()=>{const token=localStorage.getItem("virtual-store-auth-token");if(!token){Promise.resolve().then(()=>setStatus("denied"));return}api<{role:string}>("/api/v1/auth/me").then(a=>setStatus(a.role==="platform_admin"?"allowed":"denied")).catch(()=>setStatus("denied"))},[]);if(status==="checking")return <main className="auth-loading">Checking platform administrator access…</main>;if(status==="denied")return <main className="platform-access-denied"><span className="brand-icon">v</span><p className="eyebrow">RESTRICTED WORKSPACE</p><h1>Platform administrator access only.</h1><p>Sign in with a platform administrator account. Store-owner accounts belong in My Store.</p><Link className="button-primary" href="/login">Sign in ↗</Link><Link href="/mystore">Go to My Store</Link></main>;return <PlatformDashboard/>}
