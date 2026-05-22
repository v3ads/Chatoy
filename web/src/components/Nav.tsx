"use client";

import Link from "next/link";

export default function Nav() {
  return (
    <header className="sticky top-0 z-50 border-b border-white/5 bg-surface/85 backdrop-blur-xl">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <Link href="/" className="text-2xl font-bold tracking-tight text-text-primary">
          Mytho<span className="text-accent">Stack</span>
        </Link>
        <nav className="hidden items-center gap-8 text-sm font-medium text-text-secondary md:flex">
          <Link href="/#how" className="hover:text-text-primary transition-colors">How it works</Link>
          <Link href="/#pricing" className="hover:text-text-primary transition-colors">Pricing</Link>
          <Link href="/login" className="hover:text-text-primary transition-colors">Log in</Link>
          <Link href="/login" className="rounded-lg bg-accent px-5 py-2 text-sm font-semibold text-surface transition-colors hover:bg-accent-dim">
            Get Early Access
          </Link>
        </nav>
        <Link href="/login" className="rounded-lg bg-accent px-5 py-2 text-sm font-semibold text-surface md:hidden">
          Join Waitlist
        </Link>
      </div>
    </header>
  );
}
