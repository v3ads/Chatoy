from __future__ import annotations

from typing import Protocol

# Generic, public-knowledge direct-response frameworks keyed by asset type.
# A production build swaps this for a vector DB (Chroma/Pinecone) seeded with a
# larger corpus and retrieved by semantic similarity. We deliberately describe
# frameworks rather than reproduce any copyrighted source material.
_DEFAULT_FRAMEWORKS: dict[str, list[str]] = {
    "email_promo": [
        "PAS: open on the reader's Problem, Agitate the cost of inaction, then "
        "present your offer as the Solution with a single CTA.",
        "Curiosity subject line + one big idea per email; the only job of each "
        "line is to get the next line read.",
        "Stack one specific, believable proof point (number, before/after, "
        "testimonial) immediately before the call to action.",
    ],
    "landing_page": [
        "Above the fold: outcome-driven headline, one-line subhead naming the "
        "mechanism, and a single primary CTA.",
        "AIDA: Attention (headline) -> Interest (the problem you solve) -> "
        "Desire (proof + benefits) -> Action (CTA repeated after each section).",
        "Handle the top 3 objections explicitly (price, time, risk) and add a "
        "risk-reversal/guarantee near the button.",
    ],
    "lead_magnet": [
        "Promise one specific, fast win the prospect can achieve today; narrow "
        "beats comprehensive.",
        "Title formula: [Number] + [desirable outcome] + [time frame / without "
        "pain], e.g. '7 emails that booked 3 demos in a week'.",
        "End with a low-friction next step that bridges to the paid offer.",
    ],
    "sales_page": [
        "Long-form structure: hook -> problem -> unique mechanism -> offer -> "
        "proof -> bonuses -> guarantee -> price justification -> CTA -> FAQ.",
        "Sell the transformation and the mechanism, not the feature list.",
        "Use a value stack so the price feels small next to the outcome.",
    ],
    "ad": [
        "Pattern-interrupt hook in the first line; speak to one audience and one "
        "pain.",
        "One promise, one proof, one CTA — never split attention.",
        "Match the ad's promise to the landing page headline (message match).",
    ],
}

_GENERIC = [
    "PAS (Problem-Agitate-Solution): name the pain, make it vivid, resolve it.",
    "AIDA: Attention, Interest, Desire, Action.",
    "Lead with the single sharpest benefit; one idea, one CTA.",
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
