"use client";

import { useEffect, useState } from "react";

/**
 * A left-hand slide-in navigation drawer for small screens. Renders a hamburger
 * trigger (hidden on lg+) and an overlay panel. Children are a render function
 * that receives `close` so links/actions can dismiss the drawer.
 */
export default function MobileMenu({
  children,
  triggerClassName = "",
}: {
  children: (close: () => void) => React.ReactNode;
  triggerClassName?: string;
}) {
  const [open, setOpen] = useState(false);
  const close = () => setOpen(false);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") close();
    };
    document.addEventListener("keydown", onKey);
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = prev;
    };
  }, [open]);

  return (
    <>
      <button
        type="button"
        aria-label="Open navigation menu"
        aria-expanded={open}
        onClick={() => setOpen(true)}
        className={`inline-flex h-10 w-10 items-center justify-center rounded-lg border border-surface-border bg-surface-card text-text-primary transition-colors hover:bg-surface-border lg:hidden ${triggerClassName}`}
      >
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
          <path d="M3 6h18M3 12h18M3 18h18" />
        </svg>
      </button>

      {open && (
        <div className="fixed inset-0 z-[60] lg:hidden" role="dialog" aria-modal="true">
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={close} />
          <div className="absolute inset-y-0 left-0 flex w-72 max-w-[82%] flex-col gap-2 overflow-y-auto border-r border-surface-border bg-surface-elevated p-5 shadow-2xl">
            <div className="mb-3 flex items-center justify-between">
              <span className="text-xl font-bold tracking-tight text-text-primary">
                Mytho<span className="text-accent">Stack</span>
              </span>
              <button
                type="button"
                onClick={close}
                aria-label="Close menu"
                className="flex h-8 w-8 items-center justify-center rounded-lg text-text-muted transition-colors hover:text-text-primary"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                  <path d="M6 6l12 12M18 6L6 18" />
                </svg>
              </button>
            </div>
            {children(close)}
          </div>
        </div>
      )}
    </>
  );
}
