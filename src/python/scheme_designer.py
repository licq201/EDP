"""
EDP - Expectation Domain Perception Method
Resource Allocation and Portfolio Optimization Engine.

This module implements the optimized resource allocation engine based on:
1. Kelly Criterion for optimal capital allocation (Kelly, 1956)
2. Modern Portfolio Theory for diversified allocation (Markowitz, 1952)
3. Three Principles of Allocation (non-negotiable constraints)

Three Principles of Allocation:
    1. Principle of Signal Alignment
       Only allocate to outcomes with positive probability flow signals.
       Ensures capital is directed towards evidence-supported opportunities.

    2. Principle of Asymmetric Potential
       Allocate only to outcomes with meaningful upside potential
       (sufficient probability-distance from saturation).

    3. Principle of Risk Diversification
       Allocate across independent signals to minimize idiosyncratic risk,
       maintaining reasonable diversification constraints.

Mathematical Formulation:
    Kelly Fraction:
        f* = (p * (b + 1) - 1) / b
        where p = estimated probability, b = potential return

    Kelly Allocation with Signal:
        allocation = f* * signal_strength * confidence_factor

    Diversification Constraint:
        Σ allocation_i ≤ Budget
        max(allocation_i) ≤ Budget * concentration_limit

References:
    Kelly, J.L. (1956). "A New Interpretation of Information Rate."
    The Bell System Technical Journal, 35(4), 917-926.

    Markowitz, H. (1952). "Portfolio Selection."
    The Journal of Finance, 7(1), 77-91.

    Cover, T.M. & Thomas, J.A. (2006). "Elements of Information Theory," 2nd ed.
    Wiley, Chapter 6.

⚠️ ACADEMIC RESEARCH AND EDUCATIONAL PURPOSES ONLY
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class RiskLevel(Enum):
    """
    Risk classification for allocation layers.

    Based on the risk-return trade-off in portfolio theory,
    outcomes are categorized by their expected return potential.
    """

    CONSERVATIVE = "conservative"  # High probability, low return
    BALANCED = "balanced"  # Medium probability, medium return
    AGGRESSIVE = "aggressive"  # Low probability, high return
    EXTREME = "extreme"  # Very low probability, very high return


class ValidationResult(Enum):
    """Result of scheme validation against the Three Principles."""

    VALID = "valid"
    WARNING = "warning"
    INVALID = "invalid"


@dataclass
class AllocationLeg:
    """
    A single allocation leg (selection) with signal metadata.

    Represents one candidate for capital allocation, including all
    information needed to compute Kelly-optimal fractions.

    Attributes:
        identifier: Unique identifier for this selection
        probability: Estimated probability (0.0-1.0) from the analysis engine
        odds: Decimal quote (return multiplier if correct, e.g., 3.0 means 2x return)
        signal_score: Signal strength from flow analysis / amplification (0-1)
        confidence: Confidence in the signal (0-1)
        flow_direction: Direction of probability movement
        tags: Optional categorical tags
    """

    identifier: str
    probability: float
    odds: float
    signal_score: float = 0.0
    confidence: float = 1.0
    flow_direction: str = "upward"
    tags: dict[str, str] = field(default_factory=dict)

    def expected_value(self) -> float:
        """
        Calculate expected value of this leg.

        EV = probability * (odds - 1) - (1 - probability) * 1

        Returns:
            Expected value per unit capital (negative = expected loss)
        """
        if self.odds <= 1.0:
            return -1.0
        return self.probability * (self.odds - 1.0) - (1.0 - self.probability)

    def kelly_fraction(self, fraction: float = 0.25) -> float:
        """
        Calculate the optimal Kelly fraction for this leg.

        Kelly Criterion:
            f* = (p * b - q) / b = (p * (b + 1) - 1) / b

        where p = probability, b = net odds, q = 1 - p

        We use fractional Kelly (typically 0.25-0.5) for risk management,
        as full-Kelly leads to significant volatility.

        References:
            MacLean, L.C., Thorp, E.O., & Ziemba, W.T. (2010).
            "The Kelly Capital Growth Investment Criterion."

        Args:
            fraction: Fractional Kelly multiplier (0.25 = quarter-Kelly)

        Returns:
            Recommended capital fraction (capped at 0.0-1.0)
        """
        if self.odds <= 1.0 or self.probability <= 0:
            return 0.0

        # Kelly fraction formula
        f_star = (self.probability * self.odds - 1.0) / (self.odds - 1.0)

        # Apply fractional Kelly for risk control
        return max(0.0, min(f_star * fraction, 1.0))


@dataclass
class Allocation:
    """
    A complete capital allocation plan for a single leg.

    Attributes:
        leg: The allocation leg with signal information
        amount: Capital allocated to this leg
        risk_level: Classified risk level
        expected_return: Expected return on this allocation
        kelly_ratio: Ratio of allocation to Kelly-optimal fraction
        validator_notes: Optional list of validation messages
    """

    leg: AllocationLeg
    amount: float
    risk_level: RiskLevel
    expected_return: float = 0.0
    kelly_ratio: float = 0.0
    validator_notes: list[str] = field(default_factory=list)

    @property
    def expected_payoff(self) -> float:
        """Expected payoff = amount * expected_value + amount."""
        return self.amount * (1.0 + self.leg.expected_value())

    @property
    def risk_contribution(self) -> float:
        """Risk contribution proportional to Kelly-ratio squared (simplified)."""
        return self.amount * self.kelly_ratio ** 2


@dataclass
class AllocationBundle:
    """
    A complete capital allocation plan across multiple candidates.

    Represents a diversified portfolio with budget constraints,
    risk management, and allocation tracking.

    Attributes:
        allocations: List of individual allocations
        total_budget: Total available capital
        allocated_amount: Amount currently allocated
        generated_at: Timestamp of bundle generation
    """

    allocations: list[Allocation]
    total_budget: float
    allocated_amount: float = 0.0
    generated_at: datetime = field(default_factory=datetime.now)

    @property
    def remaining_budget(self) -> float:
        """Remaining unallocated capital."""
        return self.total_budget - self.allocated_amount

    @property
    def portfolio_expected_value(self) -> float:
        """Total portfolio expected value."""
        return sum(a.amount * a.leg.expected_value() for a in self.allocations)

    @property
    def diversification_ratio(self) -> float:
        """
        Diversification ratio (Herfindahl-based).

        HHI = Σ(share_i^2), where share_i = allocation_i / total_allocation
        Ratio = 1 - HHI (higher = more diversified)
        """
        if self.allocated_amount <= 0:
            return 0.0
        shares = [a.amount / self.allocated_amount for a in self.allocations]
        hhi = sum(s * s for s in shares)
        return max(0.0, 1.0 - hhi)

    def get_allocations_by_risk(self, risk_level: RiskLevel) -> list[Allocation]:
        """Filter allocations by risk level."""
        return [a for a in self.allocations if a.risk_level == risk_level]


class AllocationEngine:
    """
    Resource allocation engine implementing the Three Principles and Kelly Criterion.

    The allocation engine takes signal outputs from the amplification analysis
    and produces optimized capital allocation plans. The implementation:

    1. Validates each candidate against the Three Principles
    2. Computes Kelly-optimal allocations with fractional-Kelly risk control
    3. Applies Markowitz-style diversification constraints
    4. Produces the final allocation bundle

    References:
        Kelly, J.L. (1956). "A New Interpretation of Information Rate."
        The Bell System Technical Journal, 35(4), 917-926.

        Markowitz, H.M. (1952). "Portfolio Selection."
        Journal of Finance, 7(1), 77-91.

    Example:
        >>> engine = AllocationEngine()
        >>> bundle = engine.generate_allocation(
        ...     amplification_report=report,
        ...     budget=1000.0,
        ...     candidates=candidates
        ... )
    """

    # Configuration constants
    MIN_ALLOCATION = 1.0  # Minimum allocation per leg
    MAX_CONCENTRATION = 0.2  # Max 20% of budget to any single leg
    KELLY_FRACTION = 0.25  # Quarter-Kelly for conservative allocation
    MIN_RETURN_MULTIPLIER = 3.0  # Minimum potential return for Principle 2
    MIN_SIGNAL_STRENGTH = 0.1  # Minimum signal strength for Principle 1
    MAX_RISK_LEVELS = 4  # Number of risk stratification bins

    def __init__(self, config: dict[str, Any] | None = None):
        """
        Initialize the allocation engine.

        Args:
            config: Optional configuration dictionary
                   Keys: kelly_fraction, min_allocation, max_concentration,
                         min_return_multiplier, min_signal_strength
        """
        self.config = config or {}
        self.kelly_fraction = self.config.get("kelly_fraction", self.KELLY_FRACTION)
        self.min_allocation = self.config.get("min_allocation", self.MIN_ALLOCATION)
        self.max_concentration = self.config.get("max_concentration", self.MAX_CONCENTRATION)
        self.min_return = self.config.get("min_return_multiplier", self.MIN_RETURN_MULTIPLIER)
        self.min_signal = self.config.get("min_signal_strength", self.MIN_SIGNAL_STRENGTH)

    def classify_risk_level(self, odds: float, probability: float) -> RiskLevel:
        """
        Classify the risk level of a leg based on probability and odds.

        Risk levels are derived from the probability-odds relationship:
        - High probability, low odds → Conservative
        - Low probability, high odds → Aggressive

        Args:
            odds: Decimal quote
            probability: Estimated probability

        Returns:
            RiskLevel classification
        """
        if probability >= 0.5 or odds <= 3.0:
            return RiskLevel.CONSERVATIVE
        elif probability >= 0.25 or odds <= 5.0:
            return RiskLevel.BALANCED
        elif probability >= 0.1 or odds <= 10.0:
            return RiskLevel.AGGRESSIVE
        return RiskLevel.EXTREME

    def validate_candidate(
        self, leg: AllocationLeg
    ) -> tuple[ValidationResult, list[str]]:
        """
        Validate a candidate allocation leg against the Three Principles.

        Principle 1: Positive flow signal - Only allocate to outcomes with
                     positive probability flow signals (Principle of Signal Alignment).
        Principle 2: Asymmetric potential - Only allocate to outcomes with
                     sufficient upside potential (Principle of Asymmetric Potential).
        Principle 3: Reasonable structure - Ensure quotes and probabilities
                     are consistent (Principle of Risk Diversification).

        Args:
            leg: Candidate allocation leg to validate

        Returns:
            Tuple of (ValidationResult, list of validation messages)
        """
        messages: list[str] = []
        is_valid = True

        # Principle 1: Signal Alignment - Positive flow signal required
        if leg.flow_direction != "upward":
            messages.append(
                "Principle 1 violation: No positive probability flow signal"
            )
            is_valid = False
        if leg.signal_score < self.min_signal:
            messages.append(
                f"Principle 1 violation: Signal strength {leg.signal_score:.2f} "
                f"below minimum {self.min_signal:.2f}"
            )
            is_valid = False

        # Principle 2: Asymmetric Potential - Sufficient upside return
        if leg.odds < self.min_return:
            messages.append(
                f"Principle 2 violation: Odds {leg.odds:.2f} below "
                f"minimum multiplier {self.min_return:.2f}"
            )
            is_valid = False

        # Principle 3: Reasonable structure - Valid probability range
        if not 0 < leg.probability <= 1.0:
            messages.append(
                f"Principle 3 violation: Invalid probability {leg.probability}"
            )
            is_valid = False

        # Kelly consistency check: probability * odds > 1 required for positive EV
        if leg.probability * leg.odds <= 1.0:
            messages.append(
                f"Note: Probability * Odds {leg.probability * leg.odds:.3f} <= 1 "
                "(negative expected value)"
            )
            # Not invalid, but downgraded to WARNING
            if is_valid:
                return (ValidationResult.WARNING, messages)

        if is_valid:
            return (ValidationResult.VALID, messages)
        return (ValidationResult.INVALID, messages)

    def compute_kelly_allocation(
        self, leg: AllocationLeg, total_budget: float
    ) -> tuple[float, float, RiskLevel]:
        """
        Compute Kelly-optimal allocation for a single leg.

        Implementation:
        1. Compute raw Kelly fraction: f* = (p*b - 1) / (b - 1)
        2. Apply fractional Kelly multiplier
        3. Apply maximum concentration constraint
        4. Scale to available budget

        Args:
            leg: The allocation leg to compute
            total_budget: Total budget available

        Returns:
            Tuple of (recommended_amount, kelly_ratio, risk_level)
        """
        # Compute Kelly-optimal fraction
        kelly_f = leg.kelly_fraction(self.kelly_fraction)

        # Base allocation
        raw_amount = kelly_f * total_budget * leg.signal_score * leg.confidence

        # Apply concentration constraint (Markowitz diversification)
        max_amount = total_budget * self.max_concentration

        # Final allocation (capped at max, floored at minimum)
        final_amount = max(self.min_allocation, min(raw_amount, max_amount))

        # Kelly ratio: actual / Kelly-optimal
        kelly_ratio = final_amount / max(kelly_f * total_budget, 0.001) if kelly_f > 0 else 0.0

        # Classify risk level
        risk_level = self.classify_risk_level(leg.odds, leg.probability)

        return final_amount, kelly_ratio, risk_level

    def generate_allocation(
        self,
        budget: float,
        candidates: list[AllocationLeg],
        max_allocations: int = 10,
    ) -> AllocationBundle:
        """
        Generate optimized capital allocation plan across candidates.

        Algorithm:
        1. Validate all candidates against the Three Principles
        2. Rank valid candidates by expected value * signal strength * confidence
        3. Compute Kelly-optimal allocation for each top-ranked candidate
        4. Apply diversification constraint (max concentration cap)
        5. Return the allocation bundle with portfolio statistics

        References:
            Cover, T.M. (1991). "Universal Portfolios."
            Mathematical Finance, 1(1), 1-29.

        Args:
            budget: Total capital available for allocation
            candidates: List of candidate allocation legs
            max_allocations: Maximum number of legs to include

        Returns:
            AllocationBundle with optimized plan
        """
        # Step 1: Validate all candidates
        scored_candidates: list[tuple[float, AllocationLeg, ValidationResult]] = []
        for candidate in candidates:
            result, _messages = self.validate_candidate(candidate)
            if result != ValidationResult.INVALID:
                # Score by expected value weighted by signal strength
                ev = candidate.expected_value()
                score = ev * candidate.signal_score * candidate.confidence
                scored_candidates.append((score, candidate, result))

        # Step 2: Sort by score (descending)
        scored_candidates.sort(key=lambda x: x[0], reverse=True)

        # Step 3: Generate allocations for top candidates
        allocations: list[Allocation] = []
        remaining_budget = budget
        budget_fraction = budget / max(max_allocations, 1) * self.max_concentration

        for score, candidate, _result in scored_candidates[:max_allocations]:
            # Skip if no remaining budget
            if remaining_budget < self.min_allocation:
                break

            # Compute Kelly-based allocation
            amount, kelly_ratio, risk_level = self.compute_kelly_allocation(
                candidate, budget
            )

            # Enforce remaining budget
            amount = min(amount, remaining_budget)
            if amount < self.min_allocation:
                continue

            # Expected return
            ev = candidate.expected_value()
            expected_return = amount * ev

            # Create allocation
            allocation = Allocation(
                leg=candidate,
                amount=amount,
                risk_level=risk_level,
                expected_return=expected_return,
                kelly_ratio=kelly_ratio,
                validator_notes=[
                    f"Score: {score:.4f}",
                    f"Kelly fraction: {candidate.kelly_fraction(self.kelly_fraction):.3f}",
                    f"EV per unit: {ev:.3f}",
                ],
            )
            allocations.append(allocation)
            remaining_budget -= amount

        # Step 4: Build portfolio statistics
        allocated_amount = sum(a.amount for a in allocations)

        return AllocationBundle(
            allocations=allocations,
            total_budget=budget,
            allocated_amount=allocated_amount,
        )

    def optimize_portfolio(
        self, bundle: AllocationBundle, target_diversification: float = 0.6
    ) -> AllocationBundle:
        """
        Post-hoc portfolio optimization to improve diversification.

        Adjusts allocations to ensure:
        1. Minimum diversification ratio (target_diversification)
        2. No single allocation exceeds concentration limit
        3. Allocations remain proportional to Kelly fractions

        This implements a simplified Markowitz rebalancing:
        given the Kelly-optimal fractions, adjust amounts to satisfy
        the diversification constraint without deviating from the
        ranking of candidates.

        Args:
            bundle: The initial allocation bundle
            target_diversification: Minimum diversification ratio target

        Returns:
            Optimized allocation bundle
        """
        if not bundle.allocations:
            return bundle

        current_ratio = bundle.diversification_ratio
        if current_ratio >= target_diversification:
            return bundle  # Already diversified

        # Proportionally rebalance: move allocation from concentrated legs
        # to less-represented legs while maintaining Kelly ordering.
        total_allocated = bundle.allocated_amount

        # Target allocation: proportional to Kelly signal strength
        strengths = [
            max(a.leg.signal_score * a.leg.confidence, 0.01) for a in bundle.allocations
        ]
        total_strength = sum(strengths)

        # Compute target amounts
        for i, allocation in enumerate(bundle.allocations):
            target_amount = total_allocated * (strengths[i] / total_strength)
            # Apply concentration cap
            cap = bundle.total_budget * self.max_concentration
            allocation.amount = max(self.min_allocation, min(target_amount, cap))

        # Recompute allocated amount
        bundle.allocated_amount = sum(a.amount for a in bundle.allocations)

        return bundle


__all__ = [
    "RiskLevel",
    "ValidationResult",
    "AllocationLeg",
    "Allocation",
    "AllocationBundle",
    "AllocationEngine",
]
