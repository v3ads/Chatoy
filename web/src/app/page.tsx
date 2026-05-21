import Link from "next/link";
import Footer from "@/components/Footer";
import Nav from "@/components/Nav";

export default function Home() {
  return (
    <div className="flex min-h-screen flex-col">
      <Nav />

      <main className="flex-1">
        {/* Hero */}
        <section className="mx-auto max-w-6xl px-6 pb-16 pt-20 text-center">
          <p className="mb-4 inline-block rounded-full bg-accent-soft px-3 py-1 text-xs font-medium text-accent">
            Your AI growth team
          </p>
          <h1 className="mx-auto max-w-3xl text-4xl font-semibold tracking-tight sm:text-5xl">
            A strategist and a copywriter, working as one.
          </h1>
          <p className="mx-auto mt-5 max-w-2xl text-lg text-text-secondary">
            MythoStack interviews you like a Chief Revenue Officer to lock the one
            asset that moves the needle — then writes it in your voice using proven
            direct-response frameworks.
          </p>
          <div className="mt-8 flex items-center justify-center gap-3">
            <Link
              href="/login"
              className="rounded-lg bg-accent px-5 py-2.5 font-medium text-surface hover:opacity-90"
            >
              Start now
            </Link>
            <Link
              href="/#how"
              className="rounded-lg border border-surface-border px-5 py-2.5 font-medium text-text-secondary hover:text-text-primary"
            >
              See how it works
            </Link>
          </div>
        </section>

        {/* How it works */}
        <section id="how" className="border-t border-surface-border bg-surface-elevated/30">
          <div className="mx-auto max-w-6xl px-6 py-16">
            <h2 className="text-center text-2xl font-semibold tracking-tight">
              How it works
            </h2>
            <div className="mt-10 grid gap-6 sm:grid-cols-3">
              <Feature
                step="1"
                title="The CRO interviews you"
                body="A sharp, one-question-at-a-time conversation uncovers the single highest-leverage asset you need right now."
              />
              <Feature
                step="2"
                title="The copywriter ships it"
                body="Project Shepherd writes the asset in your cloned voice, using frameworks pulled from decades of direct response."
              />
              <Feature
                step="3"
                title="Stacking wins"
                body="Log the results. MythoStack remembers what worked and uses it to decide your next move."
              />
            </div>
          </div>
        </section>

        {/* Pricing */}
        <section id="pricing" className="mx-auto max-w-6xl px-6 py-16">
          <h2 className="text-center text-2xl font-semibold tracking-tight">
            Simple pricing
          </h2>
          <div className="mx-auto mt-10 max-w-md rounded-2xl border border-surface-border bg-surface-elevated p-8">
            <div className="flex items-baseline gap-1">
              <span className="text-4xl font-semibold">$99</span>
              <span className="text-text-muted">/month</span>
            </div>
            <p className="mt-2 text-sm text-text-secondary">
              Your always-on growth team. Includes a generous monthly point
              allowance; top up anytime when you need more.
            </p>
            <ul className="mt-6 space-y-2 text-sm text-text-secondary">
              <li>• Unlimited strategy conversations</li>
              <li>• Copy written in your voice</li>
              <li>• Direct-response framework library</li>
              <li>• Results memory that compounds</li>
            </ul>
            <Link
              href="/login"
              className="mt-8 block rounded-lg bg-accent px-5 py-2.5 text-center font-medium text-surface hover:opacity-90"
            >
              Get started
            </Link>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}

function Feature({ step, title, body }: { step: string; title: string; body: string }) {
  return (
    <div className="rounded-xl border border-surface-border bg-surface p-6">
      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-accent-soft text-sm font-semibold text-accent">
        {step}
      </div>
      <h3 className="mt-4 font-medium">{title}</h3>
      <p className="mt-2 text-sm text-text-secondary">{body}</p>
    </div>
  );
}
