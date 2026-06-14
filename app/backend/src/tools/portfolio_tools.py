"""Markowitz mean-variance portfolio optimisation — Indian-market defaults.

Educational only — not personalised investment advice.

All return / volatility figures are annual; monetary amounts are INR (₹).
"""
from __future__ import annotations

import numpy as np

from .financial_utils import clamp

# ---------------------------------------------------------------------------
# Module-level capital-market assumptions (annual, Indian context)
# ---------------------------------------------------------------------------

ASSETS: list[str] = [
    "equity_largecap",
    "equity_midcap",
    "debt",
    "gold",
    "international",
]

# Expected nominal annual returns (decimal)
EXPECTED_RETURNS: np.ndarray = np.array([0.11, 0.13, 0.07, 0.08, 0.10])

# Annual standard deviations (decimal)
VOLATILITY: np.ndarray = np.array([0.16, 0.22, 0.05, 0.15, 0.18])

# Correlation matrix (5×5, symmetric, 1.0 diagonal)
# Order: equity_largecap, equity_midcap, debt, gold, international
CORRELATION: np.ndarray = np.array(
    [
        #  LC     MC    Debt   Gold   Intl
        [1.00,  0.80,  0.05, -0.10,  0.60],  # equity_largecap
        [0.80,  1.00,  0.00, -0.05,  0.55],  # equity_midcap
        [0.05,  0.00,  1.00,  0.10,  0.05],  # debt
        [-0.10, -0.05, 0.10,  1.00, -0.05],  # gold
        [0.60,  0.55,  0.05, -0.05,  1.00],  # international
    ]
)

# Covariance matrix derived once at import time
COVARIANCE: np.ndarray = np.outer(VOLATILITY, VOLATILITY) * CORRELATION

# Indian risk-free rate (~6.5 % nominal, roughly aligned with 10-yr G-Sec)
_RF: float = 0.065

_N_ASSETS: int = len(ASSETS)

# ---------------------------------------------------------------------------
# Core metric helper
# ---------------------------------------------------------------------------


def portfolio_metrics(
    weights: np.ndarray,
    mean_returns: np.ndarray,
    cov: np.ndarray,
) -> dict:
    """Compute annualised return, volatility, and Sharpe for a weight vector.

    Args:
        weights:      1-D array of asset weights (should sum to 1).
        mean_returns: 1-D array of expected annual returns (decimal).
        cov:          2-D covariance matrix (annual).

    Returns:
        {"return": float, "volatility": float, "sharpe": float}
    """
    ret = float(np.dot(weights, mean_returns))
    var = float(weights @ cov @ weights)
    vol = float(np.sqrt(max(var, 1e-12)))
    sharpe = (ret - _RF) / vol
    return {"return": ret, "volatility": vol, "sharpe": sharpe}


# ---------------------------------------------------------------------------
# Monte-Carlo sampling
# ---------------------------------------------------------------------------


def _random_portfolios(
    n: int,
    mean_returns: np.ndarray,
    cov: np.ndarray,
    seed_offset: int = 0,
) -> list[dict]:
    """Generate *n* random long-only portfolios via Dirichlet sampling.

    Uses a fixed seed (42 + seed_offset) for reproducibility.

    Returns a list of dicts with keys: weights, return, volatility, sharpe.
    """
    rng = np.random.default_rng(42 + seed_offset)
    # Dirichlet with alpha=1 gives uniform coverage of the simplex.
    weight_matrix = rng.dirichlet(np.ones(_N_ASSETS), size=n)  # (n, 5)

    portfolios: list[dict] = []
    for w in weight_matrix:
        m = portfolio_metrics(w, mean_returns, cov)
        portfolios.append(
            {
                "weights": w,
                "return": m["return"],
                "volatility": m["volatility"],
                "sharpe": m["sharpe"],
            }
        )
    return portfolios


# ---------------------------------------------------------------------------
# Optimiser
# ---------------------------------------------------------------------------


