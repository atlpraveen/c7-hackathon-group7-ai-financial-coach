"""Indian personal-finance tools (educational).

Covers SIP, EPF, NPS, ELSS and old-vs-new income-tax regimes for FY 2024-25.
All monetary amounts are in INR (₹). Figures are illustrative — not tax or
investment advice. Verify against current IT rules and EPFO / PFRDA circulars.
"""
from __future__ import annotations

from .financial_utils import clamp, safe_div


# ---------------------------------------------------------------------------
# SIP (Systematic Investment Plan)
# ---------------------------------------------------------------------------

def sip_future_value(
    monthly_investment: float,
    annual_return_pct: float,
    years: int,
) -> dict:
    """Monthly-compounded SIP future value.

    Returns invested corpus, maturity value, gains and a year-by-year
    projection list starting at year 0 (today).
    """
    monthly_investment = max(monthly_investment, 0.0)
    years = max(years, 0)
    monthly_rate = annual_return_pct / 100 / 12

    balance = 0.0
    invested = 0.0
    projection = [{"year": 0, "invested": 0, "value": 0}]

    for yr in range(1, years + 1):
        for _ in range(12):
            balance = balance * (1 + monthly_rate) + monthly_investment
            invested += monthly_investment
        projection.append(
            {
                "year": yr,
                "invested": round(invested),
                "value": round(balance),
            }
        )

    maturity = round(balance)
    total_invested = round(invested)
    return {
        "monthly_investment": round(monthly_investment),
        "years": years,
        "annual_return_pct": annual_return_pct,
        "invested": total_invested,
        "maturity": maturity,
        "gains": maturity - total_invested,
        "projection": projection,
    }


# ---------------------------------------------------------------------------
# EPF (Employee Provident Fund)
# ---------------------------------------------------------------------------

def epf_projection(
    monthly_basic: float,
    years: int,
    current_balance: float = 0.0,
    employee_pct: float = 12.0,
    employer_pct: float = 3.67,
    annual_rate: float = 8.25,
    annual_increment_pct: float = 5.0,
) -> dict:
    """EPF corpus projection with annual salary increment and interest.

    Only the employer's EPF share (employer_pct, default 3.67%) goes to the
    EPF corpus; the remaining ~8.33% goes to EPS and is excluded from corpus.
    Interest is credited annually on the closing balance.

    Returns total contribution, maturity value, interest earned and a
    year-by-year projection.
    """
    monthly_basic = max(monthly_basic, 0.0)
    years = max(years, 0)
    current_balance = max(current_balance, 0.0)

    balance = current_balance
    total_contributed = 0.0
    projection = [{"year": 0, "balance": round(balance), "contributed": 0}]

    basic = monthly_basic
    for yr in range(1, years + 1):
        # Annual contributions at current basic
        annual_employee = basic * (employee_pct / 100) * 12
        annual_employer_epf = basic * (employer_pct / 100) * 12
        annual_contribution = annual_employee + annual_employer_epf

        balance += annual_contribution
        balance += balance * (annual_rate / 100)
        total_contributed += annual_contribution

        projection.append(
            {
                "year": yr,
                "balance": round(balance),
                "contributed": round(total_contributed),
            }
        )

        # Increment basic for next year
        basic *= 1 + annual_increment_pct / 100

    maturity = round(balance)
    total_contributed_r = round(total_contributed)
    return {
        "monthly_basic": round(monthly_basic),
        "years": years,
        "annual_rate": annual_rate,
        "total_contributed": total_contributed_r,
        "maturity": maturity,
        "interest_earned": maturity - total_contributed_r - round(current_balance),
        "projection": projection,
    }


# ---------------------------------------------------------------------------
# NPS (National Pension System)
# ---------------------------------------------------------------------------

