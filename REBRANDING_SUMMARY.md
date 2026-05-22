# MythoStack Rebranding Summary

This document tracks all changes made to transform "Chatoy" into "MythoStack," a unique multi-agent AI marketing SaaS.

## 🎯 Brand Positioning

**From**: Chatoy (generic AI tool)  
**To**: MythoStack — "Every campaign builds on the last"

**Core Positioning**: Growth Architect (AI strategist) + Asset Engine (AI copywriter) → Compounding growth

## 📝 Files Modified

### Backend Agent Roles (Lexicon Purge)

| File | Changes |
| :--- | :--- |
| `app/agents/cro.py` | Renamed to `app/agents/architect.py` |
| `app/agents/shepherd.py` | Renamed to `app/agents/writer.py` |
| `app/agents/graph.py` | Updated imports to use `architect.py` and `writer.py` |
| `app/agents/prompts.py` | Updated system prompts: "CRO" → "Growth Architect", "Project Shepherd" → "Asset Engine" |

### Configuration & Environment

| File | Changes |
| :--- | :--- |
| `app/config.py` | Renamed `cro_model` → `architect_model`, `shepherd_model` → `writer_model`; Updated env prefix `CHATOY_` → `MYTHOSTACK_` |
| `app/llm/factory.py` | Updated default role from `"cro"` to `"architect"` |
| `app/llm/fake.py` | Updated docstring and role detection to use new agent names; Updated env var reference to `MYTHOSTACK_` |
| `app/main.py` | Updated LLM builder calls to use `role="architect"` and `role="writer"` |
| `.env.example` | Updated all `CHATOY_*` variables to `MYTHOSTACK_*`; Renamed role-specific vars |

### Documentation

| File | Changes |
| :--- | :--- |
| `README.md` | Complete rewrite with MythoStack branding and positioning |
| `ARCHITECTURE.md` | Updated to describe "Growth Architect" and "Asset Engine" roles; Updated env var references |

### Tests

| File | Changes |
| :--- | :--- |
| `tests/test_graph.py` | Updated test names and comments to reflect new agent roles |

## 🔄 Terminology Mapping

| Old Term | New Term | Context |
| :--- | :--- | :--- |
| Chief Revenue Officer (CRO) | Growth Architect | Strategic agent role |
| Project Shepherd | Asset Engine | Copywriting agent role |
| CRO node | Architect node | Graph node naming |
| Shepherd node | Writer node | Graph node naming |
| `cro_model` | `architect_model` | Config variable |
| `shepherd_model` | `writer_model` | Config variable |
| `CHATOY_*` | `MYTHOSTACK_*` | Environment variable prefix |
| "Stacking Wins" | "Compounding Wins" | Memory/results terminology |

## ✅ Verification Checklist

- [x] All Python files compile without syntax errors
- [x] Graph imports updated to use new module names
- [x] System prompts reflect new agent terminology
- [x] Environment variable prefix updated globally
- [x] Configuration role mappings updated
- [x] Documentation reflects new branding
- [x] Test names and comments updated
- [x] Fake LLM behavior updated for new agent names

## 📋 Remaining Tasks (Phase 3)

1. **Stripe Integration**: Payment processing for Pro/Team plans
2. **Voice Sample Uploads**: Frontend UI for voice training
3. **Results Logging**: Campaign results tracking and feedback loop

## 🚀 Deployment Notes

When deploying to production:

1. Update environment variables from `CHATOY_*` to `MYTHOSTACK_*`
2. Ensure Supabase JWT configuration uses `MYTHOSTACK_SUPABASE_URL` or `MYTHOSTACK_JWT_SECRET`
3. Update CORS origins to include `mythostack.com` and `api.mythostack.com`
4. Database migrations (if any) should use `MYTHOSTACK_DATABASE_URL`

## 🔐 Security Notes

- All tenant isolation and JWT verification remains unchanged
- Voice profiles and asset logs are still user-scoped
- No breaking changes to authentication or authorization flows
