"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { isSupabaseConfigured, supabase } from "@/lib/supabase";
import { formatCredits } from "@/lib/api";
import { initialOf, useAccount } from "@/lib/useAccount";

/** Shared navigation for the authenticated app, used inside the mobile drawer on
 * every app page. Shows the user's avatar + credits (linking to the account
 * page), the nav links, and logout. The Admin link only appears for admins. */
export default function AppMenuLinks({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();
  const router = useRouter();
  const { email, isAdmin, credits } = useAccount();

  const links = [
    { href: "/chat", label: "Architect" },
    { href: "/voice", label: "Voice" },
    { href: "/account", label: "Profile & billing" },
    ...(isAdmin ? [{ href: "/admin", label: "Admin" }] : []),
    { href: "/", label: "Home" },
  ];

  async function logout() {
    onNavigate?.();
    await supabase?.auth.signOut();
    router.replace("/");
  }

  return (
    <div className="flex flex-col gap-3">
      <Link
        href="/account"
        onClick={onNavigate}
        className="flex items-center gap-3 rounded-xl border border-surface-border bg-surface-card p-3 transition-colors hover:border-accent"
      >
        <span className="flex h-10 w-10 items-center justify-center rounded-full bg-accent/15 text-sm font-bold text-accent">
          {initialOf(email)}
        </span>
        <div className="min-w-0">
          <div className="truncate text-sm font-medium text-text-primary">
            {email ?? "Account"}
          </div>
          <div className="text-xs text-text-muted">{formatCredits(credits)} credits</div>
        </div>
      </Link>

      <nav className="flex flex-col gap-1">
        {links.map((l) => {
          const active = pathname === l.href;
          return (
            <Link
              key={l.href}
              href={l.href}
              onClick={onNavigate}
              className={`rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
                active
                  ? "bg-accent/10 text-accent"
                  : "text-text-secondary hover:bg-surface-border hover:text-text-primary"
              }`}
            >
              {l.label}
            </Link>
          );
        })}
        {isSupabaseConfigured && (
          <button
            type="button"
            onClick={() => void logout()}
            className="mt-2 rounded-lg px-3 py-2.5 text-left text-sm font-medium text-red-400 transition-colors hover:bg-red-900/20"
          >
            Log out
          </button>
        )}
      </nav>
    </div>
  );
}