def nps_projection(
    monthly_investment: float,
    years: int,
    current_balance: float = 0.0,
    annual_return_pct: float = 10.0,
    annuity_pct: float = 40.0,
    annuity_rate_pct: float = 6.0,
) -> dict:
    """NPS corpus projection with annuity split at maturity.

    At maturity, *annuity_pct* of the corpus must be used to purchase an
    annuity; the remaining lump sum (up to 60%) is tax-free.  Monthly pension
    is estimated from the annuity corpus.
    """
    monthly_investment = max(monthly_investment, 0.0)
    years = max(years, 0)
    current_balance = max(current_balance, 0.0)
    annuity_pct = clamp(annuity_pct, 40.0, 100.0)

    monthly_rate = annual_return_pct / 100 / 12
    balance = current_balance
    invested = 0.0

    for _ in range(years * 12):
        balance = balance * (1 + monthly_rate) + monthly_investment
        invested += monthly_investment

    maturity_corpus = round(balance)
    total_invested = round(invested) + round(current_balance)
    annuity_corpus = round(maturity_corpus * annuity_pct / 100)
    lump_sum = maturity_corpus - annuity_corpus
    est_monthly_pension = round((annuity_corpus * annuity_rate_pct / 100) / 12)

    return {
        "monthly_investment": round(monthly_investment),
        "years": years,
        "maturity_corpus": maturity_corpus,
        "invested": round(invested),
        "gains": maturity_corpus - round(invested) - round(current_balance),
        "lump_sum": lump_sum,
        "annuity_corpus": annuity_corpus,
        "est_monthly_pension": est_monthly_pension,
    }


# ---------------------------------------------------------------------------
# ELSS (Equity Linked Savings Scheme)
# ---------------------------------------------------------------------------

def elss_plan(
    monthly_investment: float,
    years: int,
    annual_return_pct: float = 12.0,
    tax_slab_pct: float = 30.0,
) -> dict:
    """ELSS SIP plan with 80C tax benefit.

    Eligible 80C deduction is capped at ₹1,50,000 per year.  Tax saved is
    based on the supplied marginal slab rate.  Lock-in is 3 years per
    instalment, so the shortest horizon is 3 years.
    """
    monthly_investment = max(monthly_investment, 0.0)
    years = max(years, 3)  # minimum lock-in

    annual_invested = min(monthly_investment * 12, 150_000.0)
    eligible_80c = round(annual_invested)
    tax_saved_per_year = round(eligible_80c * tax_slab_pct / 100)

    sip = sip_future_value(monthly_investment, annual_return_pct, years)

    return {
        "monthly_investment": round(monthly_investment),
        "annual_invested": round(annual_invested),
        "eligible_80c": eligible_80c,
        "tax_saved_per_year": tax_saved_per_year,
        "lock_in_years": 3,
        "years": sip["years"],
        "annual_return_pct": annual_return_pct,
        "invested": sip["invested"],
        "maturity": sip["maturity"],
        "gains": sip["gains"],
        "projection": sip["projection"],
    }


# ---------------------------------------------------------------------------
# Income Tax — Old Regime (FY 2024-25)
# ---------------------------------------------------------------------------

def _apply_old_slabs(taxable: float) -> float:
    """Compute tax under old regime slabs (individual < 60 yrs)."""
    tax = 0.0
    slabs = [
        (250_000, 0.00),
        (250_000, 0.05),   # 2.5L – 5L
        (500_000, 0.20),   # 5L – 10L
    ]
    remaining = taxable
    for band, rate in slabs:
        chunk = min(remaining, band)
        tax += chunk * rate
        remaining -= chunk
        if remaining <= 0:
            break
    if remaining > 0:
        tax += remaining * 0.30
    return tax


def tax_old_regime(
    gross_income: float,
    deductions_80c: float = 0.0,
    deductions_80d: float = 0.0,
    other_deductions: float = 0.0,
    standard_deduction: float = 50_000.0,
) -> dict:
    """FY 2024-25 old regime tax computation.

    Deduction caps: 80C ≤ ₹1,50,000; 80D ≤ ₹25,000.
    Section 87A rebate: if taxable income ≤ ₹5,00,000, tax = 0.
    Adds 4% health & education cess on final tax.
    """
    gross_income = max(gross_income, 0.0)
    d80c = clamp(deductions_80c, 0.0, 150_000.0)
    d80d = clamp(deductions_80d, 0.0, 25_000.0)
    total_deductions = round(standard_deduction + d80c + d80d + max(other_deductions, 0.0))
    taxable_income = max(round(gross_income) - total_deductions, 0)

    tax_before_cess = round(_apply_old_slabs(taxable_income))
    # Section 87A rebate
    if taxable_income <= 500_000:
        tax_before_cess = 0
    cess = round(tax_before_cess * 0.04)
    total_tax = tax_before_cess + cess
    effective_rate_pct = round(safe_div(total_tax * 100, gross_income), 2)

    return {
        "regime": "old",
        "gross_income": round(gross_income),
        "total_deductions": total_deductions,
        "taxable_income": taxable_income,
        "tax_before_cess": tax_before_cess,
        "cess": cess,
        "total_tax": total_tax,
        "effective_rate_pct": effective_rate_pct,
    }


