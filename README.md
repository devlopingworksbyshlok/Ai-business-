# AI Founders – ₹1000 Cr Business Simulation

Two AI agents (Founder + Co-Founder) start a company from scratch, discuss strategy, divide work, and try to build a **₹1000 Crore** company.

## Features

- **Separate Groq API key** for each agent (no sharing)
- Agents freely choose any business idea
- Realistic customer acquisition, churn, CAC, pricing elasticity, capacity constraints, reputation
- Clean live dashboard with key metrics + charts
- Conversation board shows **only short, main points** with clear speaker labels
- Fast time scale (target 2–3 real minutes ≈ 1 simulated day)
- Hire, marketing, pricing, product investment, capacity decisions

## Quick Start

1. **Install dependencies**
   ```bash
   cd ai_business_sim
   pip install -r requirements.txt
   ```

2. **Add your API keys**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and put one Groq key for Founder and one for Co-Founder:
   ```
   GROQ_API_KEY_FOUNDER=gsk_xxxxxxxx
   GROQ_API_KEY_COFOUNDER=gsk_yyyyyyyy
   ```

3. **Run the app**
   ```bash
   streamlit run app.py
   ```

4. Click **Start Simulation** in the sidebar.

## How to use

- **Next Day + Meeting** → Agents hold a short discussion, make decisions, one simulated day passes
- **Skip 7 Days** → Fast forward a week (lighter activity)
- **Auto-run** → Continuously advances days (adjust sleep time in code for true 2–3 min pace)

The conversation board deliberately keeps messages short (agents are instructed to stay under ~60 words).

## Notes

- Starting capital: ₹50 Lakh
- Valuation is estimated from revenue run-rate, growth signals, team, brand & quality
- Customer logic includes diminishing returns on ads, capacity limits, review/reputation feedback loops, and realistic churn
- You can leave auto-run on and watch the company evolve

Enjoy building the next ₹1000 Cr company.
