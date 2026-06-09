# Zeus Voice AI — Buyer's Guide

## What You're Buying

A **complete, ready-to-deploy voice AI web app** that you can:
- Rebrand as your own product
- Sell as a monthly SaaS ($10-15/user/mo)
- Use as a lead magnet or portfolio piece

## What It Does

Users sign in with Google, then talk to their:
- **Gmail** — read emails, check inbox ("Read my latest email")
- **Calendar** — check schedule, upcoming events ("What's on my calendar today?")  
- **Web search** — look up anything ("Search for AI voice startups")
- **General chat** — conversational AI, ask anything

All hands-free, voice in and voice out.

## How to Sell It

### Option A: Sell as SaaS ($10-15/mo)

- Deploy once on Vercel + Render
- The `.env` already has your API keys — users just sign in with Google
- Add a simple Stripe checkout page (use Stripe Checkout, 30 min setup)
- Charger per user/month — users get their own Google-linked assistant

**Target market:** Busy professionals, small business owners, executives
**Why they pay:** Hands-free email + calendar management. Saves time.

### Option B: Sell the Source Code as a Product

- List on **Acquire.com** as "Turnkey Voice AI Web App"
- List on **Gumroad** for $29-97 (source code + deploy guide)
- Pitch: *"Build your own AI assistant SaaS in 30 minutes"*

**Target buyer:** Solo founders, no-code entrepreneurs, people who want to start an AI business

## Pricing Strategy

| Approach | Price | Why |
|:---------|:-----:|:----|
| Source code sale | $29-97 | One-time, no support overhead |
| SaaS monthly | $10-15/mo | Recurring revenue |
| SaaS annual | $99-149/yr | Better retention |
| White-label license | $500-1,500 | Premium package + rights |

## Marketing Angles

1. **"Your personal AI executive assistant"** — Focus on email + calendar
2. **"Talk to your inbox"** — Hands-free email for busy people
3. **"Jarvis for your browser"** — The voice assistant everyone wanted
4. **"No subscriptions, no API keys"** — For the source code sale

## What to Customize Before Selling

| What | Where | How |
|:-----|:------|:----|
| Brand name | `frontend/index.html` | Search/replace "Zeus" |
| Logo/icon | `frontend/` | Replace SVG logo |
| Colors | `frontend/style.css` | Change `#00d4ff` accent |
| Domain | Vercel settings | Add custom domain |
| TTS voice | `backend/main.py:204` | Change voice name |
| Welcome message | `frontend/index.html:30` | First bot message |

## Technical Support (for you)

- Deployment guide covers Vercel + Render step-by-step
- Backend is 1 Python file
- Frontend is 3 files (HTML + CSS + JS)
- Buyer doesn't touch code unless they want to rebrand
- All API keys are free-tier: Groq (free), Google (free)

## ROI Estimate

| Scenario | Users | Price | Revenue |
|:---------|:-----:|:-----:|:-------:|
| Sell source code | 1 buyer | $497 | $497 |
| Small SaaS launch | 10 users @ $15/mo | $150/mo | $1,800/yr |
| Medium SaaS | 50 users @ $15/mo | $750/mo | $9,000/yr |
| White-label sale | 1 buyer | $1,500 | $1,500 |
