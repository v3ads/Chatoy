from __future__ import annotations

from typing import Protocol

# Generic, public-knowledge direct-response frameworks keyed by asset type.
# A production build swaps this for a vector DB (Chroma/Pinecone) seeded with a
# larger corpus and retrieved by semantic similarity. We deliberately describe
# frameworks rather than reproduce any copyrighted source material.
_DEFAULT_FRAMEWORKS: dict[str, list[str]] = {
    "email_promo": [
        "BAB (Before-After-Bridge): describe the current pain (Before), paint the "
        "ideal world without it (After), and show how your product is the only "
        "way to get there (Bridge).",
        "The '9-Word Email' approach: 'Are you still looking for help with [Problem]?' "
        "Use this for re-engagement or low-friction lead generation.",
        "Intent-Driven Lifecycle: Use email automation and knowledge bases to "
        "reduce friction and generate speed in the customer journey.",
        "Soft CTA: Instead of 'Buy Now', use 'Mind if I send more info?' or "
        "'Would you be against a quick chat?' to lower friction.",
    ],
    "landing_page": [
        "The PASTOR Framework: Problem (identify it), Amplify (the cost of inaction), "
        "Story/Solution (the fix), Transformation/Testimonial (proof), Offer (the deal), "
        "Response (the CTA).",
        "Above the fold: outcome-driven headline, one-line subhead naming the "
        "unique mechanism, and a single primary CTA.",
        "STDC (See-Think-Do-Care): Organize the landing page content to serve "
        "different intent stages, from broad awareness to specific action.",
        "The 5 Basic Objections Filter: explicitly address Lack of Time, Lack of Money, "
        "Lack of Trust, 'It won't work for me', and 'I don't need it now'.",
    ],
    "lead_magnet": [
        "The 'Specific Win' Formula: Promise one specific, fast win the prospect "
        "can achieve today; narrow beats comprehensive.",
        "Title formula: [Number] + [desirable outcome] + [time frame / without "
        "pain], e.g. '7 emails that booked 3 demos in a week'.",
        "The 'Bridge' Strategy: The lead magnet should solve a *symptom* but "
        "highlight a *root cause* that only your paid product solves.",
    ],
    "sales_page": [
        "The Star-Story-Solution: introduce a relatable Star, tell their Story of "
        "struggle, and present your product as the only logical Solution.",
        "The 4 C's Checklist: ensure every section is Clear (no jargon), Concise "
        "(no fluff), Compelling (emotional), and Credible (backed by data/proof).",
        "The Value Stack: list everything they get, assign a higher value to each, "
        "then reveal the actual price as a fraction of that total value.",
    ],
    "ad": [
        "Pattern-Interrupt Hook: start with a bold statement or a question that "
        "stops the scroll in the first 3 seconds.",
        "PESO Model Alignment: Ensure the ad (Paid) integrates with Shared and "
        "Owned channels to provide a coherent narrative pipe.",
        "PPPP: Picture (paint the dream), Promise (how you deliver), Prove (social "
        "proof), Push (direct CTA).",
        "Message Match: Ensure the ad's core promise and tone exactly match the "
        "landing page headline to reduce bounce rates.",
    ],
    "strategy": [
        "The 3Cs Framework: Analyze Customer (intent signals), Company (USP/genius), "
        "and Competitor (gap analysis) to find the 'white space' for positioning.",
        "The STP Model: Segment based on size/growth, Target based on accessibility, "
        "and Position based on sustainable LTV:CAC ratios (aim for 3:1+).",
        "AARRR (Pirate Metrics): Focus on fixing the 'leaky bucket' (Retention) "
        "before scaling Acquisition spend.",
    ]
}

_GENERIC = [
    "PAS (Problem-Agitate-Solve): name the pain, make it vivid, resolve it.",
    "AIDA: Attention, Interest, Desire, Action.",
    "The Four C's: Clear, Concise, Compelling, Credible.",
    "STDC (See-Think-Do-Care): Match content to the user's current intent stage.",
]


class FrameworkRetriever(Protocol):
    def retrieve(self, asset_type: str, k: int = 3) -> list[str]: ...


class InMemoryFrameworkRetriever:
    """Keyword-matched retriever over a small built-in corpus.

    Implements the same ``retrieve`` contract a vector-DB-backed retriever
    would, so it can be swapped without touching the agents.
    """

    def __init__(self, frameworks: dict[str, list[str]] | None = None) -> None:
        self._frameworks = frameworks or _DEFAULT_FRAMEWORKS

    def retrieve(self, asset_type: str, k: int = 3) -> list[str]:
        if not asset_type:
            return _GENERIC[:k]
        key = asset_type.strip().lower().replace(" ", "_").replace("-", "_")
        if key in self._frameworks:
            return self._frameworks[key][:k]
        # Loose contains-match (e.g. "promotional_email" -> "email_promo").
        for name, items in self._frameworks.items():
            tokens = name.split("_")
            if any(tok in key for tok in tokens):
                return items[:k]
        return _GENERIC[:k]
