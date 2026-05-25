"""Seed corpus for the knowledge base.

Original, paraphrased write-ups of well-known direct-response principles. We do
NOT reproduce copyrighted source material (e.g. specific sales letters); these
are concise, original descriptions of public frameworks.
"""
from __future__ import annotations

from app.services.knowledge import KnowledgeChunk

_RAW: list[tuple[str, str]] = [
    # --- general strategy / diagnosis (feeds the Architect) ---
    ("general", "Pick the single highest-leverage asset before writing anything. Diagnose where revenue actually leaks: traffic (top of funnel), conversion (offer/landing), or retention/LTV. Fix the biggest constraint first."),
    ("general", "The market-awareness ladder (Schwartz): unaware, problem-aware, solution-aware, product-aware, most-aware. Match the message to the stage — cold audiences need problem framing; warm audiences need offer and proof."),
    ("general", "An offer beats copy. Strengthen the offer first: stack value, reverse risk with a guarantee, add urgency/scarcity that's real, and make the next step tiny. Great copy on a weak offer still loses."),
    ("general", "One campaign, one objective, one audience, one call to action. Splitting focus halves results. Decide the single action you want and remove everything that doesn't drive it."),
    ("general", "Compounding marketing: log what each asset produced (open rate, conversion, revenue) and let results pick the next move. Double down on what worked; retire what didn't. Each asset should build on the last."),
    ("general", "Voice match is non-negotiable: study the customer's own words from reviews, support tickets, and sales calls. Write in their language, not yours. The closer the copy sounds to their inner monologue, the higher it converts."),

    # --- email promotions ---
    ("email_promo", "PAS (Problem–Agitate–Solve): name the reader's problem, agitate the cost of leaving it unsolved, then present your offer as the relief. Works because it sells the pain of inaction before the solution."),
    ("email_promo", "BAB (Before–After–Bridge): paint the reader's current 'before' state, contrast it with the desirable 'after', then position your product as the bridge between them."),
    ("email_promo", "One idea per email. Each line's only job is to earn the next line. Open with a curiosity or tension hook in the subject and first sentence; never bury the lede."),
    ("email_promo", "Stack a single, specific, believable proof point (a number, before/after, or short testimonial) immediately before the call to action to overcome last-second doubt."),
    ("email_promo", "Subject-line patterns that earn the open: curiosity gap, specific number/result, direct benefit, or a pattern interrupt. Keep it short; the preview text should extend, not repeat, the subject."),
    ("email_promo", "A promo sequence beats a single send: (1) announce + big benefit, (2) handle the top objection, (3) social proof / case study, (4) scarcity/deadline reminder. Most sales come from emails 3–4."),
    ("email_promo", "Write to one person. Use 'you', conversational rhythm, short paragraphs, and a P.S. that restates the core promise and deadline — the P.S. is among the most-read lines."),

    # --- landing pages ---
    ("landing_page", "Above the fold needs three things: an outcome-driven headline, a one-line subhead naming the mechanism/how, and a single primary call to action. The visitor should grasp the promise in five seconds."),
    ("landing_page", "AIDA structure: Attention (headline), Interest (the problem you solve and why now), Desire (proof, benefits, transformation), Action (CTA repeated after each section)."),
    ("landing_page", "Sell benefits and the transformation, not features. Translate every feature into 'which means you…'. Buyers act on the outcome they get, not the spec sheet."),
    ("landing_page", "Handle the top three objections explicitly — price, time, and risk — near the CTA. Add a risk reversal (guarantee, free trial, cancel anytime) right next to the button."),
    ("landing_page", "Use directional cues and visual hierarchy to funnel attention to one CTA. Remove navigation and competing links on a dedicated landing/conversion page to cut leaks."),
    ("landing_page", "Social proof belongs where doubt peaks: logos near the headline, testimonials beside the offer, and specific results (numbers) rather than vague praise."),

    # --- lead magnets ---
    ("lead_magnet", "A great lead magnet promises one specific, fast win the prospect can achieve today. Narrow and immediately useful beats broad and comprehensive."),
    ("lead_magnet", "Title formula: [number] + [desirable outcome] + [time frame / without pain], e.g. '7 emails that booked 3 demos in a week'. Specificity drives opt-ins."),
    ("lead_magnet", "Bridge the magnet to the paid offer: the free win should naturally reveal the next problem your product solves, making the upsell feel like the obvious next step."),

    # --- sales pages ---
    ("sales_page", "Long-form sales structure: hook → problem → unique mechanism → offer → proof → bonuses → guarantee → price justification → CTA → FAQ. Each block answers the next objection in the reader's mind."),
    ("sales_page", "Lead with a unique mechanism — the specific 'how' that makes your solution work and competitors' fail. It reframes the buying decision around your strength."),
    ("sales_page", "Build a value stack: itemize everything the buyer gets with a tangible value for each, sum it, then reveal a price far below the sum so the offer feels like a steal."),
    ("sales_page", "Justify the price by comparison (cost of the problem, cost of alternatives, cost per day) and reverse risk with a concrete guarantee that removes the buyer's downside."),

    # --- ads ---
    ("ad", "Open with a pattern-interrupt hook in the first line that speaks to one audience and one pain. The first three seconds decide whether the rest is read."),
    ("ad", "One promise, one proof, one CTA. Ads that split attention convert worse. Make the single next action unmistakable."),
    ("ad", "Message match: the ad's promise and visual must match the landing page headline. A mismatch between click and landing kills conversion even with great traffic."),
    ("ad", "Test angles, not just creative: different pains, desires, and identities for the same product. The winning angle usually beats a better-looking ad of the wrong angle."),
]

SEED_CHUNKS: list[KnowledgeChunk] = [
    KnowledgeChunk(content=content, asset_type=asset_type, tags=[asset_type])
    for asset_type, content in _RAW
]
