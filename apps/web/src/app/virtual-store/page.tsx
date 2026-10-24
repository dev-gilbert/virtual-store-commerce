import Link from "next/link";
import VirtualStore from "@/components/store/VirtualStore";

export const metadata = {
  title: "Explore the Virtual Store | Virtual Store Commerce",
  description: "Explore an original interactive 3D supermarket prototype.",
};

export default function VirtualStorePage() {
  return (
    <main className="page-shell virtual-store-page">
      <header className="page-heading">
        <Link className="back-link" href="/">← Back to store</Link>
        <p className="eyebrow">EARLY ACCESS · 3D STORE</p>
        <h1>Walk the aisles.<br /><span>Discover something new.</span></h1>
        <p className="page-intro">Explore the live product layout. Drag to look around, zoom to inspect the shelves, and select a product to add it to your shared basket.</p>
      </header>
      <VirtualStore />
      <p className="prototype-note">Products, prices and stock are loaded from the commerce API and shared with the catalogue. Checkout and payment confirmation run in a local sandbox only, with no real money charged.</p><p className="prototype-note"><Link href="/shop">Prefer the conventional catalogue? Shop here →</Link></p>
    </main>
  );
}
