"use client";

import { useEffect, useState } from "react";
import { getCredits, getMe } from "@/lib/api";

/** Shared account state (identity, admin flag, credit balance) for the header
 * chip, the drawer and the account page. */
export function useAccount() {
  const [email, setEmail] = useState<string | null>(null);
  const [isAdmin, setIsAdmin] = useState(false);
  const [credits, setCredits] = useState<number | null>(null);
  const [autoRecharge, setAutoRecharge] = useState(false);

  useEffect(() => {
    let active = true;
    getMe()
      .then((m) => {
        if (!active) return;
        setEmail(m.email);
        setIsAdmin(m.is_admin);
      })
      .catch(() => {});
    getCredits()
      .then((c) => {
        if (!active) return;
        setCredits(c.credits_balance);
        setAutoRecharge(c.auto_recharge_enabled);
      })
      .catch(() => {});
    return () => {
      active = false;
    };
  }, []);

  return { email, isAdmin, credits, autoRecharge };
}

export function initialOf(email: string | null | undefined): string {
  return (email?.trim()?.[0] ?? "U").toUpperCase();
}