# ---------------------------------------------------------------------------
# Income Tax — New Regime (FY 2024-25)
# ---------------------------------------------------------------------------

def _apply_new_slabs(taxable: float) -> float:
    """Compute tax under new regime slabs (FY 2024-25)."""
    tax = 0.0
    slabs = [
        (300_000, 0.00),   # 0 – 3L
        (400_000, 0.05),   # 3L – 7L
        (300_000, 0.10),   # 7L – 10L
        (200_000, 0.15),   # 10L – 12L
        (300_000, 0.20),   # 12L – 15L
    ]
    remaining = taxable
    for band, rate in slabs:
        chunk = min(remaining, band)
        tax += chunk * rate
        remaining -= chunk
        if remaining <= 0:
            break
    if remaining > 0:
        tax += remaining * 0.30
    return tax


def tax_new_regime(
    gross_income: float,
    standard_deduction: float = 75_000.0,
) -> dict:
    """FY 2024-25 new regime tax computation.

    Standard deduction ₹75,000 (salaried).
    Section 87A rebate: if taxable income ≤ ₹7,00,000, tax = 0.
    Adds 4% health & education cess on final tax.
    """
    gross_income = max(gross_income, 0.0)
    total_deductions = round(standard_deduction)
    taxable_income = max(round(gross_income) - total_deductions, 0)

    tax_before_cess = round(_apply_new_slabs(taxable_income))
    # Section 87A rebate
    if taxable_income <= 700_000:
        tax_before_cess = 0
    cess = round(tax_before_cess * 0.04)
    total_tax = tax_before_cess + cess
    effective_rate_pct = round(safe_div(total_tax * 100, gross_income), 2)

    return {
        "regime": "new",
        "gross_income": round(gross_income),
        "total_deductions": total_deductions,
        "taxable_income": taxable_income,
        "tax_before_cess": tax_before_cess,
        "cess": cess,
        "total_tax": total_tax,
        "effective_rate_pct": effective_rate_pct,
    }


# ---------------------------------------------------------------------------
# Tax Regime Comparison
# ---------------------------------------------------------------------------

def compare_tax_regimes(
    gross_income: float,
    deductions_80c: float = 0.0,
    deductions_80d: float = 0.0,
    other_deductions: float = 0.0,
) -> dict:
    """Compute tax under both regimes and recommend the lower-tax option."""
    old = tax_old_regime(gross_income, deductions_80c, deductions_80d, other_deductions)
    new = tax_new_regime(gross_income)
    savings = abs(old["total_tax"] - new["total_tax"])
    recommended = "old" if old["total_tax"] <= new["total_tax"] else "new"
    return {
        "old": old,
        "new": new,
        "recommended": recommended,
        "savings": savings,
    }


# ---------------------------------------------------------------------------
# Aggregator: build_india_plan
# ---------------------------------------------------------------------------

