import Link from "next/link";

export default function Footer() {
  const year = new Date().getFullYear();
  return (
    <footer className="border-t border-surface-border">
      <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-3 px-6 py-8 text-sm text-text-muted sm:flex-row">
        <p>© {year} MythoStack</p>
        <nav className="flex items-center gap-5">
          <Link href="/privacy" className="hover:text-text-secondary">
            Privacy
          </Link>
          <Link href="/terms" className="hover:text-text-secondary">
            Terms
          </Link>
          <Link href="/login" className="hover:text-text-secondary">
            Log in
          </Link>
        </nav>
      </div>
    </footer>
  );
}
