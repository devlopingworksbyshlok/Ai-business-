"""
AI Founder + Co-Founder Business Simulation
Live dashboard + clean short conversation board
"""

import streamlit as st
import os
import time
from dotenv import load_dotenv
from simulation import CompanyState, create_initial_state, apply_realistic_day
from agents import Agent, FOUNDER_SYSTEM, COFOUNDER_SYSTEM, run_short_meeting, extract_actions_from_discussion
from groq import Groq
import plotly.graph_objects as go
from datetime import datetime

load_dotenv()

st.set_page_config(
    page_title="AI Founders – ₹1000 Cr Simulation",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for clean look
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #1e1e2f 0%, #2a2a40 100%);
        padding: 16px 20px;
        border-radius: 12px;
        border: 1px solid #3a3a55;
        text-align: center;
    }
    .metric-value {
        font-size: 1.6rem;
        font-weight: 700;
        color: #00d4aa;
    }
    .metric-label {
        font-size: 0.85rem;
        color: #aaa;
        margin-top: 4px;
    }
    .speaker-founder {
        color: #00c853;
        font-weight: 600;
    }
    .speaker-cofounder {
        color: #2979ff;
        font-weight: 600;
    }
    .msg-box {
        background: #1a1a2e;
        padding: 10px 14px;
        border-radius: 10px;
        margin-bottom: 8px;
        border-left: 4px solid #444;
    }
    .stButton>button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)


def get_api_keys():
    """Load the two dedicated keys."""
    key1 = os.getenv("GROQ_API_KEY_FOUNDER") or st.secrets.get("GROQ_API_KEY_FOUNDER", "")
    key2 = os.getenv("GROQ_API_KEY_COFOUNDER") or st.secrets.get("GROQ_API_KEY_COFOUNDER", "")
    return key1.strip(), key2.strip()


def init_session():
    if "state" not in st.session_state:
        st.session_state.state = create_initial_state()
    if "conversation" not in st.session_state:
        st.session_state.conversation = []
    if "impacts" not in st.session_state:
        st.session_state.impacts = []
    if "started" not in st.session_state:
        st.session_state.started = False
    if "auto_running" not in st.session_state:
        st.session_state.auto_running = False
    if "last_run" not in st.session_state:
        st.session_state.last_run = None
    if "founder" not in st.session_state:
        st.session_state.founder = None
    if "cofounder" not in st.session_state:
        st.session_state.cofounder = None
    if "meeting_count" not in st.session_state:
        st.session_state.meeting_count = 0


def company_context(state: CompanyState) -> str:
    d = state.to_dashboard_dict()
    return f"""
Company: {d['name']} ({d['industry']})
Date: {d['date']}
Cash: ₹{d['cash_cr']} Cr | Valuation: ₹{d['valuation_cr']} Cr
Monthly Revenue: ₹{d['revenue_month_cr']} Cr | Profit: ₹{d['profit_month_cr']} Cr
Employees: {d['employees']} | Active Customers: {d['active_customers']}
Product Quality: {d['product_quality']}/100 | Brand Awareness: {d['brand_awareness']}/100
Reputation: {d['reputation']}/100 | CAC: ₹{d['cac']} | Churn: {d['churn_pct']}%
Price: ₹{d['price']} | Inventory: {d['inventory']} | Backlog: {d['backlog']}
Progress to ₹1000 Cr: {d['progress_to_1000cr']}%
"""


def render_dashboard(state: CompanyState):
    d = state.to_dashboard_dict()

    st.markdown(f"### 🚀 {d['name']}  ·  {d['industry']}")
    st.caption(f"📅 {d['date']}   |   Goal: ₹1000 Cr Valuation")

    # Progress
    st.progress(d['progress_to_1000cr'] / 100, text=f"Progress to ₹1000 Cr: {d['progress_to_1000cr']}%")

    # Metrics row
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1:
        st.metric("Valuation", f"₹{d['valuation_cr']} Cr")
    with c2:
        st.metric("Cash", f"₹{d['cash_cr']} Cr")
    with c3:
        st.metric("Month Revenue", f"₹{d['revenue_month_cr']} Cr")
    with c4:
        st.metric("Employees", d['employees'])
    with c5:
        st.metric("Customers", d['active_customers'])
    with c6:
        st.metric("Product Quality", f"{d['product_quality']}/100")

    # Second row
    c7, c8, c9, c10, c11, c12 = st.columns(6)
    with c7:
        st.metric("Brand Awareness", f"{d['brand_awareness']}/100")
    with c8:
        st.metric("Reputation", f"{d['reputation']}/100")
    with c9:
        st.metric("CAC", f"₹{d['cac']}")
    with c10:
        st.metric("Churn", f"{d['churn_pct']}%")
    with c11:
        st.metric("Price", f"₹{d['price']}")
    with c12:
        st.metric("Backlog", d['backlog'])


