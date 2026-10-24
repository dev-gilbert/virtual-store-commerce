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
        <p className="page-intro">Explore our first interactive supermarket prototype. Drag to look around, zoom to inspect the layout, and click the cabinet drawer to reveal its contents.</p>
      </header>
      <VirtualStore />
      <p className="prototype-note">Prototype notice: products and inventory in this scene are illustrative placeholders. No purchases or payments are processed yet.</p>
    </main>
  );
}
