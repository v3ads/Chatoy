import Link from "next/link";

export default function Nav() {
  return (
    <header className="border-b border-surface-border">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <Link href="/" className="text-lg font-semibold tracking-tight">
          Mytho<span className="text-accent">Stack</span>
        </Link>
        <nav className="flex items-center gap-5 text-sm text-text-secondary">
          <Link href="/#how" className="hidden hover:text-text-primary sm:inline">
            How it works
          </Link>
          <Link href="/#pricing" className="hidden hover:text-text-primary sm:inline">
            Pricing
          </Link>
          <Link href="/login" className="hover:text-text-primary">
            Log in
          </Link>
          <Link
            href="/login"
            className="rounded-md bg-accent px-3.5 py-1.5 font-medium text-surface hover:opacity-90"
          >
            Get started
          </Link>
        </nav>
      </div>
    </header>
  );
}
