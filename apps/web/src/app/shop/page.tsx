import type { Metadata } from "next";
import Link from "next/link";
import ShopExperience from "@/components/store/ShopExperience";
export const metadata:Metadata={title:"Shop the Catalogue | Virtual Store Commerce",description:"Browse the shared catalogue and test sandbox checkout."};
export default function ShopPage(){return <main className="page-shell shop-page"><Link className="back-link" href="/">← Back to home</Link><header className="page-heading shop-page-heading"><p className="eyebrow">THE CONVENTIONAL SHOP</p><h1>Find your favourites.<br/><span>Without leaving the aisle.</span></h1><p className="page-intro">Browse the same live products and inventory as the 3D supermarket. Your guest basket follows you across both experiences.</p></header><ShopExperience/></main>}