def render_conversation():
    st.subheader("💬 Conversation Board")
    if not st.session_state.conversation:
        st.info("No meetings yet. Start the simulation to begin.")
        return

    # Show latest meetings first (most recent at top)
    for msg in reversed(st.session_state.conversation[-20:]):  # last 20 messages max
        speaker = msg["speaker"]
        text = msg["text"]
        if speaker == "Founder":
            st.markdown(f"""
            <div class="msg-box" style="border-left-color: #00c853;">
                <span class="speaker-founder">🟢 Founder</span><br>
                {text}
            </div>
            """, unsafe_allow_html=True)
        elif speaker == "Co-Founder":
            st.markdown(f"""
            <div class="msg-box" style="border-left-color: #2979ff;">
                <span class="speaker-cofounder">🔵 Co-Founder</span><br>
                {text}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="msg-box" style="border-left-color: #ff9800;">
                <b>📌 {speaker}</b><br>
                {text}
            </div>
            """, unsafe_allow_html=True)


def render_impacts():
    if st.session_state.impacts:
        with st.expander("📊 Latest Day Impact", expanded=True):
            for imp in st.session_state.impacts[-8:]:
                st.write("• " + imp)


def render_charts(state: CompanyState):
    if len(state.history) < 2:
        return

    import pandas as pd
    df = pd.DataFrame(state.history)

    col1, col2 = st.columns(2)
    with col1:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df["day"], y=df["valuation_cr"], mode="lines", name="Valuation (Cr)", line=dict(color="#00d4aa")))
        fig.update_layout(title="Valuation Over Time", height=280, margin=dict(l=20, r=20, t=40, b=20), template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=df["day"], y=df["customers"], mode="lines", name="Active Customers", line=dict(color="#2979ff")))
        fig2.update_layout(title="Active Customers", height=280, margin=dict(l=20, r=20, t=40, b=20), template="plotly_dark")
        st.plotly_chart(fig2, use_container_width=True)


def main():
    init_session()
    state: CompanyState = st.session_state.state

    # Sidebar – Keys & Controls
    with st.sidebar:
        st.title("⚙️ Controls")
        st.markdown("---")

        key_founder, key_cofounder = get_api_keys()

        if not key_founder or not key_cofounder:
            st.error("Add both API keys")
            st.markdown("""
            Create a `.env` file in this folder:
            ```
            GROQ_API_KEY_FOUNDER=gsk_xxx
            GROQ_API_KEY_COFOUNDER=gsk_yyy
            ```
            Or add them in Streamlit Secrets.
            """)
            st.stop()

        st.success("API keys loaded (separate for each agent)")

        st.markdown("### Simulation")
        if not st.session_state.started:
            if st.button("🚀 Start Simulation", type="primary"):
                # Initialize agents with dedicated keys
                st.session_state.founder = Agent(
                    name="Founder",
                    role="CEO",
                    api_key=key_founder,
                    system_prompt=FOUNDER_SYSTEM
                )
                st.session_state.cofounder = Agent(
                    name="Co-Founder",
                    role="COO",
                    api_key=key_cofounder,
                    system_prompt=COFOUNDER_SYSTEM
                )
                st.session_state.started = True
                st.session_state.conversation = []
                st.rerun()
        else:
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("▶️ Next Day + Meeting", type="primary"):
                    run_one_cycle()
                    st.rerun()
            with col_b:
                if st.button("⏩ Skip 7 Days"):
                    for _ in range(7):
                        run_one_cycle(meeting=False)
                    st.rerun()

            st.markdown("---")
            auto = st.toggle("Auto-run (≈2-3 min per day)", value=st.session_state.auto_running)
            st.session_state.auto_running = auto

            if st.button("🔄 Reset Simulation"):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()

        st.markdown("---")
        st.caption("Time scale target: 2–3 real minutes ≈ 1 simulated day")
        st.caption("Each agent uses its own Groq API key")

    # Main area
    if not st.session_state.started:
        st.title("🚀 AI Founders – Build a ₹1000 Cr Company")
        st.markdown("""
        Two AI agents (Founder + Co-Founder) will:
        - Choose any business they want
        - Discuss strategy & divide work
        - Hire, build product, acquire customers, manage operations
        - Face realistic market & customer dynamics
        - Try to reach **₹1000 Crore** valuation

        **Conversation board shows only short, main points** with clear speaker labels.
        """)
        st.info("Add your two Groq API keys in `.env` then click **Start Simulation** in the sidebar.")
        return

    # Dashboard
    render_dashboard(state)

    st.markdown("---")

    # Two columns: Conversation + Side info
    left, right = st.columns([1.6, 1])

    with left:
        render_conversation()

    with right:
        render_impacts()
        st.markdown("### 📈 Charts")
        render_charts(state)

        if state.recent_decisions:
            st.markdown("### Last Decisions")
            for dec in state.recent_decisions[-5:]:
                st.caption("• " + dec)

    # Auto-run logic
    if st.session_state.auto_running and st.session_state.started:
        # Target: 2–3 real minutes ≈ 1 simulated day
        # Change the sleep value below to 120–180 for true pace.
        # Currently set lower so you can test quickly.
        time.sleep(12)
        run_one_cycle()
        st.rerun()



