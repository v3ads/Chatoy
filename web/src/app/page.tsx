import Link from "next/link";
import Nav from "@/components/Nav";

export default function Home() {
  return (
    <div className="flex min-h-screen flex-col">
      <Nav />
      
      <main className="flex-grow">
        {/* Hero Section */}
        <section className="relative overflow-hidden bg-surface pb-24 pt-32 text-center">
          <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_50%_0%,#1F1740_0%,#0C0B1A_70%)] opacity-50" />
          <div className="container relative mx-auto max-w-6xl px-6">
            <h1 className="mx-auto max-w-4xl font-serif text-5xl font-bold leading-[1.15] tracking-tight text-text-primary md:text-7xl">
              Every campaign<br />builds on the last.
            </h1>
            <p className="mx-auto mt-8 max-w-2xl text-xl leading-relaxed text-text-secondary">
              MythoStack is an AI marketing architect. It studies your business, identifies the highest-leverage move, and builds complete campaigns that compound — without you writing a single prompt.
            </p>
            <div className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row">
              <Link href="/login" className="rounded-lg bg-accent px-8 py-4 text-lg font-semibold text-surface transition-colors hover:bg-accent-dim">
                Join the Waitlist <span className="ml-2">→</span>
              </Link>
            </div>
            <p className="mt-6 text-sm text-text-muted">Free 7-day trial. No credit card.</p>
          </div>
        </section>

        {/* The Core Loop */}
        <section id="how" className="bg-surface-elevated py-24">
          <div className="container mx-auto max-w-6xl px-6">
            <div className="mb-16 text-center">
              <span className="text-xs font-bold uppercase tracking-[0.2em] text-accent">How it works</span>
              <h2 className="mt-4 font-serif text-4xl font-bold text-text-primary md:text-5xl">
                A system that gets smarter<br />the more you use it.
              </h2>
            </div>
            
            <div className="grid gap-8 md:grid-cols-3">
              {[
                {
                  num: "01",
                  title: "Analyze",
                  desc: "It reads your business — products, customers, past campaigns — and surfaces the one move that will move revenue the most, right now. No guesswork."
                },
                {
                  num: "02",
                  title: "Build",
                  desc: "Writes the entire campaign in your voice. Emails, landing pages, upsell offers. Complete and ready to ship. You copy it in and it runs."
                },
                {
                  num: "03",
                  title: "Compound",
                  desc: "Feed it the results. It learns what worked, adjusts its model of your audience, and starts building the next campaign. Each one stacks on the last."
                }
              ].map((step, i) => (
                <div key={i} className="rounded-2xl border border-surface-border bg-surface-card p-8 transition-transform hover:-translate-y-1">
                  <div className="font-serif text-5xl font-bold text-accent/20">{step.num}</div>
                  <h3 className="mt-4 text-xl font-semibold text-text-primary">{step.title}</h3>
                  <p className="mt-4 text-text-secondary leading-relaxed">{step.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Flow Section */}
        <section className="bg-surface py-24">
          <div className="container mx-auto max-w-6xl px-6 text-center">
            <span className="text-xs font-bold uppercase tracking-[0.2em] text-accent">From input to revenue</span>
            <h2 className="mt-4 font-serif text-4xl font-bold text-text-primary md:text-5xl">
              You provide the business.<br />It provides the growth.
            </h2>
            
            <div className="mt-16 flex flex-col items-start justify-between gap-12 md:flex-row">
              {[
                { icon: "📋", title: "Describe your business", desc: "Products, audience, what's working. Simple onboarding — 10 minutes." },
                { icon: "🧠", title: "It finds the opportunity", desc: "Proprietary model identifies the highest-ROI action." },
                { icon: "✍️", title: "It writes your voice", desc: "Learns your tone from samples. Output reads like you wrote it." },
                { icon: "🚀", title: "You deploy and track", desc: "Paste the campaign into your tools. Watch the compound effect." }
              ].map((step, i) => (
                <div key={i} className="flex flex-1 flex-col items-center gap-4">
                  <div className="flex h-16 w-16 items-center justify-center rounded-full border border-surface-border bg-surface-card text-3xl">
                    {step.icon}
                  </div>
                  <h4 className="font-semibold text-text-primary">{step.title}</h4>
                  <p className="text-sm text-text-secondary leading-relaxed max-w-[200px]">{step.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Comparison Section */}
        <section className="bg-surface-elevated py-24">
          <div className="container mx-auto max-w-6xl px-6">
            <div className="mb-16 text-center">
              <span className="text-xs font-bold uppercase tracking-[0.2em] text-accent">The difference</span>
              <h2 className="mt-4 font-serif text-4xl font-bold text-text-primary md:text-5xl">
                Not another text generator.
              </h2>
            </div>
            
            <div className="grid gap-8 md:grid-cols-2">
              <div className="rounded-2xl border border-surface-border bg-surface-card p-10 opacity-60">
                <h3 className="text-xl font-semibold text-text-muted">Conventional AI Tools</h3>
                <ul className="mt-8 space-y-4">
                  {["You decide what to write", "Generic tone — obvious AI", "Same quality every output", "No memory of past results"].map((item, i) => (
                    <li key={i} className="flex items-start gap-3 text-text-muted">
                      <span className="font-bold">✕</span> {item}
                    </li>
                  ))}
                </ul>
              </div>
              <div className="rounded-2xl border border-accent/30 bg-gradient-to-b from-[#1F1740] to-surface-card p-10 ring-1 ring-accent/20">
                <h3 className="text-xl font-semibold text-text-primary">MythoStack</h3>
                <ul className="mt-8 space-y-4">
                  {["It decides the strategy and picks the move", "Learns your voice — reads like you", "Improves with every result you feed back", "Builds on previous wins — compound growth"].map((item, i) => (
                    <li key={i} className="flex items-start gap-3 text-text-primary">
                      <span className="font-bold text-accent">✓</span> {item}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        </section>

        {/* Pricing Section */}
        <section id="pricing" className="bg-surface py-24">
          <div className="container mx-auto max-w-6xl px-6">
            <div className="mb-16 text-center">
              <span className="text-xs font-bold uppercase tracking-[0.2em] text-accent">Pricing</span>
              <h2 className="mt-4 font-serif text-4xl font-bold text-text-primary md:text-5xl">
                One plan. Everything included.
              </h2>
            </div>
            
            <div className="grid gap-8 md:grid-cols-3">
              <div className="flex flex-col rounded-2xl border border-surface-border bg-surface-card p-8 text-center">
                <h3 className="text-lg font-semibold">Starter</h3>
                <div className="my-6 font-serif text-5xl font-bold text-text-primary">$0</div>
                <p className="mb-8 text-sm text-text-secondary">7-day full access. No card required. See what it can build for your business.</p>
                <Link href="/login" className="rounded-lg border border-surface-border bg-surface-card px-5 py-2.5 text-center font-semibold text-text-primary transition-colors hover:bg-surface-border mt-auto">Start Free Trial</Link>
              </div>
              <div className="flex flex-col rounded-2xl border-2 border-accent bg-gradient-to-b from-[#1F1740] to-surface-card p-8 text-center ring-1 ring-accent/20">
                <h3 className="text-lg font-semibold">Pro</h3>
                <div className="my-6 font-serif text-5xl font-bold text-text-primary">$99<span className="text-lg font-normal text-text-muted">/mo</span></div>
                <p className="mb-8 text-sm text-text-secondary">Unlimited campaigns. Voice training. Full campaign builder. Priority support.</p>
                <Link href="/login" className="rounded-lg bg-accent px-5 py-2.5 text-center font-semibold text-surface transition-colors hover:bg-accent-dim mt-auto">Get Started</Link>
              </div>
              <div className="flex flex-col rounded-2xl border border-surface-border bg-surface-card p-8 text-center opacity-80">
                <h3 className="text-lg font-semibold">Team</h3>
                <div className="my-6 font-serif text-5xl font-bold text-text-primary">$199<span className="text-lg font-normal text-text-muted">/mo</span></div>
                <p className="mb-8 text-sm text-text-secondary">Up to 3 seats. Shared library. Team voice profiles. Coming Q2 2027.</p>
                <button disabled className="rounded-lg border border-surface-border bg-surface-card px-5 py-2.5 text-center font-semibold text-text-muted mt-auto cursor-not-allowed">Join Waitlist</button>
              </div>
            </div>
          </div>
        </section>

        {/* Testimonials */}
        <section className="bg-surface-elevated py-24">
          <div className="container mx-auto max-w-6xl px-6">
            <div className="mb-16 text-center">
              <span className="text-xs font-bold uppercase tracking-[0.2em] text-accent">What early users say</span>
              <h2 className="mt-4 font-serif text-4xl font-bold text-text-primary md:text-5xl">
                Beta access coming soon.
              </h2>
            </div>
            
            <div className="grid gap-8 md:grid-cols-2">
              <div className="rounded-2xl border border-surface-border bg-surface-card p-8">
                <blockquote className="italic text-text-secondary leading-relaxed">
                  "I've tried every AI copy tool. They all required me to know what to ask. The idea that an AI can look at my whole business and tell me 'do this next' — that's the upgrade I've been waiting for."
                </blockquote>
                <div className="mt-6 text-sm font-semibold text-accent">— Beta Waitlist Member</div>
              </div>
              <div className="rounded-2xl border border-surface-border bg-surface-card p-8">
                <blockquote className="italic text-text-secondary leading-relaxed">
                  "My stack is already full of tools. I don't need another interface. I need something that actually makes decisions and produces finished work. That's the pitch that got me to sign up."
                </blockquote>
                <div className="mt-6 text-sm font-semibold text-accent">— Early Access Subscriber</div>
              </div>
            </div>
          </div>
        </section>

        {/* Final CTA */}
        <section className="bg-surface py-32 text-center">
          <div className="container mx-auto max-w-4xl px-6">
            <h2 className="font-serif text-4xl font-bold text-text-primary md:text-5xl">
              Ready to build a marketing engine<br />that compounds?
            </h2>
            <p className="mt-6 text-xl text-text-secondary">
              Join the waitlist. First cohort gets founding-member pricing and direct input on the roadmap.
            </p>
            <div className="mt-10">
              <Link href="/login" className="rounded-lg bg-accent px-10 py-4 text-lg font-semibold text-surface transition-colors hover:bg-accent-dim">
                Get Early Access <span className="ml-2">→</span>
              </Link>
            </div>
          </div>
        </section>
      </main>

      <footer className="border-t border-surface-border bg-surface py-12 text-center">
        <p className="text-sm text-text-muted">
          MythoStack &copy; 2026 &nbsp;·&nbsp; Every campaign builds on the last.
        </p>
      </footer>
    </div>
  );
}
