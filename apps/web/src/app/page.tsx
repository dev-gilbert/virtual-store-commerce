import Link from "next/link";

const highlights = [
  { number: "01", title: "Explore in 3D", description: "Move through a virtual supermarket and discover products in their place on the shelf." },
  { number: "02", title: "Shop your way", description: "Prefer speed? Search the catalogue and add products without entering the 3D store." },
  { number: "03", title: "One shared basket", description: "The vision is one product catalogue and cart behind both shopping experiences." },
];

export default function Home() {
  return (
    <main className="home-shell">
      <nav className="top-nav">
        <Link href="/" className="brand-mark"><span className="brand-icon">v</span><span>virtual<span className="brand-light">store</span></span></Link>
        <div className="nav-links"><Link href="#how-it-works">How it works</Link><Link href="/virtual-store">3D store</Link></div>
        <Link href="/virtual-store" className="nav-cta">Explore store <span aria-hidden="true">↗</span></Link>
      </nav>

      <section className="hero-section">
        <div className="hero-copy">
          <p className="eyebrow"><span className="status-dot" /> A new dimension of shopping</p>
          <h1>Your next shop.<br /><span>In a whole new space.</span></h1>
          <p className="hero-description">A more human way to shop online. Explore a virtual supermarket, discover products in context, or take the fast lane through a familiar product catalogue.</p>
          <div className="hero-actions"><Link href="/virtual-store" className="button-primary">Enter the 3D store <span aria-hidden="true">→</span></Link><Link href="#how-it-works" className="button-secondary">See how it works</Link></div>
          <p className="hero-footnote">Early prototype · Built for the web · More to come</p>
        </div>
        <Link href="/virtual-store" className="hero-visual" aria-label="Explore the interactive 3D store">
          <div className="visual-grid" />
          <div className="visual-orbit orbit-one" /><div className="visual-orbit orbit-two" />
          <div className="visual-card card-top"><span className="card-dot" /> YOUR STORE, REIMAGINED</div>
          <div className="aisle-scene">
            <div className="aisle-light" />
            <div className="aisle-shelf shelf-left"><i /><i /><i /><i /><i /><i /></div>
            <div className="aisle-shelf shelf-right"><i /><i /><i /><i /><i /><i /></div>
            <div className="aisle-floor" />
            <div className="aisle-sign">FRESH FINDS <span>↓</span></div>
          </div>
          <div className="visual-card card-bottom"><span className="mini-cube">◇</span><span><strong>Step inside</strong><small>Explore at your own pace</small></span><span className="round-arrow">↗</span></div>
        </Link>
      </section>

      <section id="how-it-works" className="feature-section">
        <div className="section-heading"><p className="eyebrow">THE EXPERIENCE</p><h2>Online shopping, with a sense of place.</h2><p>Built to bring the discovery of a physical store into the convenience of online commerce.</p></div>
        <div className="feature-grid">{highlights.map((item) => <article className="feature-card" key={item.number}><span className="feature-number">{item.number}</span><h3>{item.title}</h3><p>{item.description}</p></article>)}</div>
      </section>

      <section className="bottom-cta"><div><p className="eyebrow">THE FIRST AISLE IS OPEN</p><h2>Curiosity looks good on you.</h2></div><Link href="/virtual-store" className="button-primary">Explore the prototype <span aria-hidden="true">→</span></Link></section>
      <footer className="site-footer"><Link href="/" className="brand-mark"><span className="brand-icon">v</span><span>virtual<span className="brand-light">store</span></span></Link><p>Original concept. Early prototype. Built for better ways to shop.</p><span>© 2026 Virtual Store Commerce</span></footer>
    </main>
  );
}