def run_one_cycle(meeting: bool = True):
    """Advance one simulated day. Optionally hold a short meeting."""
    state: CompanyState = st.session_state.state
    founder: Agent = st.session_state.founder
    cofounder: Agent = st.session_state.cofounder

    ctx = company_context(state)

    if not st.session_state.started:
        return

    # First ever meeting → choose business
    if state.current_day == 0 and state.name == "Unnamed Startup":
        topic = (
            "This is Day 0. We have ₹50 Lakh starting capital. "
            "We must decide: 1) Company name 2) Industry/business idea 3) Initial product 4) Rough go-to-market. "
            "Be decisive, ambitious and specific. Agree on a clear name and direction."
        )
        discussion = run_short_meeting(founder, cofounder, ctx, topic, turns=5)

        # Extract founding decisions
        actions = extract_actions_from_discussion(discussion, ctx, founder.client, is_founding=True)

        state.name = actions.get("company_name", "Nexus Labs")
        state.industry = actions.get("industry", "AI Software")
        state.product_name = actions.get("product_name", "Core Platform")
        state.tagline = actions.get("tagline", "")

        st.session_state.conversation.append({
            "speaker": "System",
            "text": f"🚀 Company founded: **{state.name}** ({state.industry}) — {state.tagline}. Starting capital ₹50 Lakh."
        })

        for msg in discussion:
            st.session_state.conversation.append(msg)

        state.recent_decisions.append(actions.get("notes", "Company founded"))
        state.current_day = 1
        return


    # Normal day
    if meeting:
        st.session_state.meeting_count += 1
        topic = (
            f"Day {state.current_day}. Current valuation ₹{state.valuation/1e7:.1f} Cr. "
            f"Cash ₹{state.cash/1e7:.2f} Cr. "
            "Review numbers, decide today's priorities (hiring, marketing spend, pricing, product, capacity). "
            "Be specific and short."
        )
        discussion = run_short_meeting(founder, cofounder, ctx, topic, turns=4)

        for msg in discussion:
            st.session_state.conversation.append(msg)

        # Extract actions
        actions = extract_actions_from_discussion(discussion, ctx, founder.client)
        notes = actions.get("notes", "Daily execution")
        state.recent_decisions.append(notes)
        if len(state.recent_decisions) > 15:
            state.recent_decisions = state.recent_decisions[-10:]

        # Apply realistic simulation
        impacts = apply_realistic_day(state, actions)
        st.session_state.impacts = impacts

        st.session_state.conversation.append({
            "speaker": "System",
            "text": f"Day {state.current_day} closed. " + " | ".join(impacts[:3])
        })
    else:
        # Quiet day – still apply light natural progress
        impacts = apply_realistic_day(state, {
            "hire": {},
            "marketing_spend": state.marketing_spend_month / 30 if state.marketing_spend_month else 0,
            "new_price": None,
            "product_investment": 0,
            "increase_capacity": 0,
            "focus": "growth"
        })
        st.session_state.impacts = impacts

    state.advance_day()

    # Trim conversation to keep board clean
    if len(st.session_state.conversation) > 40:
        st.session_state.conversation = st.session_state.conversation[-30:]


if __name__ == "__main__":
    main()