def build_india_plan(profile: dict, params: dict | None = None) -> dict:
    """Aggregate Indian personal-finance plan.

    Derives sensible defaults from *profile* and merges any *params* overrides.
    Returns a structured dict suitable for narrative generation.
    """
    params = params or {}

    monthly_income: float = max(float(profile.get("monthly_income") or 0), 0.0)
    monthly_expenses: float = max(float(profile.get("monthly_expenses") or 0), 0.0)
    age: int = int(params.get("age") or profile.get("age") or 30)

    # Derived base values
    annual_gross = round(monthly_income * 12)
    monthly_basic = float(params.get("monthly_basic") or monthly_income * 0.40)
    monthly_basic = max(monthly_basic, 0.0)
    investable_monthly = max(monthly_income - monthly_expenses, 0.0)

    # Horizon: retire at 60 or use supplied value
    horizon_years: int = int(
        params.get("horizon_years") or max(min(60 - age, 30), 1)
    )

    # Split investable across SIP / ELSS / NPS (default: 50/30/20 split)
    # Allow full override via params
    default_sip = round(investable_monthly * 0.50)
    default_elss = round(investable_monthly * 0.30)
    default_nps = round(investable_monthly * 0.20)

    sip_monthly: float = float(params.get("sip_monthly") or default_sip)
    elss_monthly: float = float(params.get("elss_monthly") or default_elss)
    nps_monthly: float = float(params.get("nps_monthly") or default_nps)

    tax_slab_pct: float = float(params.get("tax_slab_pct") or 30.0)
    deductions_80c: float = float(params.get("deductions_80c") or 0.0)
    deductions_80d: float = float(params.get("deductions_80d") or 0.0)

    # SIP projection
    sip_data = sip_future_value(
        monthly_investment=sip_monthly,
        annual_return_pct=float(params.get("sip_return_pct") or 12.0),
        years=horizon_years,
    )

    # EPF projection
    epf_data = epf_projection(
        monthly_basic=monthly_basic,
        years=horizon_years,
        current_balance=float(profile.get("epf_balance") or 0.0),
    )

    # NPS projection
    nps_data = nps_projection(
        monthly_investment=nps_monthly,
        years=horizon_years,
        current_balance=float(profile.get("nps_balance") or 0.0),
    )

    # ELSS plan (also uses 80C deduction)
    elss_data = elss_plan(
        monthly_investment=elss_monthly,
        years=horizon_years,
        tax_slab_pct=tax_slab_pct,
    )

    # Add ELSS 80C to declared 80C deductions (cap enforced inside tax functions)
    total_80c = deductions_80c + elss_data["eligible_80c"]

    # Tax comparison
    tax_comp = compare_tax_regimes(
        gross_income=float(annual_gross),
        deductions_80c=total_80c,
        deductions_80d=deductions_80d,
    )

    # Recommendations
    recommendations: list[str] = []

    if investable_monthly <= 0:
        recommendations.append(
            "Your expenses equal or exceed income — prioritise reducing expenses before investing."
        )
    else:
        recommendations.append(
            f"You can invest approximately ₹{round(investable_monthly):,}/month after expenses."
        )

    recommendations.append(
        f"Recommended tax regime: {tax_comp['recommended'].upper()} "
        f"— saves ₹{tax_comp['savings']:,}/year vs. the other regime."
    )

    if elss_data["eligible_80c"] > 0:
        recommendations.append(
            f"ELSS SIP of ₹{elss_monthly:,.0f}/month qualifies for ₹{elss_data['eligible_80c']:,} "
            f"80C deduction, saving ₹{elss_data['tax_saved_per_year']:,} in tax per year."
        )

    if nps_monthly > 0:
        recommendations.append(
            f"NPS contribution of ₹{nps_monthly:,.0f}/month can qualify for additional ₹50,000 "
            f"deduction under Section 80CCD(1B) — check with your tax advisor."
        )

    if sip_data["maturity"] > 0:
        recommendations.append(
            f"A SIP of ₹{sip_monthly:,.0f}/month at 12% p.a. for {horizon_years} years "
            f"could grow to ₹{sip_data['maturity']:,} (invested: ₹{sip_data['invested']:,})."
        )

    if epf_data["maturity"] > 0:
        recommendations.append(
            f"EPF corpus could grow to ₹{epf_data['maturity']:,} over {horizon_years} years."
        )

    return {
        "annual_gross": annual_gross,
        "investable_monthly": round(investable_monthly),
        "sip": sip_data,
        "epf": epf_data,
        "nps": nps_data,
        "elss": elss_data,
        "tax_comparison": tax_comp,
        "recommendations": recommendations,
        "disclaimer": (
            "Educational only — not tax or investment advice. "
            "Verify against current IT rules."
        ),
    }
