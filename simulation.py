"""
Company simulation engine with realistic customer, market, and operations logic.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
import random
import math
from datetime import datetime, timedelta


@dataclass
class CompanyState:
    # Identity
    name: str = "Unnamed Startup"
    industry: str = "Not decided"
    tagline: str = ""
    founded_day: int = 0

    # Time
    current_day: int = 0
    current_month: int = 1
    current_year: int = 1

    # Financials (in ₹ Crores for big numbers, but we track in actual ₹ for precision)
    cash: float = 50_00_000          # Starting capital ₹50 Lakh
    revenue_total: float = 0.0
    revenue_this_month: float = 0.0
    expenses_this_month: float = 0.0
    profit_this_month: float = 0.0
    valuation: float = 2_00_00_000   # Starting valuation ₹2 Cr

    # Product
    product_name: str = "MVP"
    product_quality: float = 40.0    # 0-100
    price: float = 999.0             # Selling price
    production_capacity: int = 100   # Units per day
    inventory: int = 0
    units_sold_today: int = 0
    units_sold_total: int = 0

    # Customers & Market
    total_customers: int = 0
    active_customers: int = 0
    brand_awareness: float = 5.0     # 0-100
    market_size: float = 5000_00_00_000  # ₹5000 Cr addressable market (will adjust by industry)
    cac: float = 800.0               # Customer Acquisition Cost
    churn_rate: float = 0.08         # Monthly
    avg_order_value: float = 999.0
    repeat_purchase_rate: float = 0.25

    # Team
    employees: int = 2               # Founder + Co-Founder initially
    founders: int = 2
    eng_team: int = 0
    sales_team: int = 0
    support_team: int = 0
    marketing_team: int = 0
    ops_team: int = 0
    monthly_salary_cost: float = 0.0

    # Marketing & Growth
    marketing_spend_today: float = 0.0
    marketing_spend_month: float = 0.0

    # Reputation & Other
    reputation: float = 50.0         # 0-100
    reviews_score: float = 3.5       # 1-5
    backlog: int = 0                 # Unfulfilled orders

    # History for charts
    history: List[Dict[str, Any]] = field(default_factory=list)

    # Decisions log (short)
    recent_decisions: List[str] = field(default_factory=list)

    def advance_day(self):
        self.current_day += 1
        if self.current_day % 30 == 0:
            self.current_month += 1
            if self.current_month > 12:
                self.current_month = 1
                self.current_year += 1
            # Monthly reset
            self.revenue_this_month = 0.0
            self.expenses_this_month = 0.0
            self.profit_this_month = 0.0
            self.marketing_spend_month = 0.0

    def get_date_str(self) -> str:
        return f"Year {self.current_year}, Month {self.current_month}, Day {self.current_day % 30 or 30}"

    def estimate_valuation(self) -> float:
        """Rough realistic valuation based on revenue, growth, team, brand."""
        annual_run_rate = self.revenue_this_month * 12
        multiple = 8.0  # Base SaaS/D2C multiple

        if self.product_quality > 75:
            multiple += 3
        if self.brand_awareness > 40:
            multiple += 2
        if self.churn_rate < 0.05:
            multiple += 2
        if self.employees > 20:
            multiple += 1

        # Early stage discount
        if annual_run_rate < 1_00_00_000:  # < 1 Cr ARR
            multiple *= 0.6

        val = max(self.cash * 1.5, annual_run_rate * multiple + self.cash)
        # Smooth it
        self.valuation = self.valuation * 0.7 + val * 0.3
        return self.valuation

    def to_dashboard_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "industry": self.industry,
            "date": self.get_date_str(),
            "cash_cr": round(self.cash / 1_00_00_000, 2),
            "valuation_cr": round(self.valuation / 1_00_00_000, 2),
            "revenue_month_cr": round(self.revenue_this_month / 1_00_00_000, 3),
            "profit_month_cr": round(self.profit_this_month / 1_00_00_000, 3),
            "employees": self.employees,
            "active_customers": self.active_customers,
            "product_quality": round(self.product_quality, 1),
            "brand_awareness": round(self.brand_awareness, 1),
            "reputation": round(self.reputation, 1),
            "cac": round(self.cac, 0),
            "churn_pct": round(self.churn_rate * 100, 1),
            "price": self.price,
            "inventory": self.inventory,
            "backlog": self.backlog,
            "progress_to_1000cr": min(100, round((self.valuation / 1000_00_00_000) * 100, 1)),
        }


def apply_realistic_day(state: CompanyState, actions: Dict[str, Any]) -> List[str]:
    """
    Apply one day of realistic simulation based on agent decisions.
    Returns list of short impact messages.
    """
    impacts = []

    # --- Parse common actions ---
    hire = actions.get("hire", {})
    marketing_budget = float(actions.get("marketing_spend", 0) or 0)
    price_change = actions.get("new_price", None)
    quality_invest = float(actions.get("product_investment", 0) or 0)
    production_boost = int(actions.get("increase_capacity", 0) or 0)
    focus = actions.get("focus", "")  # e.g. "sales", "product", "support"

    # 1. Hiring
    for role, count in hire.items():
        count = int(count or 0)
        if count <= 0:
            continue
        cost_per = {
            "engineer": 80000,
            "sales": 60000,
            "support": 40000,
            "marketing": 55000,
            "ops": 45000,
        }.get(role, 50000)

        total_cost = count * cost_per
        if state.cash >= total_cost:
            state.cash -= total_cost
            state.employees += count
            if role == "engineer":
                state.eng_team += count
                state.product_quality = min(100, state.product_quality + count * 1.5)
            elif role == "sales":
                state.sales_team += count
            elif role == "support":
                state.support_team += count
                state.churn_rate = max(0.02, state.churn_rate - count * 0.008)
            elif role == "marketing":
                state.marketing_team += count
            elif role == "ops":
                state.ops_team += count
                state.production_capacity += count * 30

            state.monthly_salary_cost += count * cost_per
            impacts.append(f"Hired {count} {role}(s). Team size now {state.employees}.")
        else:
            impacts.append(f"Could not hire {count} {role}(s) — insufficient cash.")

    # 2. Pricing
    if price_change is not None:
        old_price = state.price
        state.price = float(price_change)
        state.avg_order_value = state.price
        elasticity_impact = (old_price - state.price) / old_price * 0.6  # rough
        impacts.append(f"Price changed from ₹{old_price:.0f} → ₹{state.price:.0f}")

    # 3. Product investment
    if quality_invest > 0 and state.cash >= quality_invest:
        state.cash -= quality_invest
        gain = min(8.0, quality_invest / 200000 * 3)
        state.product_quality = min(100, state.product_quality + gain)
        impacts.append(f"Invested ₹{quality_invest/100000:.1f}L in product. Quality → {state.product_quality:.1f}")

    # 4. Capacity
    if production_boost > 0 and state.cash >= production_boost * 50000:
        state.cash -= production_boost * 50000
        state.production_capacity += production_boost * 50
        impacts.append(f"Increased daily capacity by {production_boost*50} units.")

    # 5. Marketing spend for the day
    marketing_budget = min(marketing_budget, state.cash * 0.3)  # safety
    if marketing_budget > 0:
        state.cash -= marketing_budget
        state.marketing_spend_today = marketing_budget
        state.marketing_spend_month += marketing_budget

        # Awareness gain (diminishing returns)
        awareness_gain = math.log1p(marketing_budget / 50000) * 1.8
        if state.marketing_team > 0:
            awareness_gain *= (1 + state.marketing_team * 0.15)
        state.brand_awareness = min(95, state.brand_awareness + awareness_gain)

        # CAC improvement with team + spend efficiency
        state.cac = max(150, state.cac * 0.995 - state.marketing_team * 5)
    else:
        state.marketing_spend_today = 0

    # --- Realistic Customer Acquisition & Sales ---
    # Base demand from awareness + quality + price attractiveness
    price_attractiveness = max(0.3, 1.5 - (state.price / 3000))  # cheaper = more attractive
    quality_factor = state.product_quality / 100
    awareness_factor = state.brand_awareness / 100

    base_daily_leads = (state.brand_awareness * 8) + (state.marketing_spend_today / 400)
    base_daily_leads *= (1 + state.sales_team * 0.25)

    conversion_rate = 0.04 * quality_factor * price_attractiveness * (state.reputation / 70)
    conversion_rate = max(0.008, min(0.18, conversion_rate))

    new_customers = int(base_daily_leads * conversion_rate * random.uniform(0.85, 1.15))
    new_customers = max(0, new_customers)

    # Capacity & inventory check
    potential_units = new_customers + int(state.active_customers * state.repeat_purchase_rate * 0.03)
    available = state.production_capacity + state.inventory
    actual_units = min(potential_units, available)

    if actual_units < potential_units:
        state.backlog += (potential_units - actual_units)
        state.reputation = max(20, state.reputation - 1.5)
        impacts.append(f"Capacity issue: {potential_units - actual_units} orders delayed. Reputation hit.")
    else:
        state.backlog = max(0, state.backlog - 5)

    # Fulfill
    from_inventory = min(state.inventory, actual_units)
    state.inventory -= from_inventory
    produced = actual_units - from_inventory
    # Production cost
    unit_cost = max(80, state.price * 0.35 - state.ops_team * 5)
    production_cost = produced * unit_cost
    state.cash -= production_cost

    state.units_sold_today = actual_units
    state.units_sold_total += actual_units
    state.inventory = max(0, state.inventory)  # safety

    # Revenue
    day_revenue = actual_units * state.price
    state.cash += day_revenue
    state.revenue_total += day_revenue
    state.revenue_this_month += day_revenue

    # Customers
    state.total_customers += new_customers
    state.active_customers += new_customers

    # Churn (daily portion of monthly)
    daily_churn = int(state.active_customers * (state.churn_rate / 30) * random.uniform(0.7, 1.3))
    # Support team reduces churn
    daily_churn = max(0, daily_churn - state.support_team * 2)
    state.active_customers = max(0, state.active_customers - daily_churn)

    # Reputation & reviews drift toward quality
    target_review = 2.8 + (state.product_quality / 100) * 2.0
    state.reviews_score = state.reviews_score * 0.9 + target_review * 0.1
    state.reputation = state.reputation * 0.95 + (state.reviews_score * 15) * 0.05
    state.reputation = max(10, min(98, state.reputation))

    # Expenses
    daily_salary = state.monthly_salary_cost / 30
    state.cash -= daily_salary
    state.expenses_this_month += daily_salary + production_cost + state.marketing_spend_today

    state.profit_this_month = state.revenue_this_month - state.expenses_this_month

    # Update valuation
    state.estimate_valuation()

    # Record history every day
    state.history.append({
        "day": state.current_day,
        "valuation_cr": state.valuation / 1_00_00_000,
        "cash_cr": state.cash / 1_00_00_000,
        "customers": state.active_customers,
        "revenue_month_cr": state.revenue_this_month / 1_00_00_000,
    })

    # Keep history reasonable length
    if len(state.history) > 400:
        state.history = state.history[-300:]

    # Short summary impacts
    if new_customers > 0:
        impacts.append(f"+{new_customers} new customers today. Active: {state.active_customers}")
    if day_revenue > 0:
        impacts.append(f"Revenue today: ₹{day_revenue/100000:.2f}L")

    if state.cash < 5_00_000:
        impacts.append("⚠️ Low cash warning!")

    return impacts


def create_initial_state() -> CompanyState:
    return CompanyState()