def optimize(
    mean_returns: np.ndarray | None = None,
    cov: np.ndarray | None = None,
    n_samples: int = 20_000,
    risk_tolerance: str = "moderate",
) -> dict:
    """Monte-Carlo mean-variance optimisation.

    Samples *n_samples* random portfolios from the simplex and identifies:
    - max-Sharpe portfolio
    - min-volatility portfolio
    - a "recommended" portfolio chosen by *risk_tolerance*

    Returns a dict with keys: assets, max_sharpe, min_volatility, recommended,
    frontier (list of ~50 {volatility, return} points along the efficient
    frontier sorted ascending by volatility).
    """
    if mean_returns is None:
        mean_returns = EXPECTED_RETURNS
    if cov is None:
        cov = COVARIANCE

    portfolios = _random_portfolios(n_samples, mean_returns, cov)

    # --- Identify key portfolios ---
    max_sharpe_p = max(portfolios, key=lambda p: p["sharpe"])
    min_vol_p = min(portfolios, key=lambda p: p["volatility"])

    rt = (risk_tolerance or "moderate").lower()

    if rt == "conservative":
        # Prefer min-volatility region: best Sharpe among lowest-20% vol
        vol_threshold = np.percentile([p["volatility"] for p in portfolios], 20)
        candidates = [p for p in portfolios if p["volatility"] <= vol_threshold]
        recommended_p = max(candidates, key=lambda p: p["sharpe"])
        label = "Conservative — Capital Preservation"
    elif rt == "aggressive":
        # Best return among top-20% Sharpe band
        sharpe_threshold = np.percentile([p["sharpe"] for p in portfolios], 80)
        candidates = [p for p in portfolios if p["sharpe"] >= sharpe_threshold]
        recommended_p = max(candidates, key=lambda p: p["return"])
        label = "Aggressive — Maximum Growth"
    else:
        # Moderate: max-Sharpe
        recommended_p = max_sharpe_p
        label = "Moderate — Balanced Growth"

    def _weights_dict(w: np.ndarray) -> dict[str, float]:
        """Convert weight array to {asset: rounded_percent} dict summing ~100."""
        pcts = [round(float(x) * 100, 1) for x in w]
        # Adjust largest weight so total is exactly 100
        diff = round(100.0 - sum(pcts), 1)
        if diff:
            idx = int(np.argmax(w))
            pcts[idx] = round(pcts[idx] + diff, 1)
        return dict(zip(ASSETS, pcts))

    def _fmt(p: dict) -> dict:
        return {
            "weights": _weights_dict(p["weights"]),
            "return": round(p["return"] * 100, 2),
            "volatility": round(p["volatility"] * 100, 2),
            "sharpe": round(p["sharpe"], 3),
        }

    # --- Efficient-frontier approximation (~50 points) ---
    # Bin portfolios by volatility, keep highest-return in each bin.
    vols = np.array([p["volatility"] for p in portfolios])
    rets = np.array([p["return"] for p in portfolios])
    vol_min, vol_max = vols.min(), vols.max()
    bins = np.linspace(vol_min, vol_max, 51)
    frontier_points: list[dict] = []
    for i in range(len(bins) - 1):
        mask = (vols >= bins[i]) & (vols < bins[i + 1])
        if mask.any():
            best_ret = rets[mask].max()
            mid_vol = (bins[i] + bins[i + 1]) / 2
            frontier_points.append(
                {"volatility": round(float(mid_vol) * 100, 2),
                 "return": round(float(best_ret) * 100, 2)}
            )
    frontier_points.sort(key=lambda x: x["volatility"])

    rec = _fmt(recommended_p)
    rec["label"] = label

    return {
        "assets": ASSETS,
        "max_sharpe": _fmt(max_sharpe_p),
        "min_volatility": _fmt(min_vol_p),
        "recommended": rec,
        "frontier": frontier_points,
    }


# ---------------------------------------------------------------------------
# High-level plan builder (mirrors build_investment_plan style)
# ---------------------------------------------------------------------------


def build_portfolio_plan(
    risk_tolerance: str,
    investable_monthly: float,
    current_portfolio: float = 0.0,
    horizon_years: int = 15,
) -> dict:
    """Run Markowitz optimisation and project growth of an INR portfolio.

    Monthly SIP is split across assets proportionally to recommended weights.
    Growth projection uses monthly compounding; yearly snapshots are returned.

    Returns a dict suitable for direct JSON serialisation.
    """
    opt = optimize(risk_tolerance=risk_tolerance)
    rec = opt["recommended"]

    # Expected annual return / vol in decimal form
    annual_return_pct: float = rec["return"]   # already in %
    annual_return_dec: float = annual_return_pct / 100.0
    annual_vol_pct: float = rec["volatility"]  # already in %

    # Monthly compounding projection
    monthly_rate = annual_return_dec / 12
    balance = float(current_portfolio)
    contributed = float(current_portfolio)
    projection: list[dict] = [
        {"year": 0, "balance": round(balance, 2), "contributed": round(contributed, 2)}
    ]
    monthly_contribution = max(float(investable_monthly), 0.0)
    for year in range(1, horizon_years + 1):
        for _ in range(12):
            balance = balance * (1 + monthly_rate) + monthly_contribution
            contributed += monthly_contribution
        projection.append(
            {"year": year,
             "balance": round(balance, 2),
             "contributed": round(contributed, 2)}
        )

    final = projection[-1]

    # ₹ monthly allocation per asset
    weight_pcts: dict[str, float] = rec["weights"]
    rupee_allocation: dict[str, float] = {
        asset: round(weight_pcts[asset] / 100.0 * monthly_contribution, 2)
        for asset in ASSETS
    }

    return {
        "risk_tolerance": (risk_tolerance or "moderate").lower(),
        "investable_monthly": round(monthly_contribution, 2),
        "horizon_years": horizon_years,
        "optimization": opt,
        "rupee_allocation": rupee_allocation,
        "expected_annual_return": annual_return_pct,
        "expected_volatility": annual_vol_pct,
        "sharpe": rec["sharpe"],
        "projection": projection,
        "projected_balance": final["balance"],
        "total_contributed": final["contributed"],
        "disclaimer": (
            "Illustrative mean-variance optimization on assumed capital-market "
            "expectations — not investment advice."
        ),
    }
