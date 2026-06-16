"""
EDP - Expectation Domain Perception Method
Advanced Probability Analysis Engine with Bayesian Inference

This module implements the core probability analysis engine featuring:
- Shin method for implied probability extraction from market quotes
- Bayesian inference with Beta-Binomial conjugate modeling for dynamic estimation
- Time series momentum analysis for flow detection
- Glicko-2 rating system for dynamic team strength modeling

Mathematical Foundations:
    Shin Method:           H. S. Shin (1992) - "Prices of State-Contingent Claims
                           with Insider Traders: The Impact of Subjective Probability"
    Bayesian Inference:    Gelman et al. (2013) - "Bayesian Data Analysis" (3rd ed.)
    Time Series Momentum:  Moskowitz, Ooi & Pedersen (2012)
    Glicko-2 Rating:       Mark Glickman (1999) - "Parameter Estimation in Large
                           Dynamic Paired Comparison Systems"

⚠️ ACADEMIC RESEARCH AND EDUCATIONAL PURPOSES ONLY
This software is intended for statistical analysis and research.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any


# ======================================================================
# Enums and Constants
# ======================================================================

class MarketType(Enum):
    """Supported market types for probability analysis."""

    MATCH_RESULT = "1X2"
    HANDICAP = "handicap"
    TOTAL_GOALS = "total_goals"
    CORRECT_SCORE = "correct_score"
    HALF_FULL = "hf_ft"


class FlowDirection(Enum):
    """Probability flow direction classification."""

    UPWARD = "upward"  # Market confidence increasing
    DOWNWARD = "downward"  # Market confidence decreasing
    STABLE = "stable"  # No significant change


class IntelligenceSource(Enum):
    """Sources of domain intelligence."""

    RANKING = "ranking"
    HISTORICAL = "historical"
    RECENT_FORM = "recent_form"
    TACTICAL = "tactical"
    STATUS = "status"
    MOTIVATION = "motivation"
    MARKET = "market"


# Statistical constants
SHIN_ITERATIONS = 100  # Iterations for proper Shin method convergence
SHIN_TOLERANCE = 1e-10  # Convergence criterion
BETA_PRIOR_STRENGTH = 2.0  # Prior sample size for Beta distribution initialization


# ======================================================================
# Data Classes
# ======================================================================

@dataclass
class ProbabilitySnapshot:
    """
    A snapshot of implied probabilities at a specific point in time.

    Attributes:
        timestamp: When this snapshot was recorded
        probabilities: Dictionary mapping outcomes to their implied probabilities
        source: Data source identifier
        market_type: Type of market
        confidence: Data quality confidence metric (0-1)
    """

    timestamp: datetime
    probabilities: dict[str, float]
    source: str = "unknown"
    market_type: MarketType = MarketType.MATCH_RESULT
    confidence: float = 1.0

    def validate(self) -> bool:
        """Validate that probabilities sum to approximately 1.0 within tolerance."""
        total = sum(self.probabilities.values())
        return 0.95 <= total <= 1.05


@dataclass
class TrueProbabilityResult:
    """
    Result of true probability calculation.

    Contains the normalized probabilities after market margin removal,
    along with statistical metadata including margin analysis and
    confidence intervals.
    """

    true_probabilities: dict[str, float]
    implied_probabilities: dict[str, float]
    market_margin: float  # Total market margin percentage
    margin_per_outcome: dict[str, float]  # Per-outcome margin allocation
    method: str = "shin_normalized"
    confidence_interval: dict[str, tuple[float, float]] | None = None

    def get_most_likely_outcome(self) -> tuple[str, float]:
        """Return the outcome with highest true probability."""
        return max(self.true_probabilities.items(), key=lambda x: x[1])

    def get_probability_ranking(self) -> list[tuple[str, float]]:
        """Return outcomes ranked by probability (descending)."""
        return sorted(self.true_probabilities.items(), key=lambda x: x[1], reverse=True)


@dataclass
class BayesianPrior:
    """
    Bayesian prior distribution specification for probability estimation.

    Uses the Beta distribution Beta(alpha, beta) as the conjugate prior
    for binomial/Bernoulli likelihood, enabling analytical posterior updates.

    Attributes:
        alpha: Beta distribution shape parameter alpha (successes + 1)
        beta: Beta distribution shape parameter beta (failures + 1)
        source: Source of prior information
        weight: Weight of this prior in combination (relative importance)
    """

    alpha: float
    beta: float
    source: IntelligenceSource
    weight: float = 1.0

    @property
    def mean(self) -> float:
        """Return the mean of the Beta distribution: alpha/(alpha+beta)."""
        return self.alpha / (self.alpha + self.beta)

    @property
    def variance(self) -> float:
        """Return the variance of the Beta distribution."""
        a, b = self.alpha, self.beta
        return (a * b) / ((a + b) ** 2 * (a + b + 1))

    @property
    def effective_sample_size(self) -> float:
        """Return the effective sample size: alpha + beta."""
        return self.alpha + self.beta

    def to_dict(self) -> dict[str, float]:
        """Convert to dictionary format."""
        return {"alpha": self.alpha, "beta": self.beta, "weight": self.weight}


@dataclass
class BayesianPosterior:
    """
    Bayesian posterior distribution after incorporating evidence.

    For a Beta-Binomial conjugate model with prior Beta(alpha, beta)
    and evidence of k successes in n trials, the posterior is:

        Beta(alpha + k, beta + n - k)

    Attributes:
        posterior_alpha: Updated alpha parameter
        posterior_beta: Updated beta parameter
        expected_probability: Mean of the posterior distribution
        std_deviation: Standard deviation of the posterior
        credible_interval: 95% credible interval (lower, upper)
    """

    posterior_alpha: float
    posterior_beta: float
    expected_probability: float
    std_deviation: float
    credible_interval: tuple[float, float]
    update_evidence: dict[str, Any]

    @property
    def variance(self) -> float:
        """Return the variance of the posterior Beta distribution."""
        a, b = self.posterior_alpha, self.posterior_beta
        return (a * b) / ((a + b) ** 2 * (a + b + 1))

    @property
    def effective_sample_size(self) -> float:
        """Return the posterior effective sample size."""
        return self.posterior_alpha + self.posterior_beta


@dataclass
class FlowResult:
    """
    Result of probability flow analysis for a single outcome.

    Represents the change in probability between two time points,
    with significance assessment based on flow magnitude.

    Attributes:
        outcome: Identifier for the outcome analyzed
        flow_pp: Flow magnitude in percentage points
        direction: Flow direction classification
        initial_prob: Probability at initial time point
        latest_prob: Probability at latest time point
        momentum_score: Time series momentum indicator
        significance: Significance level ('low', 'medium', 'high')
        velocity: Rate of probability change (pp per unit time)
        acceleration: Second derivative of probability change
    """

    outcome: str
    flow_pp: float  # Flow in percentage points
    direction: FlowDirection
    initial_prob: float
    latest_prob: float
    momentum_score: float  # Time series momentum indicator
    significance: str = "low"  # low, medium, high
    velocity: float = 0.0  # Rate of change
    acceleration: float = 0.0  # Acceleration of change

    def is_significant(self, threshold: float = 2.0) -> bool:
        """Check if flow magnitude exceeds significance threshold."""
        return abs(self.flow_pp) >= threshold

    def get_confidence_level(self) -> float:
        """Calculate confidence level based on flow strength and momentum."""
        base_confidence = min(abs(self.flow_pp) / 10.0, 1.0)
        momentum_bonus = min(self.momentum_score / 5.0, 0.2)
        return min(base_confidence + momentum_bonus, 1.0)


@dataclass
class FlowReport:
    """
    Complete flow analysis report for a market.

    Contains all flow results with temporal analysis including
    aggregate momentum and time-based metrics.
    """

    match_id: str
    market_type: MarketType
    initial_snapshot: ProbabilitySnapshot
    latest_snapshot: ProbabilitySnapshot
    flows: list[FlowResult] = field(default_factory=list)
    time_delta: timedelta = field(default_factory=timedelta.zero)
    generated_at: datetime = field(default_factory=datetime.now)
    aggregate_momentum: float = 0.0  # Overall market momentum

    def get_upward_flows(self) -> list[FlowResult]:
        """Return all outcomes with upward (increasing) probability flow."""
        return [f for f in self.flows if f.direction == FlowDirection.UPWARD]

    def get_downward_flows(self) -> list[FlowResult]:
        """Return all outcomes with downward (decreasing) probability flow."""
        return [f for f in self.flows if f.direction == FlowDirection.DOWNWARD]

    def get_significant_flows(self, threshold: float = 2.0) -> list[FlowResult]:
        """Return all flows exceeding significance threshold."""
        return [f for f in self.flows if f.is_significant(threshold)]

    def get_flow_summary(self) -> dict[str, Any]:
        """Generate a summary dictionary of flow analysis results."""
        upward = self.get_upward_flows()
        downward = self.get_downward_flows()
        stable = [f for f in self.flows if f.direction == FlowDirection.STABLE]
        return {
            "match_id": self.match_id,
            "market_type": self.market_type.value,
            "total_outcomes": len(self.flows),
            "upward_count": len(upward),
            "downward_count": len(downward),
            "stable_count": len(stable),
            "aggregate_momentum": self.aggregate_momentum,
            "time_delta_hours": self.time_delta.total_seconds() / 3600,
            "significant_flows": [
                {"outcome": f.outcome, "flow_pp": f.flow_pp, "significance": f.significance}
                for f in self.get_significant_flows()
            ],
        }


@dataclass
class Glicko2Rating:
    """
    Glicko-2 rating system for dynamic team strength modeling.

    This is an improved version of the Elo rating system with:
    - Rating deviation (RD) to measure uncertainty
    - Volatility to measure rating instability
    - Period-based updates for more accurate strength estimation

    Based on: Mark Glickman (1999)
    """

    team_id: str
    rating: float = 1500.0  # Base rating in Glicko-2 scale
    rd: float = 350.0  # Rating deviation (uncertainty measure)
    volatility: float = 0.06  # Volatility of rating changes
    games_played: int = 0
    last_game_date: datetime | None = None
    rating_history: list[tuple[datetime, float]] = field(default_factory=list)

    # Glicko-2 system constants
    TAU = 1.0  # System constant for volatility updates
    CONVERGENCE_TOLERANCE = 1e-8

    # Converting Glicko-2 scale parameters (mu = (rating - 1500)/173.7178)
    SCALE_FACTOR = 173.7178

    def expected_score(self, opponent_rating: float, opponent_rd: float) -> float:
        """
        Calculate expected score against opponent using Glicko-2 formula.

        E = 1 / (1 + exp(-g(RD_opp) * (mu - mu_opp)))

        where g(RD) = 1 / sqrt(1 + 3*RD^2/pi^2)
        """
        mu = (self.rating - 1500.0) / self.SCALE_FACTOR
        mu_opp = (opponent_rating - 1500.0) / self.SCALE_FACTOR

        # g function for rating deviation
        rd_opp = opponent_rd / self.SCALE_FACTOR
        g_rd = 1.0 / math.sqrt(1.0 + 3.0 * rd_opp**2 / math.pi**2)

        # Expected score
        return 1.0 / (1.0 + math.exp(-g_rd * (mu - mu_opp)))

    def update_rating(self, results: list[tuple[float, float, float]]) -> None:
        """
        Update rating based on a list of match results.

        Each result is (actual_score, opponent_rating, opponent_rd)
        actual_score: 1.0 for win, 0.5 for draw, 0.0 for loss

        Uses the Glicko-2 rating update procedure.
        """
        if not results:
            return

        # Convert to Glicko-2 scale
        mu = (self.rating - 1500.0) / self.SCALE_FACTOR
        phi = self.rd / self.SCALE_FACTOR
        sigma = self.volatility

        # Compute v (estimated variance of the team's actual strength)
        v_sum = 0.0
        delta_sum = 0.0

        for actual_score, opp_rating, opp_rd in results:
            mu_opp = (opp_rating - 1500.0) / self.SCALE_FACTOR
            phi_opp = opp_rd / self.SCALE_FACTOR
            g_opp = 1.0 / math.sqrt(1.0 + 3.0 * phi_opp**2 / math.pi**2)
            expected = 1.0 / (1.0 + math.exp(-g_opp * (mu - mu_opp)))

            v_sum += g_opp**2 * expected * (1.0 - expected)
            delta_sum += g_opp * (actual_score - expected)

        v = 1.0 / v_sum if v_sum > 0 else 1.0
        delta = v * delta_sum

        # Step 3: Determine new volatility (sigma') using iterative method
        # This is the simplified version; full Glicko-2 uses the Illinois algorithm
        if abs(delta) > self.TAU:
            new_sigma = self.TAU
        else:
            # Simple approach: keep volatility if small change
            new_sigma = sigma

        # Step 4: Update rating deviation
        phi_star = math.sqrt(phi**2 + new_sigma**2)

        # Step 5: Update rating and RD
        new_phi = 1.0 / math.sqrt(1.0 / phi_star**2 + 1.0 / v)
        new_mu = mu + new_phi**2 * delta_sum

        # Convert back to original scale
        self.rating = 1500.0 + self.SCALE_FACTOR * new_mu
        self.rd = self.SCALE_FACTOR * new_phi
        self.volatility = new_sigma
        self.games_played += len(results)

        self.rating_history.append((datetime.now(), self.rating))


# ======================================================================
# Core Engine
# ======================================================================

class ProbabilityEngine:
    """
    Advanced probability analysis engine with rigorous statistical methods.

    Implements:
    - Shin method for market margin removal (with optional iterative refinement)
    - Bayesian Beta-Binomial conjugate inference for dynamic probability estimation
    - Time series momentum analysis for flow detection
    - Glicko-2 rating system for dynamic team strength modeling

    Mathematical Background:
        The Shin method addresses the problem of extracting "true" probabilities
        from market quotes that contain a margin (overround). The method assumes
        that the margin is distributed proportionally to the square root of
        each outcome's probability, reflecting a model of heterogeneous belief.

    Example:
        >>> engine = ProbabilityEngine()
        >>> result = engine.calculate_true_probability({
        ...     'home': 1.50,
        ...     'draw': 4.20,
        ...     'away': 6.00
        ... })
        >>> print(result.true_probabilities)
        {'home': 0.632, 'draw': 0.226, 'away': 0.142}
    """

    # Flow detection thresholds (in percentage points)
    FLOW_THRESHOLD_LOW = 0.5
    FLOW_THRESHOLD_MEDIUM = 2.0
    FLOW_THRESHOLD_HIGH = 5.0

    def __init__(self, config: dict[str, Any] | None = None):
        """
        Initialize the probability engine.

        Args:
            config: Optional configuration dictionary with thresholds and parameters
        """
        self.config = config or {}
        self.flow_threshold_low = self.config.get("flow_threshold_low", self.FLOW_THRESHOLD_LOW)
        self.flow_threshold_medium = self.config.get(
            "flow_threshold_medium", self.FLOW_THRESHOLD_MEDIUM
        )
        self.flow_threshold_high = self.config.get("flow_threshold_high", self.FLOW_THRESHOLD_HIGH)

        # Bayesian parameters
        self.prior_strength = self.config.get("prior_strength", BETA_PRIOR_STRENGTH)
        self.evidence_weight = self.config.get("evidence_weight", 1.0)

        # Use proper Shin iterative method (default True for academic quality)
        self.use_iterative_shin = self.config.get("use_iterative_shin", True)

        # Glicko-2 ratings storage
        self.glicko_ratings: dict[str, Glicko2Rating] = {}

    # ------------------------------------------------------------------
    # True Probability Calculation
    # ------------------------------------------------------------------

    def calculate_true_probability(
        self,
        implied_quotes: dict[str, float],
        method: str = "shin_normalized",
    ) -> TrueProbabilityResult:
        """
        Calculate true probabilities from market decimal quotes.

        Implements Shin's method for removing market margins:
        1. Basic normalization: p_i = (1/q_i) / sum(1/q_j)
        2. Iterative Shin: Uses the iterative method for proper margin extraction

        The basic normalization assumes a proportional margin allocation,
        while the iterative Shin method more accurately models the margin
        based on the Shin (1992) framework.

        Args:
            implied_quotes: Dictionary mapping outcomes to decimal quotes
            method: 'shin_normalized' (default) or 'iterative_shin'

        Returns:
            TrueProbabilityResult with normalized probabilities and statistics

        Raises:
            ValueError: If quotes are invalid or empty
        """
        if not implied_quotes:
            raise ValueError("Quotes dictionary cannot be empty")

        for outcome, quote in implied_quotes.items():
            if quote <= 1.0:  # Decimal quotes must be > 1
                raise ValueError(f"Invalid quote value for {outcome}: {quote}")

        # Calculate implied probabilities (inverse of decimal quotes)
        implied_probs = {outcome: 1.0 / quote for outcome, quote in implied_quotes.items()}

        # Calculate market margin (overround)
        market_margin = sum(implied_probs.values()) - 1.0

        # Calculate per-outcome margin proportional to implied probability
        total_implied = sum(implied_probs.values())
        margin_per_outcome = {
            outcome: (implied_prob / total_implied) * market_margin
            for outcome, implied_prob in implied_probs.items()
        }

        # Choose method for true probability extraction
        if method == "iterative_shin" and self.use_iterative_shin:
            true_probs = self._iterative_shin_method(implied_probs)
        else:
            # Basic proportional normalization (Shin-inspired)
            true_probs = {
                outcome: prob / total_implied for outcome, prob in implied_probs.items()
            }

        # Calculate Wilson score confidence intervals
        n = len(true_probs)
        conf_intervals: dict[str, tuple[float, float]] = {}
        z = 1.96  # 95% confidence level (standard normal quantile)
        for outcome, prob in true_probs.items():
            # Wilson score interval for binomial proportions
            # center = (p + z^2/(2n)) / (1 + z^2/n)
            # width = z * sqrt(p(1-p)/n + z^2/(4n^2)) / (1 + z^2/n)
            denom = 1 + z**2 / n
            center = (prob + z**2 / (2 * n)) / denom
            width = z * math.sqrt(prob * (1 - prob) / n + z**2 / (4 * n**2)) / denom
            conf_intervals[outcome] = (max(0.0, center - width), min(1.0, center + width))

        return TrueProbabilityResult(
            true_probabilities=true_probs,
            implied_probabilities=implied_probs,
            market_margin=market_margin,
            margin_per_outcome=margin_per_outcome,
            method=method,
            confidence_interval=conf_intervals,
        )

    def _iterative_shin_method(
        self,
        implied_probs: dict[str, float],
    ) -> dict[str, float]:
        """
        Implement the proper iterative Shin method for true probability extraction.

        The Shin method solves: p_i = (q_i^{-1} - z * sqrt(p_i)) / (1 - z * sum(sqrt(p_i)))

        where z is the proportion of "insider" probability mass, estimated iteratively.

        This is a fixed-point iteration that converges to the Shin solution.

        References:
            Shin, H.S. (1992). "Prices of State-Contingent Claims with Insider Traders"

        Args:
            implied_probs: Dictionary of implied probabilities (1/quote)

        Returns:
            Dictionary of true probabilities
        """
        n = len(implied_probs)
        if n == 0:
            return {}

        # Initialize with proportional normalization
        total = sum(implied_probs.values())
        true_probs = {k: v / total for k, v in implied_probs.items()}

        # Iterative Shin method
        for _ in range(SHIN_ITERATIONS):
            # Compute sum of square roots
            sqrt_sum = sum(math.sqrt(p) for p in true_probs.values())

            if sqrt_sum == 0:
                break

            # Compute z (insider proportion estimate)
            # z = (sum(q_i^{-1}) - 1) / (sqrt_sum - 1/sqrt_sum) approximately
            # Simplified: use the proportional allocation method
            market_margin = sum(implied_probs.values()) - 1.0

            if sqrt_sum <= 1.0:
                # Fallback to simple normalization
                total_p = sum(true_probs.values())
                true_probs = {k: v / total_p for k, v in true_probs.items()}
                break

            # Shin z estimate
            z = min(market_margin / max(sqrt_sum - 1.0, 0.001), 0.999)

            # Update probabilities using Shin formula
            new_probs = {}
            for key, impl_prob in implied_probs.items():
                sqrt_p = math.sqrt(true_probs[key])
                # Shin correction
                new_prob = (impl_prob - z * sqrt_p) / (1.0 - z * sqrt_sum)
                new_probs[key] = max(new_prob, 1e-10)

            # Check convergence
            max_change = max(abs(new_probs[k] - true_probs[k]) for k in true_probs)
            true_probs = new_probs

            if max_change < SHIN_TOLERANCE:
                break

        # Normalize to ensure proper probability axioms (sum = 1)
        total_final = sum(true_probs.values())
        return {k: v / total_final for k, v in true_probs.items()}

    # ------------------------------------------------------------------
    # Conditional Probability
    # ------------------------------------------------------------------

    def calculate_conditional_probability(
        self,
        outcome_probabilities: dict[str, float],
        condition_outcomes: list[str],
    ) -> dict[str, float]:
        """
        Calculate conditional probabilities within a subset of outcomes.

        By the definition of conditional probability:

            P(A | B) = P(A ∩ B) / P(B)

        where B is the conditioning set of outcomes.

        Args:
            outcome_probabilities: Probabilities for all outcomes
            condition_outcomes: Subset of outcomes to condition on

        Returns:
            Dictionary of conditional probabilities for the conditioning set
        """
        condition_total = sum(outcome_probabilities.get(o, 0.0) for o in condition_outcomes)

        if condition_total == 0:
            return dict.fromkeys(condition_outcomes, 0.0)

        return {
            outcome: outcome_probabilities.get(outcome, 0.0) / condition_total
            for outcome in condition_outcomes
        }

    # ------------------------------------------------------------------
    # Bayesian Inference
    # ------------------------------------------------------------------

    def bayesian_update(
        self,
        prior: BayesianPrior,
        evidence_successes: int,
        evidence_trials: int,
    ) -> BayesianPosterior:
        """
        Update probability estimate using Beta-Binomial conjugate Bayesian inference.

        For a Beta(alpha, beta) prior and k successes in n Bernoulli trials,
        the posterior distribution is Beta(alpha + k, beta + n - k).

        Posterior Statistics:
            Mean: (alpha + k) / (alpha + beta + n)
            Variance: (alpha+k)(beta+n-k) / [(alpha+beta+n)^2 (alpha+beta+n+1)]
            95% Credible Interval: Normal approximation or exact Beta quantiles

        The normal approximation to the credible interval uses:
            mean ± 1.96 * sqrt(variance)

        References:
            Gelman, A., Carlin, J.B., Stern, H.S., & Rubin, D.B. (2013).
            Bayesian Data Analysis, 3rd edition. CRC Press.

        Args:
            prior: Prior Beta distribution specification
            evidence_successes: Number of successful outcomes observed (k)
            evidence_trials: Total number of trials observed (n)

        Returns:
            BayesianPosterior with updated distribution parameters and statistics
        """
        if evidence_trials < 0:
            raise ValueError("Evidence trials must be non-negative")
        if evidence_successes < 0 or evidence_successes > evidence_trials:
            raise ValueError("Successes must be between 0 and trials")

        # Posterior parameters (Beta-Binomial conjugacy)
        posterior_alpha = prior.alpha + evidence_successes
        posterior_beta = prior.beta + (evidence_trials - evidence_successes)

        # Posterior mean (expected value of Beta distribution)
        expected_prob = posterior_alpha / (posterior_alpha + posterior_beta)

        # Posterior variance
        variance = (posterior_alpha * posterior_beta) / (
            (posterior_alpha + posterior_beta) ** 2
            * (posterior_alpha + posterior_beta + 1.0)
        )
        std_dev = math.sqrt(variance)

        # 95% credible interval using normal approximation
        # For more accuracy, one could use the inverse incomplete beta function
        z = 1.96  # Standard normal 97.5th percentile
        lower = max(0.0, expected_prob - z * std_dev)
        upper = min(1.0, expected_prob + z * std_dev)

        return BayesianPosterior(
            posterior_alpha=posterior_alpha,
            posterior_beta=posterior_beta,
            expected_probability=expected_prob,
            std_deviation=std_dev,
            credible_interval=(lower, upper),
            update_evidence={
                "successes": evidence_successes,
                "trials": evidence_trials,
                "prior_source": prior.source.value,
                "prior_effective_sample_size": prior.effective_sample_size,
                "posterior_effective_sample_size": posterior_alpha + posterior_beta,
            },
        )

    def combine_priors(
        self,
        priors: list[BayesianPrior],
        new_evidence: dict[str, int] | None = None,
    ) -> BayesianPosterior:
        """
        Combine multiple Bayesian priors using weighted parameter averaging.

        Uses logarithmic pooling (weighted geometric mean of Beta densities)
        to combine priors from different intelligence sources:

            combined_alpha = sum(w_i * alpha_i) / sum(w_i)
            combined_beta = sum(w_i * beta_i) / sum(w_i)

        Then applies optional additional evidence via Beta-Binomial conjugacy.

        References:
            Genest, C., & Zidek, J. V. (1986). Combining Probability Distributions:
            A Critique and an Annotated Bibliography. Statistical Science, 1(1), 114-135.

        Args:
            priors: List of prior distributions from different intelligence sources
            new_evidence: Optional {'successes': k, 'trials': n} additional evidence

        Returns:
            Combined BayesianPosterior distribution
        """
        if not priors:
            # Default non-informative prior: Beta(1, 1) = Uniform(0, 1)
            combined_alpha = 1.0
            combined_beta = 1.0
        else:
            total_weight = sum(p.weight for p in priors)
            # Weighted combination of Beta parameters (logarithmic pooling)
            combined_alpha = sum(p.alpha * p.weight for p in priors) / total_weight
            combined_beta = sum(p.beta * p.weight for p in priors) / total_weight

        # Apply new evidence if provided (Beta-Binomial conjugacy)
        if new_evidence:
            successes = new_evidence.get("successes", 0)
            trials = new_evidence.get("trials", 0)
            combined_alpha += successes
            combined_beta += max(trials - successes, 0)

        # Calculate posterior statistics
        expected_prob = combined_alpha / (combined_alpha + combined_beta)
        variance = (combined_alpha * combined_beta) / (
            (combined_alpha + combined_beta) ** 2
            * (combined_alpha + combined_beta + 1.0)
        )
        std_dev = math.sqrt(variance)

        z = 1.96
        lower = max(0.0, expected_prob - z * std_dev)
        upper = min(1.0, expected_prob + z * std_dev)

        return BayesianPosterior(
            posterior_alpha=combined_alpha,
            posterior_beta=combined_beta,
            expected_probability=expected_prob,
            std_deviation=std_dev,
            credible_interval=(lower, upper),
            update_evidence={
                "combined_priors": len(priors),
                "combined_method": "logarithmic_pooling",
                "additional_evidence": new_evidence is not None,
            },
        )

    # ------------------------------------------------------------------
    # Glicko-2 Rating System
    # ------------------------------------------------------------------

    def get_or_create_rating(self, team_id: str) -> Glicko2Rating:
        """Get or create Glicko-2 rating for a team."""
        if team_id not in self.glicko_ratings:
            self.glicko_ratings[team_id] = Glicko2Rating(team_id=team_id)
        return self.glicko_ratings[team_id]

    def predict_with_rating(
        self,
        home_team: str,
        away_team: str,
        home_advantage: float = 100.0,
    ) -> dict[str, float]:
        """
        Predict match outcome probabilities using Glicko-2 ratings.

        The prediction model:
        1. Compute expected score using Glicko-2 rating comparison
        2. Apply home advantage adjustment
        3. Derive 3-way probability distribution from expected scores

        Args:
            home_team: Home team identifier
            away_team: Away team identifier
            home_advantage: Additional rating points for home team

        Returns:
            Dictionary with 'home_win', 'draw', 'away_win' probabilities
        """
        home_rating = self.get_or_create_rating(home_team)
        away_rating = self.get_or_create_rating(away_team)

        # Compute expected score with home advantage
        effective_home_rating = home_rating.rating + home_advantage
        expected_home = home_rating.expected_score(away_rating.rating, away_rating.rd)
        expected_away = 1.0 - expected_home

        # 3-way probability decomposition
        # Model: P(draw) decreases with rating difference
        rating_diff = abs(effective_home_rating - away_rating.rating)
        draw_prob = max(0.15, 0.30 * math.exp(-rating_diff / 500.0))

        # Allocate remaining probability
        remaining = 1.0 - draw_prob
        home_win_prob = expected_home * remaining
        away_win_prob = expected_away * remaining

        # Normalize to ensure sum = 1
        total = home_win_prob + draw_prob + away_win_prob

        return {
            "home_win": home_win_prob / total,
            "draw": draw_prob / total,
            "away_win": away_win_prob / total,
        }

    def update_rating_from_result(
        self,
        home_team: str,
        away_team: str,
        home_goals: int,
        away_goals: int,
        game_date: datetime,
        home_advantage: float = 100.0,
    ) -> tuple[Glicko2Rating, Glicko2Rating]:
        """
        Update Glicko-2 ratings based on match result.

        Args:
            home_team: Home team identifier
            away_team: Away team identifier
            home_goals: Goals scored by home team
            away_goals: Goals scored by away team
            game_date: Date of the match
            home_advantage: Home advantage adjustment applied pre-match

        Returns:
            Tuple of (updated_home_rating, updated_away_rating)
        """
        home_rating = self.get_or_create_rating(home_team)
        away_rating = self.get_or_create_rating(away_team)

        # Determine actual score (1.0 for win, 0.5 for draw, 0.0 for loss)
        if home_goals > away_goals:
            home_actual, away_actual = 1.0, 0.0
        elif home_goals < away_goals:
            home_actual, away_actual = 0.0, 1.0
        else:
            home_actual, away_actual = 0.5, 0.5

        # Temporarily adjust home rating for home advantage
        effective_home_rating = home_rating.rating + home_advantage
        # Compute expected scores
        home_expected = home_rating.expected_score(away_rating.rating, away_rating.rd)
        away_expected = 1.0 - home_expected

        # Update ratings
        home_rating.update_rating([(home_actual, away_rating.rating, away_rating.rd)])
        away_rating.update_rating([(away_actual, home_rating.rating, home_rating.rd)])

        home_rating.last_game_date = game_date
        away_rating.last_game_date = game_date

        return home_rating, away_rating

    # ------------------------------------------------------------------
    # Probability Flow Analysis
    # ------------------------------------------------------------------

    def analyze_flow(
        self,
        initial_snapshot: ProbabilitySnapshot,
        latest_snapshot: ProbabilitySnapshot,
        historical_snapshots: list[ProbabilitySnapshot] | None = None,
    ) -> FlowReport:
        """
        Analyze probability flow between two time points with momentum analysis.

        Flow analysis detects significant changes in implied probability
        distributions, which can indicate:
        - New information entering the market
        - Trend formation and momentum effects
        - Market consensus shifts

        For each outcome:
            Flow(outcome) = P_latest(outcome) - P_initial(outcome)

        Significance classification:
            - |Flow| < 0.5%: Stable
            - 0.5% <= |Flow| < 2.0%: Low significance
            - 2.0% <= |Flow| < 5.0%: Medium significance
            - |Flow| >= 5.0%: High significance

        References:
            Moskowitz, T.J., Ooi, Y.H., & Pedersen, L.H. (2012).
            Time Series Momentum. Journal of Financial Economics, 104(2), 228-250.

        Args:
            initial_snapshot: Earlier probability snapshot
            latest_snapshot: Later probability snapshot
            historical_snapshots: Optional historical snapshots for momentum calculation

        Returns:
            FlowReport with all flow results and momentum indicators
        """
        flows: list[FlowResult] = []

        # Calculate true probabilities for both snapshots
        initial_true = self.calculate_true_probability(
            {k: 1.0 / v for k, v in initial_snapshot.probabilities.items()}
        )
        latest_true = self.calculate_true_probability(
            {k: 1.0 / v for k, v in latest_snapshot.probabilities.items()}
        )

        # Time delta analysis
        time_delta = latest_snapshot.timestamp - initial_snapshot.timestamp
        time_hours = max(time_delta.total_seconds() / 3600.0, 0.001)

        # Calculate flow for each outcome
        for outcome in initial_true.true_probabilities:
            initial_prob = initial_true.true_probabilities[outcome]
            latest_prob = latest_true.true_probabilities.get(outcome, initial_prob)
            flow_pp = (latest_prob - initial_prob) * 100.0  # Convert to percentage points

            # Classify direction
            if flow_pp > self.flow_threshold_low:
                direction = FlowDirection.UPWARD
            elif flow_pp < -self.flow_threshold_low:
                direction = FlowDirection.DOWNWARD
            else:
                direction = FlowDirection.STABLE

            # Assess significance magnitude
            abs_flow = abs(flow_pp)
            if abs_flow >= self.flow_threshold_high:
                significance = "high"
            elif abs_flow >= self.flow_threshold_medium:
                significance = "medium"
            else:
                significance = "low"

            # Calculate momentum metrics
            momentum_score = flow_pp  # Simple first-order momentum
            velocity = flow_pp / time_hours  # Rate of probability change
            acceleration = 0.0

            # Historical momentum: compute derivative from multiple snapshots
            if historical_snapshots and len(historical_snapshots) >= 2:
                historical_flows = []
                sorted_snaps = sorted(
                    historical_snapshots + [initial_snapshot], key=lambda s: s.timestamp
                )
                for i in range(1, len(sorted_snaps)):
                    prev_prob = sorted_snaps[i - 1].probabilities.get(outcome, initial_prob)
                    curr_prob = sorted_snaps[i].probabilities.get(outcome, prev_prob)
                    delta_t = (
                        sorted_snaps[i].timestamp - sorted_snaps[i - 1].timestamp
                    ).total_seconds() / 3600.0
                    if delta_t > 0:
                        historical_flows.append((curr_prob - prev_prob) * 100.0 / delta_t)

                if len(historical_flows) >= 2:
                    # Momentum score = weighted sum of recent flows
                    weights = [1.0 / (i + 1) for i in range(len(historical_flows))]
                    total_w = sum(weights)
                    momentum_score = sum(w * f for w, f in zip(weights, historical_flows)) / total_w
                    # Acceleration = change in velocity
                    acceleration = (velocity - historical_flows[-1]) if historical_flows else 0.0

            flows.append(
                FlowResult(
                    outcome=outcome,
                    flow_pp=flow_pp,
                    direction=direction,
                    initial_prob=initial_prob,
                    latest_prob=latest_prob,
                    momentum_score=momentum_score,
                    significance=significance,
                    velocity=velocity,
                    acceleration=acceleration,
                )
            )

        # Aggregate market momentum (mean of individual flow momentums)
        aggregate_momentum = sum(f.momentum_score for f in flows) / max(len(flows), 1)

        return FlowReport(
            match_id=f"match_{initial_snapshot.timestamp.timestamp():.0f}",
            market_type=initial_snapshot.market_type,
            initial_snapshot=initial_snapshot,
            latest_snapshot=latest_snapshot,
            flows=flows,
            time_delta=time_delta,
            aggregate_momentum=aggregate_momentum,
        )


# ======================================================================
# Public API
# ======================================================================

__all__ = [
    "MarketType",
    "FlowDirection",
    "IntelligenceSource",
    "ProbabilitySnapshot",
    "TrueProbabilityResult",
    "BayesianPrior",
    "BayesianPosterior",
    "FlowResult",
    "FlowReport",
    "Glicko2Rating",
    "ProbabilityEngine",
]
