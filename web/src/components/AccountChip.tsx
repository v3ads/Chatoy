"use client";

import Link from "next/link";
import { formatCredits } from "@/lib/api";
import { initialOf, useAccount } from "@/lib/useAccount";

/** Compact avatar + credit balance, linking to the account/billing page.
 * Used in the desktop app header. */
export default function AccountChip() {
  const { email, credits } = useAccount();
  return (
    <Link
      href="/account"
      title={email ?? "Account"}
      className="flex items-center gap-2 rounded-full border border-surface-border bg-surface-card py-1 pl-1 pr-3 transition-colors hover:border-accent"
    >
      <span className="flex h-7 w-7 items-center justify-center rounded-full bg-accent/15 text-xs font-bold text-accent">
        {initialOf(email)}
      </span>
      <span className="text-xs font-bold uppercase tracking-wider text-text-secondary">
        {formatCredits(credits)} credits
      </span>
    </Link>
  );
}
