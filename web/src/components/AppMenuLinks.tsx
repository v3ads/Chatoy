"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { isSupabaseConfigured, supabase } from "@/lib/supabase";
import { getMe } from "@/lib/api";

/** Shared navigation links + logout for the authenticated app, used inside the
 * mobile drawer on every app page. The Admin link only appears for admins. */
export default function AppMenuLinks({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();
  const router = useRouter();
  const [isAdmin, setIsAdmin] = useState(false);

  useEffect(() => {
    let active = true;
    getMe()
      .then((m) => {
        if (active) setIsAdmin(m.is_admin);
      })
      .catch(() => {});
    return () => {
      active = false;
    };
  }, []);

  const links = [
    { href: "/chat", label: "Architect" },
    { href: "/voice", label: "Voice" },
    ...(isAdmin ? [{ href: "/admin", label: "Admin" }] : []),
    { href: "/", label: "Home" },
  ];

  async function logout() {
    onNavigate?.();
    await supabase?.auth.signOut();
    router.replace("/");
  }

  return (
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
  );
}
