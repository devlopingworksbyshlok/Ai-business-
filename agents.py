"""
Founder and Co-Founder agents with dedicated Groq API keys.
They keep messages short and focused on decisions.
"""

from groq import Groq
from typing import List, Dict, Any, Optional
import json
import re


FOUNDER_SYSTEM = """You are the Founder of a startup. Visionary, ambitious, decisive.
Your goal is to build a ₹1000 Crore company.

Rules for every reply:
- Keep it SHORT (max 40-60 words). No long paragraphs.
- Speak in first person.
- Focus on strategy, big decisions, vision, priorities, fundraising mindset.
- Be direct. Propose clear actions.
- Never write more than 3-4 short sentences.
- End with a clear recommendation or question for your Co-Founder when needed.
"""

COFOUNDER_SYSTEM = """You are the Co-Founder & COO. Execution-focused, practical, numbers-driven.
Your goal is to help build a ₹1000 Crore company.

Rules for every reply:
- Keep it SHORT (max 40-60 words). No long paragraphs.
- Speak in first person.
- Focus on operations, hiring, product quality, sales execution, costs, customer metrics.
- Be realistic and push back when ideas are too risky or vague.
- Never write more than 3-4 short sentences.
- Give concrete next steps.
"""


class Agent:
    def __init__(self, name: str, role: str, api_key: str, system_prompt: str, model: str = "llama-3.3-70b-versatile"):
        self.name = name
        self.role = role
        self.client = Groq(api_key=api_key)
        self.system_prompt = system_prompt
        self.model = model
        self.history: List[Dict[str, str]] = []

    def say(self, user_message: str, company_context: str) -> str:
        """Generate a short reply."""
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "system", "content": f"Current company state:\n{company_context}"},
        ]

        # Keep only last 6 turns to stay focused
        for h in self.history[-6:]:
            messages.append(h)

        messages.append({"role": "user", "content": user_message})

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=150,  # Force short answers
            )
            reply = response.choices[0].message.content.strip()
        except Exception as e:
            reply = f"(API error: {str(e)[:80]})"

        # Save to history
        self.history.append({"role": "user", "content": user_message})
        self.history.append({"role": "assistant", "content": reply})

        return reply

    def reset_history(self):
        self.history = []


def extract_actions_from_discussion(discussion: List[Dict[str, str]], company_context: str, client: Groq, is_founding: bool = False) -> Dict[str, Any]:
    """
    After a short discussion, extract concrete actions as JSON.
    Uses one of the keys (we pass a client).
    """
    transcript = "\n".join([f"{m['speaker']}: {m['text']}" for m in discussion])

    if is_founding:
        prompt = f"""You are a business simulation engine. The two founders are deciding the company identity on Day 0.

Discussion:
{transcript}

Return ONLY a valid JSON object:
{{
  "company_name": "Name they chose",
  "industry": "Short industry (e.g. AI SaaS, D2C Beauty, Fintech, Food Tech)",
  "product_name": "Initial product name",
  "tagline": "One short tagline",
  "notes": "One sentence summary of the founding decision"
}}

Rules:
- Extract the name and industry they actually agreed on.
- If unclear, invent a strong plausible name that fits their discussion.
- Return pure JSON only, no markdown.
"""
    else:
        prompt = f"""You are a business simulation engine. From the founders' short discussion below, extract the concrete decisions they agreed on for TODAY.

Company context:
{company_context}

Discussion:
{transcript}

Return ONLY a valid JSON object with these possible keys (omit any not mentioned):
{{
  "hire": {{"engineer": 0, "sales": 0, "support": 0, "marketing": 0, "ops": 0}},
  "marketing_spend": 0,
  "new_price": null,
  "product_investment": 0,
  "increase_capacity": 0,
  "focus": "product" | "sales" | "support" | "growth" | "cost",
  "notes": "one short sentence summary of the main decision"
}}

Rules:
- Only include actions they clearly decided.
- Numbers must be realistic for current cash.
- If no clear decision on something, use 0 or null.
- Return pure JSON only, no markdown.
"""

    try:
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=400,
        )
        text = resp.choices[0].message.content.strip()
        # Clean possible markdown
        text = re.sub(r"^```json\s*|\s*```$", "", text, flags=re.MULTILINE)
        return json.loads(text)
    except Exception as e:
        if is_founding:
            return {
                "company_name": "Nexus Labs",
                "industry": "AI Software",
                "product_name": "Core Platform",
                "tagline": "Building the future",
                "notes": "Founding decisions extracted with fallback"
            }
        return {
            "hire": {},
            "marketing_spend": 0,
            "new_price": None,
            "product_investment": 0,
            "increase_capacity": 0,
            "focus": "growth",
            "notes": f"Could not parse decisions cleanly ({str(e)[:40]})"
        }



def run_short_meeting(
    founder: Agent,
    cofounder: Agent,
    company_context: str,
    topic: str,
    turns: int = 4
) -> List[Dict[str, str]]:
    """
    Run a short, focused discussion (only main points).
    Returns list of {"speaker": ..., "text": ...}
    """
    discussion = []
    current_msg = f"Topic for this meeting: {topic}\n\nStart the discussion. Keep every reply under 60 words."

    for i in range(turns):
        if i % 2 == 0:
            # Founder speaks
            reply = founder.say(current_msg, company_context)
            discussion.append({"speaker": "Founder", "text": reply})
            current_msg = reply
        else:
            # Co-Founder speaks
            reply = cofounder.say(current_msg, company_context)
            discussion.append({"speaker": "Co-Founder", "text": reply})
            current_msg = reply

    return discussion
