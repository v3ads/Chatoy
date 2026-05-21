"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Chat from "@/components/Chat";
import { isSupabaseConfigured, supabase } from "@/lib/supabase";

export default function ChatPage() {
  const router = useRouter();
  // When Supabase isn't configured we run in dev-token mode and let you in.
  const [ready, setReady] = useState(!isSupabaseConfigured);
  const [email, setEmail] = useState<string | null>(null);

  useEffect(() => {
    if (!isSupabaseConfigured || !supabase) return;
    supabase.auth.getSession().then(({ data }) => {
      if (!data.session) {
        router.replace("/login");
        return;
      }
      setEmail(data.session.user.email ?? null);
      setReady(true);
    });
  }, [router]);

  async function logout() {
    await supabase?.auth.signOut();
    router.replace("/");
  }

  if (!ready) {
    return <div className="p-8 text-text-muted">Loading…</div>;
  }

  return (
    <Chat
      userEmail={email}
      onLogout={isSupabaseConfigured ? logout : undefined}
    />
  );
}
