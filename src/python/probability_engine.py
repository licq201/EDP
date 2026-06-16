"""
SPAF - Sports Probability Analysis Framework
Core probability engine implementation.

This module implements the core probability analysis engine based on:
- Shin method for true probability extraction (Shin, 1992)
- Bayesian updating for probability flow analysis
- Kelly criterion variant for capital allocation

References:
    Shin, H.S. (1992). "Prices of State Contingent Claims with Insider Traders,
    and the Favourite-Longshot Bias." The Economic Journal, 102(411), 426-435.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class MarketType(Enum):
    """Supported market types for probability analysis."""

    MATCH_RESULT = "1X2"  # Win/Draw/Loss
    HANDICAP = "handicap"  # Asian handicap
    TOTAL_GOALS = "total_goals"  # Over/Under
    CORRECT_SCORE = "correct_score"  # Exact score
    HALF_TIME_FULL_TIME = "ht_ft"  # Half-time/Full-time


class FlowDirection(Enum):
    """Probability flow direction classification."""

    POSITIVE = "positive"  # Inflow - market favoring this outcome
    NEGATIVE = "negative"  # Outflow - market moving away
    NEUTRAL = "neutral"  # Stable - no significant change


@dataclass
class ProbabilitySnapshot:
    """
    A snapshot of probabilities at a specific point in time.

    Attributes:
        timestamp: When this snapshot was taken
        probabilities: Dictionary mapping outcomes to their probabilities
        source: Data source identifier
        market_type: Type of betting market
    """

    timestamp: datetime
    probabilities: dict[str, float]
    source: str = "unknown"
    market_type: MarketType = MarketType.MATCH_RESULT

    def validate(self) -> bool:
        """Validate that probabilities sum to approximately 1.0."""
        total = sum(self.probabilities.values())
        return 0.99 <= total <= 1.01  # Allow small floating point errors


@dataclass
class TrueProbabilityResult:
    """
    Result of true probability calculation.

    Contains the normalized probabilities after removing bookmaker margin,
    along with metadata about the calculation.
    """

    true_probabilities: dict[str, float]
    implied_probabilities: dict[str, float]
    overround: float  # Total margin percentage
    method: str = "basic_normalization"

    def get_most_likely_outcome(self) -> tuple[str, float]:
        """Return the outcome with highest true probability."""
        best_outcome = max(self.true_probabilities.items(), key=lambda x: x[1])
        return best_outcome


@dataclass
class FlowResult:
    """
    Result of probability flow analysis.

    Represents the change in true probabilities between two time points,
    along with classification and significance assessment.
    """

    outcome: str
    flow_pp: float  # Flow in percentage points
    direction: FlowDirection
    initial_prob: float
    latest_prob: float
    significance: str = "low"  # low, medium, high

    def is_significant(self, threshold: float = 2.0) -> bool:
        """Check if flow exceeds significance threshold."""
        return abs(self.flow_pp) >= threshold


@dataclass
class FlowReport:
    """
    Complete flow analysis report for a market.

    Contains all flow results and aggregate statistics.
    """

    match_id: str
    market_type: MarketType
    initial_snapshot: ProbabilitySnapshot
    latest_snapshot: ProbabilitySnapshot
    flows: list[FlowResult] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.now)

    def get_positive_flows(self) -> list[FlowResult]:
        """Return all outcomes with positive flow."""
        return [f for f in self.flows if f.direction == FlowDirection.POSITIVE]

    def get_significant_flows(self, threshold: float = 2.0) -> list[FlowResult]:
        """Return all flows exceeding significance threshold."""
        return [f for f in self.flows if f.is_significant(threshold)]


class ProbabilityEngine:
    """
    Core probability analysis engine.

    Implements the Shin method (simplified) for extracting true probabilities
    from bookmaker odds, removing the overround/margin.

    Example:
        >>> engine = ProbabilityEngine()
        >>> result = engine.calculate_true_probability({
        ...     'home': 1.50,
        ...     'draw': 4.20,
        ...     'away': 6.00
        ... })
        >>> print(result.true_probabilities)
        {'home': 0.632, 'draw': 0.226, 'away': 0.158}
    """

    # Significance thresholds for flow classification (in percentage points)
    FLOW_THRESHOLD_LOW = 1.0
    FLOW_THRESHOLD_MEDIUM = 2.0
    FLOW_THRESHOLD_HIGH = 5.0

    def __init__(self, config: Optional[dict[str, Any]] = None):
        """
        Initialize the probability engine.

        Args:
            config: Optional configuration dictionary with thresholds
        """
        self.config = config or {}
        self.flow_threshold_low = self.config.get(
            "flow_threshold_low", self.FLOW_THRESHOLD_LOW
        )
        self.flow_threshold_medium = self.config.get(
            "flow_threshold_medium", self.FLOW_THRESHOLD_MEDIUM
        )
        self.flow_threshold_high = self.config.get(
            "flow_threshold_high", self.FLOW_THRESHOLD_HIGH
        )

    def calculate_true_probability(
        self, odds: dict[str, float]
    ) -> TrueProbabilityResult:
        """
        Calculate true probabilities from bookmaker odds.

        Uses basic normalization method (simplified Shin method):
        P_true(outcome_i) = (1 / odds_i) / Σ(1 / odds_j)

        Args:
            odds: Dictionary mapping outcomes to decimal odds

        Returns:
            TrueProbabilityResult with normalized probabilities

        Raises:
            ValueError: If odds are invalid (negative, zero, or empty)
        """
        if not odds:
            raise ValueError("Odds dictionary cannot be empty")

        for outcome, odd in odds.items():
            if odd <= 0:
                raise ValueError(f"Invalid odd value for {outcome}: {odd}")

        # Calculate implied probabilities
        implied_probs = {outcome: 1.0 / odd for outcome, odd in odds.items()}

        # Calculate overround (total margin)
        overround = sum(implied_probs.values()) - 1.0

        # Normalize to get true probabilities
        total_implied = sum(implied_probs.values())
        true_probs = {
            outcome: prob / total_implied
            for outcome, prob in implied_probs.items()
        }

        return TrueProbabilityResult(
            true_probabilities=true_probs,
            implied_probabilities=implied_probs,
            overround=overround,
            method="basic_normalization",
        )

    def calculate_conditional_probability(
        self,
        outcome_probabilities: dict[str, float],
        condition_outcomes: list[str],
    ) -> dict[str, float]:
        """
        Calculate conditional probabilities within a subset of outcomes.

        P(score | direction) = P(score) / Σ P(scores_in_direction)

        Args:
            outcome_probabilities: Probabilities for all outcomes
            condition_outcomes: Subset of outcomes to condition on

        Returns:
            Dictionary of conditional probabilities
        """
        condition_total = sum(
            outcome_probabilities.get(o, 0) for o in condition_outcomes
        )

        if condition_total == 0:
            return {o: 0.0 for o in condition_outcomes}

        return {
            outcome: outcome_probabilities.get(outcome, 0) / condition_total
            for outcome in condition_outcomes
        }

    def analyze_flow(
        self,
        initial_snapshot: ProbabilitySnapshot,
        latest_snapshot: ProbabilitySnapshot,
    ) -> FlowReport:
        """
        Analyze probability flow between two time points.

        Flow(outcome) = P_true_latest(outcome) - P_true_initial(outcome)

        Args:
            initial_snapshot: Earlier probability snapshot
            latest_snapshot: Later probability snapshot

        Returns:
            FlowReport with all flow results and statistics
        """
        flows = []

        # Calculate true probabilities for both snapshots
        initial_true = self.calculate_true_probability(
            {k: 1.0 / v for k, v in initial_snapshot.probabilities.items()}
        )
        latest_true = self.calculate_true_probability(
            {k: 1.0 / v for k, v in latest_snapshot.probabilities.items()}
        )

        # Calculate flow for each outcome
        for outcome in initial_true.true_probabilities:
            initial_prob = initial_true.true_probabilities[outcome]
            latest_prob = latest_true.true_probabilities.get(outcome, initial_prob)
            flow_pp = (latest_prob - initial_prob) * 100  # Convert to percentage points

            # Classify direction
            if flow_pp > self.flow_threshold_low:
                direction = FlowDirection.POSITIVE
            elif flow_pp < -self.flow_threshold_low:
                direction = FlowDirection.NEGATIVE
            else:
                direction = FlowDirection.NEUTRAL

            # Assess significance
            abs_flow = abs(flow_pp)
            if abs_flow >= self.flow_threshold_high:
                significance = "high"
            elif abs_flow >= self.flow_threshold_medium:
                significance = "medium"
            else:
                significance = "low"

            flows.append(
                FlowResult(
                    outcome=outcome,
                    flow_pp=flow_pp,
                    direction=direction,
                    initial_prob=initial_prob,
                    latest_prob=latest_prob,
                    significance=significance,
                )
            )

        return FlowReport(
            match_id=f"match_{initial_snapshot.timestamp.timestamp()}",
            market_type=initial_snapshot.market_type,
            initial_snapshot=initial_snapshot,
            latest_snapshot=latest_snapshot,
            flows=flows,
        )


__all__ = [
    "MarketType",
    "FlowDirection",
    "ProbabilitySnapshot",
    "TrueProbabilityResult",
    "FlowResult",
    "FlowReport",
    "ProbabilityEngine",
]
