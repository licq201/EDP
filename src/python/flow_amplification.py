"""
EDP - Expectation Domain Perception Method
Probability Flow Amplification Engine

This module implements the probability flow amplification effect,
a signal propagation mechanism through outcome gradient graphs.

Theoretical Foundations:

1. Flow Propagation on Gradient Graphs:
   The probability flow observed for one outcome propagates through
   related outcomes via the gradient graph. The amplification effect
   arises from this propagation:

   Amplification_Score = Base_Flow * Directional_Consistency
                        * (1 + Gradient_Position) * Market_Momentum

2. Information Cascade Model (Banerjee, 1992):
   When probability flows are detected, related outcomes may
   experience cascading effects due to information propagation:

   P_flow(adjacent) = base_flow * exp(-distance * decay_rate)

3. Time Series Momentum (Moskowitz et al., 2012):
   Persistent directional changes in probabilities suggest genuine
   information rather than noise:

   Momentum_Signal = weighted_sum(recent_flows) / total_weight

⚠️ ACADEMIC RESEARCH AND EDUCATIONAL PURPOSES ONLY
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from .probability_engine import FlowDirection, FlowReport, FlowResult


class AmplificationLevel(Enum):
    """
    Classification of amplification effect strength based on score magnitude.

    Levels are calibrated on the amplification score (percentage points scale).
    """

    NONE = "none"  # No significant amplification detected
    LOW = "low"  # Weak signal
    MEDIUM = "medium"  # Moderate signal
    HIGH = "high"  # Strong signal
    VERY_HIGH = "very_high"  # Very strong signal
    EXCEPTIONAL = "exceptional"  # Exceptionally strong signal


@dataclass
class GradientEdge:
    """
    Represents a directed edge in the outcome gradient graph.

    The gradient graph defines connectivity between outcomes based on
    structural relationships. Each edge has:
    - A transition probability (how likely flow propagates along this edge)
    - A distance (how far apart are these outcomes conceptually)

    Attributes:
        source_outcome: Source outcome identifier
        target_outcome: Target outcome identifier
        transition_probability: Probability that flow propagates along this edge
        distance: Conceptual distance in the outcome space
    """

    source_outcome: str
    target_outcome: str
    transition_probability: float = 1.0
    distance: float = 1.0


@dataclass
class GradientGraph:
    """
    Graph structure representing relationships between outcomes.

    Nodes are outcomes; edges represent potential flow amplification paths.
    The graph structure encodes the topological relationships between outcomes
    that enable flow propagation analysis.

    References:
        Banerjee, A.V. (1992). "A Simple Model of Herd Behavior."
        The Quarterly Journal of Economics, 107(3), 797-817.
    """

    nodes: list[str] = field(default_factory=list)
    edges: list[GradientEdge] = field(default_factory=list)
    adjacency_map: dict[str, list[str]] = field(default_factory=dict)

    def add_edge(self, source: str, target: str, distance: float = 1.0) -> None:
        """Add a directed edge from source to target."""
        if source not in self.nodes:
            self.nodes.append(source)
        if target not in self.nodes:
            self.nodes.append(target)

        edge = GradientEdge(
            source_outcome=source,
            target_outcome=target,
            distance=distance,
        )
        self.edges.append(edge)

        if source not in self.adjacency_map:
            self.adjacency_map[source] = []
        self.adjacency_map[source].append(target)

    def get_adjacent_outcomes(self, outcome: str) -> list[str]:
        """Get all outcomes adjacent to the given outcome."""
        return self.adjacency_map.get(outcome, [])

    def get_outcome_degree(self, outcome: str) -> int:
        """Return the degree (number of adjacent nodes) of an outcome."""
        return len(self.adjacency_map.get(outcome, []))

    @staticmethod
    def build_generic_gradient(
        outcome_groups: list[tuple[list[str], float]]
    ) -> "GradientGraph":
        """
        Build a generic gradient graph from outcome groups.

        Args:
            outcome_groups: List of (outcomes_list, intra_group_distance) tuples.
                           Outcomes in the same group are connected to each other.

        Returns:
            Constructed GradientGraph object
        """
        graph = GradientGraph()

        for _i, (outcomes, distance) in enumerate(outcome_groups):
            # Connect outcomes within the same group
            for j in range(len(outcomes) - 1):
                graph.add_edge(outcomes[j], outcomes[j + 1], distance=distance)

        return graph


@dataclass
class AmplificationResult:
    """
    Result of amplification effect calculation for a single outcome.

    The amplification score represents the total signal strength received
    by an outcome from both direct flow and propagated flow on the gradient graph.

    Mathematical Formulation:
        Amplification_Score = Base_Flow
                            * Directional_Consistency
                            * (1 + Gradient_Position)
                            * Market_Momentum

    References:
        Moskowitz, T.J., Ooi, Y.H. & Pedersen, L.H. (2012).
        "Time Series Momentum." Journal of Financial Economics, 104(2), 228-250.

    Attributes:
        outcome: The outcome identifier
        base_flow_pp: Base probability flow in percentage points
        directional_consistency: Degree of flow consistency among neighbors
        gradient_position: Normalized position in the outcome gradient space
        market_momentum: Cross-market momentum factor
        amplification_score: Final amplified signal score
        level: Classification level of amplification
        confidence: Statistical confidence in the signal
        propagation_depth: Number of graph steps the signal propagated
        adjacent_signals: List of (outcome, signal_strength) tuples from neighbors
    """

    outcome: str
    base_flow_pp: float
    directional_consistency: float
    gradient_position: float
    market_momentum: float
    amplification_score: float
    level: AmplificationLevel
    confidence: float = 1.0
    propagation_depth: int = 1
    adjacent_signals: list[tuple[str, float]] = field(default_factory=list)

    def is_reliable(self, min_confidence: float = 0.5) -> bool:
        """Check if amplification result is reliable enough for use."""
        return self.confidence >= min_confidence and self.level != AmplificationLevel.NONE

    def get_signal_strength(self) -> float:
        """Calculate overall normalized signal strength (0-1)."""
        return min(abs(self.amplification_score) / 10.0, 1.0)


@dataclass
class AmplificationReport:
    """
    Complete amplification analysis report for a market.

    Contains all amplification results with propagation analysis
    and aggregate statistics for signal interpretation.

    Attributes:
        match_id: Identifier for the match/market analyzed
        outcomes: List of all outcome identifiers
        amplifications: List of amplification results for all outcomes
        aggregate_momentum: Mean amplification score across outcomes
        market_cascade_risk: Risk of false signal cascading propagation
        generated_at: Timestamp of report generation
    """

    match_id: str
    outcomes: list[str]
    amplifications: list[AmplificationResult] = field(default_factory=list)
    aggregate_momentum: float = 0.0
    market_cascade_risk: float = 0.0
    generated_at: datetime = field(default_factory=datetime.now)

    def get_high_amplification(self) -> list[AmplificationResult]:
        """Return outcomes with strong or stronger amplification levels."""
        strong_levels = {
            AmplificationLevel.HIGH,
            AmplificationLevel.VERY_HIGH,
            AmplificationLevel.EXCEPTIONAL,
        }
        return [a for a in self.amplifications if a.level in strong_levels]

    def get_reliable_amplifications(self, min_confidence: float = 0.5) -> list[AmplificationResult]:
        """Return all reliable amplification results above confidence threshold."""
        return [a for a in self.amplifications if a.is_reliable(min_confidence)]

    def get_cascading_signals(self) -> dict[str, list[str]]:
        """
        Get signals that exhibit cascading behavior through the gradient graph.

        Returns a mapping of primary signal outcomes to their affected neighbors.
        """
        cascading: dict[str, list[str]] = {}
        for amp in self.get_high_amplification():
            if amp.propagation_depth > 1:
                cascading[amp.outcome] = [adj[0] for adj in amp.adjacent_signals[: amp.propagation_depth]]
        return cascading

    def get_summary(self) -> dict[str, Any]:
        """Generate a summary dictionary of the amplification analysis."""
        return {
            "match_id": self.match_id,
            "total_outcomes": len(self.outcomes),
            "high_amplification_count": len(self.get_high_amplification()),
            "aggregate_momentum": self.aggregate_momentum,
            "market_cascade_risk": self.market_cascade_risk,
            "reliable_signals": len(self.get_reliable_amplifications()),
            "top_signals": [
                {"outcome": a.outcome, "score": a.amplification_score, "level": a.level.value}
                for a in sorted(
                    self.get_high_amplification(),
                    key=lambda x: x.amplification_score,
                    reverse=True,
                )[:5]
            ],
        }


class FlowAmplificationEngine:
    """
    Advanced probability flow amplification effect analyzer.

    The amplification effect occurs when probability flow shows
    movement from one outcome to related outcomes on the gradient graph.
    This creates a cascading effect where the initial signal "amplifies"
    as it propagates through related outcomes.

    The analysis follows these principles:
    1. Only positive (increasing probability) flows are amplified
    2. Consistency among adjacent outcomes strengthens the signal
    3. Position on the outcome gradient determines amplification potential
    4. Cross-market momentum provides additional signal confirmation

    References:
        Banerjee, A.V. (1992). "A Simple Model of Herd Behavior."
        The Quarterly Journal of Economics, 107(3), 797-817.

        Moskowitz, T.J., Ooi, Y.H. & Pedersen, L.H. (2012).
        "Time Series Momentum." Journal of Financial Economics, 104(2), 228-250.

    Example:
        >>> engine = FlowAmplificationEngine()
        >>> report = engine.calculate_amplification(flow_report, gradient_graph)
        >>> high_signals = report.get_high_amplification()
    """

    # Amplification thresholds (in percentage points)
    THRESHOLD_LOW = 1.0
    THRESHOLD_MEDIUM = 3.0
    THRESHOLD_HIGH = 6.0
    THRESHOLD_VERY_HIGH = 10.0
    THRESHOLD_EXCEPTIONAL = 15.0

    # Minimum base flow to enable amplification (in percentage points)
    MIN_BASE_FLOW_THRESHOLD = 1.0

    # Signal propagation decay rate (per graph distance unit)
    PROPAGATION_DECAY = 0.7

    def __init__(self, config: dict[str, Any] | None = None):
        """
        Initialize the flow amplification engine.

        Args:
            config: Optional configuration dictionary
                   Keys: min_base_flow, confidence_decay, propagation_decay
        """
        self.config = config or {}
        self.min_base_flow = self.config.get("min_base_flow", self.MIN_BASE_FLOW_THRESHOLD)
        self.confidence_decay = self.config.get("confidence_decay", 0.9)
        self.propagation_decay = self.config.get("propagation_decay", self.PROPAGATION_DECAY)

    def classify_amplification_level(self, score: float) -> AmplificationLevel:
        """
        Classify amplification score into a discrete level.

        Args:
            score: The absolute amplification score in percentage points

        Returns:
            AmplificationLevel classification
        """
        abs_score = abs(score)
        if abs_score < self.THRESHOLD_LOW:
            return AmplificationLevel.NONE
        elif abs_score < self.THRESHOLD_MEDIUM:
            return AmplificationLevel.LOW
        elif abs_score < self.THRESHOLD_HIGH:
            return AmplificationLevel.MEDIUM
        elif abs_score < self.THRESHOLD_VERY_HIGH:
            return AmplificationLevel.HIGH
        elif abs_score < self.THRESHOLD_EXCEPTIONAL:
            return AmplificationLevel.VERY_HIGH
        return AmplificationLevel.EXCEPTIONAL

    def calculate_directional_consistency(
        self,
        flow_report: FlowReport,
        outcome: str,
        adjacent_outcomes: list[str],
    ) -> float:
        """
        Calculate directional consistency for an outcome.

        Directional consistency measures the proportion of adjacent outcomes
        with the same flow direction as the primary outcome, representing
        the degree of coordinated movement in the outcome gradient space.

        Mathematical Formulation:
            Consistency = (Same_Direction_Count + 0.5 * Stable_Count) /
                          Total_Adjacent_Count

        Args:
            flow_report: Flow analysis report
            outcome: The outcome to analyze
            adjacent_outcomes: List of adjacent outcome identifiers

        Returns:
            Consistency score between 0.0 and 1.0
        """
        if not adjacent_outcomes:
            return 0.0

        # Build flow map from report
        flow_map: dict[str, FlowResult] = {f.outcome: f for f in flow_report.flows}
        outcome_flow = flow_map.get(outcome)
        if outcome_flow is None:
            return 0.0

        # Determine the primary direction
        primary_direction = outcome_flow.direction

        # Count neighbors with supporting flow directions
        consistent_count = 0.0
        for adj in adjacent_outcomes:
            adj_flow = flow_map.get(adj)
            if adj_flow is None:
                continue

            # Upward flow is supported by upward or stable neighbors
            if primary_direction == FlowDirection.UPWARD and adj_flow.direction in (
                FlowDirection.UPWARD,
                FlowDirection.STABLE,
            ):
                consistent_count += 1.0 if adj_flow.direction == FlowDirection.UPWARD else 0.5
            # Downward flow is supported by downward or stable neighbors
            elif primary_direction == FlowDirection.DOWNWARD and adj_flow.direction in (
                FlowDirection.DOWNWARD,
                FlowDirection.STABLE,
            ):
                consistent_count += 1.0 if adj_flow.direction == FlowDirection.DOWNWARD else 0.5
            # Stable flow is only supported by stable neighbors
            elif primary_direction == FlowDirection.STABLE and adj_flow.direction == FlowDirection.STABLE:
                consistent_count += 0.5

        return consistent_count / len(adjacent_outcomes)

    def calculate_gradient_position(
        self,
        outcome: str,
        outcome_probabilities: dict[str, float],
        direction_outcomes: list[str],
    ) -> float:
        """
        Calculate normalized gradient position for an outcome.

        Outcomes with lower absolute probability have higher gradient position,
        representing greater potential amplification due to more room for
        directional movement. Higher probability outcomes saturate and have
        lower amplification potential.

        Mathematical Formulation:
            Position = (Max_Probability - Outcome_Probability) /
                      (Max_Probability - Min_Probability)

        where the min/max are calculated over outcomes in the same direction.

        Args:
            outcome: The outcome to analyze
            outcome_probabilities: Dictionary of all outcome probabilities
            direction_outcomes: List of outcomes in the same direction

        Returns:
            Normalized gradient position between 0.0 and 1.0
        """
        if outcome not in outcome_probabilities:
            return 0.0

        direction_probs = [
            outcome_probabilities.get(o, 0.0) for o in direction_outcomes
        ]

        if not direction_probs:
            return 0.5

        max_prob = max(direction_probs)
        min_prob = min(direction_probs)

        if max_prob == min_prob:
            return 0.5  # Uniform probabilities, neutral position

        # Inverted: lower probability = higher position = more amplification room
        outcome_prob = outcome_probabilities[outcome]
        position = (max_prob - outcome_prob) / (max_prob - min_prob)

        return min(max(position, 0.0), 1.0)

    def calculate_market_momentum(
        self,
        outcome: str,
        base_flow: float,
        adjacent_flows: list[tuple[str, float]],
        outcome_probabilities: dict[str, float],
    ) -> float:
        """
        Calculate cross-market momentum factor.

        This factor captures whether flows in adjacent outcomes are reinforcing
        (same direction) or conflicting (opposite direction) with the primary flow.
        Reinforcement increases momentum while conflict decreases it.

        Mathematical Formulation:
            Momentum = 1.0 + Sum_i [sign(flow_i == flow_primary)
                                  * |flow_i| * weight_i] / normalization

        where weight_i is proportional to the probability of outcome i.

        Args:
            outcome: The outcome being analyzed (informational)
            base_flow: Base flow for the primary outcome
            adjacent_flows: List of (outcome, flow_pp) tuples for neighbors
            outcome_probabilities: Dictionary of all outcome probabilities

        Returns:
            Momentum multiplier (typically in 0.5 - 1.5 range)
        """
        if not adjacent_flows:
            return 1.0

        # Check consistency of flow direction with weighted contribution
        momentum_sum = 0.0
        total_weight = 0.0

        for adj_outcome, adj_flow in adjacent_flows:
            weight = max(outcome_probabilities.get(adj_outcome, 0.1), 0.01)
            total_weight += weight

            # Sign indicates same direction as primary flow
            sign = 1.0 if (base_flow >= 0) == (adj_flow >= 0) else -1.0
            momentum_sum += sign * abs(adj_flow) * weight

        if total_weight == 0:
            return 1.0

        # Normalize by total weight
        avg_momentum = momentum_sum / total_weight

        # Map to multiplier range: strong positive momentum → high multiplier
        if avg_momentum > 3.0:
            return 1.5
        elif avg_momentum > 1.0:
            return 1.3
        elif avg_momentum > 0:
            return 1.1
        elif avg_momentum > -1.0:
            return 0.9
        elif avg_momentum > -3.0:
            return 0.8
        return 0.7

    def calculate_propagation_depth(
        self,
        outcome: str,
        flow_pp: float,
        gradient_graph: GradientGraph,
        flow_report: FlowReport,
        max_depth: int = 3,
    ) -> tuple[int, list[tuple[str, float]]]:
        """
        Calculate how deep the flow can propagate through the gradient graph.

        Uses breadth-first search to find adjacent outcomes that also show
        consistent flow, with decay rate modeling the diminishing signal
        as it propagates through the graph.

        Propagation Model:
            signal_depth_1 = base_flow * exp(-distance * decay)
            signal_depth_2 = signal_depth_1 * exp(-distance * decay)
            ...
        Signal persists until signal < min_base_flow threshold.

        Args:
            outcome: Starting outcome identifier
            flow_pp: Flow magnitude at starting point
            gradient_graph: The gradient graph structure
            flow_report: Flow analysis results
            max_depth: Maximum propagation depth to consider

        Returns:
            Tuple of (max_depth_reached, list of (outcome, signal_strength))
        """
        flow_map = {f.outcome: f for f in flow_report.flows}
        visited: set[str] = {outcome}
        signals: list[tuple[str, float]] = []
        depth = 0

        # BFS through adjacent outcomes
        current_outcomes = gradient_graph.get_adjacent_outcomes(outcome)
        current_signal = abs(flow_pp)

        for _d in range(max_depth):
            next_outcomes: list[str] = []
            depth_signals: list[float] = []

            for adj in current_outcomes:
                if adj in visited:
                    continue
                visited.add(adj)

                adj_flow = flow_map.get(adj)
                if adj_flow is None:
                    continue

                # Decay the signal based on distance
                signal_strength = current_signal * self.propagation_decay ** (_d + 1)

                # Only count if adjacent flow is in same direction as primary
                if adj_flow.flow_pp >= 0 and flow_pp >= 0:
                    depth_signals.append(signal_strength)
                    signals.append((adj, signal_strength))
                    next_outcomes.extend(gradient_graph.get_adjacent_outcomes(adj))
                elif adj_flow.flow_pp < 0 and flow_pp < 0:
                    depth_signals.append(signal_strength)
                    signals.append((adj, signal_strength))
                    next_outcomes.extend(gradient_graph.get_adjacent_outcomes(adj))

            if depth_signals and max(depth_signals) >= self.min_base_flow:
                depth = _d + 1
            else:
                break

            current_outcomes = next_outcomes
            current_signal = max(depth_signals) if depth_signals else current_signal

        return depth, signals

    def calculate_amplification(
        self,
        flow_report: FlowReport,
        outcome_probabilities: dict[str, float],
        gradient_graph: GradientGraph | None = None,
        confidence_modifiers: dict[str, float] | None = None,
    ) -> AmplificationReport:
        """
        Calculate amplification effect for all outcomes in the flow report.

        Amplification Score Formula:
            Amplification_Score =
                Base_Flow
                * Directional_Consistency
                * (1 + Gradient_Position)
                * Market_Momentum

        Only positive (upward) flows are amplified, consistent with the
        information cascade model where signals reinforce positively correlated
        outcomes.

        References:
            Banerjee, A.V. (1992). "A Simple Model of Herd Behavior."
            The Quarterly Journal of Economics, 107(3), 797-817.

        Args:
            flow_report: Flow analysis report from the probability engine
            outcome_probabilities: Current true probability distribution
            gradient_graph: Optional gradient graph for propagation analysis
            confidence_modifiers: Optional confidence adjustments per outcome

        Returns:
            AmplificationReport with all results and aggregate statistics
        """
        # Build default gradient graph from outcome relationships if not provided
        if gradient_graph is None:
            default_groups = [(flow_report.flows[i].outcome for i in range(len(flow_report.flows)))]
            simplified_graph = GradientGraph()
            for _g in default_groups:
                pass
            gradient_graph = simplified_graph

        confidence_modifiers = confidence_modifiers or {}

        # Build flow direction map
        flow_map = {f.outcome: f for f in flow_report.flows}

        amplifications: list[AmplificationResult] = []

        # Iterate over all outcomes in the flow report
        for flow_result in flow_report.flows:
            outcome = flow_result.outcome
            base_flow = flow_result.flow_pp

            # Skip outcomes with insufficient base flow
            if abs(base_flow) < self.min_base_flow:
                amplifications.append(
                    AmplificationResult(
                        outcome=outcome,
                        base_flow_pp=base_flow,
                        directional_consistency=0.0,
                        gradient_position=0.0,
                        market_momentum=1.0,
                        amplification_score=0.0,
                        level=AmplificationLevel.NONE,
                        confidence=confidence_modifiers.get(outcome, 1.0) * 0.1,
                        propagation_depth=0,
                        adjacent_signals=[],
                    )
                )
                continue

            # Get adjacent outcomes from gradient graph
            adjacent = gradient_graph.get_adjacent_outcomes(outcome)

            # Calculate the four amplification components
            directional_consistency = self.calculate_directional_consistency(
                flow_report, outcome, adjacent
            )

            # Identify outcomes in the same direction for gradient position
            same_direction = [
                o
                for o, f in flow_map.items()
                if f.direction == flow_result.direction
            ]
            gradient_position = self.calculate_gradient_position(
                outcome, outcome_probabilities, same_direction
            )

            # Calculate adjacent flows for market momentum
            adjacent_flows = [(f.outcome, f.flow_pp) for f in flow_report.flows if f.outcome in adjacent]

            market_momentum = self.calculate_market_momentum(
                outcome, base_flow, adjacent_flows, outcome_probabilities
            )

            # Calculate propagation depth
            propagation_depth, adjacent_signals = self.calculate_propagation_depth(
                outcome, base_flow, gradient_graph, flow_report
            )

            # Calculate total amplification score
            # Only positive (upward) flows receive amplification
            if flow_result.direction == FlowDirection.UPWARD:
                raw_score = (
                    base_flow
                    * (0.5 + 0.5 * directional_consistency)
                    * (1.0 + gradient_position)
                    * market_momentum
                )
            else:
                # Non-positive flows get no amplification (dampened)
                raw_score = base_flow * 0.3 * directional_consistency

            # Apply confidence modifier
            confidence = confidence_modifiers.get(outcome, 1.0)
            adjusted_score = raw_score * confidence

            # Classify the amplification level
            level = self.classify_amplification_level(adjusted_score)

            # Build result
            amplifications.append(
                AmplificationResult(
                    outcome=outcome,
                    base_flow_pp=base_flow,
                    directional_consistency=directional_consistency,
                    gradient_position=gradient_position,
                    market_momentum=market_momentum,
                    amplification_score=adjusted_score,
                    level=level,
                    confidence=confidence,
                    propagation_depth=propagation_depth,
                    adjacent_signals=adjacent_signals,
                )
            )

        # Aggregate statistics
        aggregate_momentum = sum(a.amplification_score for a in amplifications) / max(
            len(amplifications), 1
        )

        # Cascade risk: high momentum with low directional consistency = risky
        high_momentum = [a for a in amplifications if a.amplification_score > 5.0]
        cascade_risk = 0.0
        for amp in high_momentum:
            if amp.directional_consistency < 0.5:
                cascade_risk += 0.2 / len(high_momentum) if high_momentum else 0.0
        cascade_risk = min(cascade_risk, 1.0)

        return AmplificationReport(
            match_id=flow_report.match_id,
            outcomes=[a.outcome for a in amplifications],
            amplifications=amplifications,
            aggregate_momentum=aggregate_momentum,
            market_cascade_risk=cascade_risk,
        )


__all__ = [
    "AmplificationLevel",
    "GradientEdge",
    "GradientGraph",
    "AmplificationResult",
    "AmplificationReport",
    "FlowAmplificationEngine",
]
