"use client";

import Link from "next/link";
import MobileMenu from "@/components/MobileMenu";

const LINKS = [
  { href: "/#how", label: "How it works" },
  { href: "/#pricing", label: "Pricing" },
  { href: "/voice", label: "Voice" },
  { href: "/login", label: "Log in" },
];

export default function Nav() {
  return (
    <header className="sticky top-0 z-50 border-b border-white/5 bg-surface/85 backdrop-blur-xl">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <Link href="/" className="text-2xl font-bold tracking-tight text-text-primary">
          Mytho<span className="text-accent">Stack</span>
        </Link>
        <nav className="hidden items-center gap-8 text-sm font-medium text-text-secondary md:flex">
          {LINKS.map((l) => (
            <Link key={l.href} href={l.href} className="hover:text-text-primary transition-colors">
              {l.label}
            </Link>
          ))}
          <Link href="/login" className="rounded-lg bg-accent px-5 py-2 text-sm font-semibold text-surface transition-colors hover:bg-accent-dim">
            Get Early Access
          </Link>
        </nav>
        <div className="md:hidden">
          <MobileMenu triggerClassName="border-white/10">
            {(close) => (
              <nav className="flex flex-col gap-1">
                {LINKS.map((l) => (
                  <Link
                    key={l.href}
                    href={l.href}
                    onClick={close}
                    className="rounded-lg px-3 py-2.5 text-sm font-medium text-text-secondary transition-colors hover:bg-surface-border hover:text-text-primary"
                  >
                    {l.label}
                  </Link>
                ))}
                <Link
                  href="/login"
                  onClick={close}
                  className="mt-2 rounded-lg bg-accent px-3 py-2.5 text-center text-sm font-semibold text-surface transition-colors hover:bg-accent-dim"
                >
                  Get Early Access
                </Link>
              </nav>
            )}
          </MobileMenu>
        </div>
      </div>
    </header>
  );
}

