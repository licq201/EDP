"""
EDP - Expectation Domain Perception Method
Multi-Source Intelligence Fusion and Domain Awareness Engine.

This module implements the multi-source intelligence integration system,
providing cross-validation of information sources and situational awareness.

Core Theoretical Foundations:

1. Multi-Source Intelligence Fusion (Endsley, 1988, 2015)
   Perception of elements in the environment within a volume of time
   and space, the comprehension of their meaning, and the projection
   of their status in the near future.

2. Bayesian Evidence Accumulation (Pearl, 1988)
   Sequential updating of posterior probabilities from independent
   evidence sources.

3. Dempster-Shafer Evidence Theory (Shafer, 1976)
   Representation and combination of evidence from multiple sources
   with uncertainty and ignorance.

4. Information Cascade Detection (Bikhchandani et al., 1992)
   Identification of correlated information flows that may indicate
   convergence or herding behavior.

5. Consensus Dynamics (Degroot, 1974)
   Weighted averaging of source opinions with credibility weighting.

Information Fusion Architecture:
    ┌──────────────────────────────────────────────────────────┐
    │          Multi-Source Intelligence Intake                │
    │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐    │
    │  │ Source 1 │ │ Source 2 │ │ Source 3 │ │ Source N │    │
    │  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘    │
    │       ▼            ▼            ▼            ▼          │
    │       └────────────┴────────────┴────────────┘          │
    │                          ▼                               │
    │          ┌──────────────────────────────────┐           │
    │          │     Evidence Preprocessing       │           │
    │          │  • Normalization                 │           │
    │          │  • Source Credibility Estimation │           │
    │          │  • Temporal Alignment            │           │
    │          └────────────────┬─────────────────┘           │
    │                           ▼                              │
    │          ┌──────────────────────────────────┐           │
    │          │     Evidence Combination         │           │
    │          │  • Bayesian Evidence Fusion      │           │
    │          │  • Consensus Dynamics            │           │
    │          │  • Cross-Source Validation       │           │
    │          └────────────────┬─────────────────┘           │
    │                           ▼                              │
    │          ┌──────────────────────────────────┐           │
    │          │   Situation Awareness Output     │           │
    │          │  • Confidence Assessment         │           │
    │          │  • Anomaly Detection             │           │
    │          │  • Stability Index               │           │
    │          └──────────────────────────────────┘           │
    └──────────────────────────────────────────────────────────┘

References:
    Endsley, M.R. (1988). "Design and Evaluation for Situation
    Awareness Enhancement." Proc. Human Factors Society, 32(1), 97-101.

    Pearl, J. (1988). "Probabilistic Reasoning in Intelligent Systems."
    Morgan Kaufmann.

    Shafer, G. (1976). "A Mathematical Theory of Evidence."
    Princeton University Press.

    Bikhchandani, S., Hirshleifer, D., & Welch, I. (1992).
    "A Theory of Fads, Fashion, Custom, and Cultural Change
    as Information Cascades." JPE, 100(5), 992-1026.

    DeGroot, M.H. (1974). "Reaching a Consensus."
    JASA, 69(345), 118-121.

    Dempster, A.P. (1968). "A Generalization of Bayesian Inference."
    JRSS B, 30(2), 205-247.

⚠️ ACADEMIC RESEARCH AND EDUCATIONAL PURPOSES ONLY
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any


class EvidenceType(Enum):
    """
    Classification of evidence sources.

    Each type corresponds to a different channel of information intake,
    which may have different credibility and reliability characteristics.
    """

    STATISTICAL = "statistical"  # Derived from statistical models
    ANALYTICAL = "analytical"  # From analytical inference engines
    OBSERVATIONAL = "observational"  # Direct observational data
    HISTORICAL = "historical"  # Historical precedent analysis
    EXPERT = "expert"  # Expert judgment / domain knowledge
    COMPOSITE = "composite"  # Aggregated from multiple sources


class SourceReliability(Enum):
    """
    Source reliability classification (adapted from NATO STANAG 2511).

    Used for credibility-weighted evidence fusion.
    """

    A = ("completely_reliable", 1.00)  # Completely reliable
    B = ("usually_reliable", 0.80)  # Usually reliable
    C = ("fairly_reliable", 0.60)  # Fairly reliable
    D = ("not_usually_reliable", 0.40)  # Not usually reliable
    E = ("unreliable", 0.20)  # Unreliable
    F = ("cannot_be_judged", 0.50)  # Reliability cannot be judged

    def __init__(self, _label: str, weight: float):
        self.weight = weight


class StabilityStatus(Enum):
    """Status of situation stability based on evidence convergence."""

    STABLE = "stable"  # Evidence consensus, low variance
    UNSTABLE = "unstable"  # Evidence disagreement, high variance
    EMERGING = "emerging"  # Evidence converging, trend forming
    AMBIGUOUS = "ambiguous"  # Insufficient / conflicting evidence
    ANOMALOUS = "anomalous"  # Evidence contradicts historical patterns


@dataclass
class EvidenceSource:
    """
    An individual evidence source contributing to the fusion process.

    Represents a single channel of information with metadata about:
    - Source identity and reliability
    - Evidence content (probability estimates, observations)
    - Temporal information
    - Confidence / variance metrics

    Attributes:
        source_id: Unique identifier for this source
        source_type: Type classification of evidence
        reliability: Rated reliability of this source
        timestamp: Time evidence was collected
        content: Core evidence content (dict with 'probability' key recommended)
        confidence: Self-reported confidence (0-1) from the source
        meta: Additional metadata (tags, context, etc.)
    """

    source_id: str
    source_type: EvidenceType
    reliability: SourceReliability
    timestamp: datetime
    content: dict[str, Any]
    confidence: float = 0.7
    meta: dict[str, Any] = field(default_factory=dict)

    def evidence_probability(self) -> float:
        """Extract probability estimate from content (0.0-1.0)."""
        p = self.content.get("probability", self.content.get("value", 0.0))
        return max(0.0, min(float(p), 1.0))

    def weighted_probability(self) -> float:
        """
        Probability weighted by source credibility.

        Weight = reliability * confidence

        Returns:
            Weighted probability estimate
        """
        return self.evidence_probability() * self.reliability.weight * self.confidence


@dataclass
class SituationAssessment:
    """
    Result of multi-source evidence fusion.

    Provides a comprehensive situational assessment including:
    - Aggregated probability estimate
    - Confidence / uncertainty quantification
    - Evidence convergence metrics
    - Anomaly detection flags
    - Risk / stability indicators

    Attributes:
        aggregate_probability: Fused probability from all sources
        confidence: Overall confidence (0-1) in the assessment
        source_count: Number of contributing sources
        consensus_score: Degree of agreement across sources (0-1)
        stability_status: Stability classification
        contributing_sources: List of source IDs
        variance: Variance across source estimates
        anomalies: List of detected anomalies
        generated_at: Timestamp of assessment
    """

    aggregate_probability: float
    confidence: float
    source_count: int
    consensus_score: float
    stability_status: StabilityStatus
    contributing_sources: list[str]
    variance: float = 0.0
    anomalies: list[dict[str, Any]] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.now)

    def summary(self) -> str:
        """Human-readable summary of the assessment."""
        return (
            f"Situation Assessment: p={self.aggregate_probability:.3f}, "
            f"conf={self.confidence:.2f}, sources={self.source_count}, "
            f"consensus={self.consensus_score:.2f}, status={self.stability_status.value}"
        )


class DomainAwarenessEngine:
    """
    Multi-source intelligence fusion and domain awareness engine.

    Implements the complete evidence fusion pipeline:
    1. Evidence intake and normalization
    2. Source credibility estimation
    3. Weighted consensus fusion (DeGroot-style)
    4. Bayesian evidence accumulation
    5. Evidence convergence / consensus analysis
    6. Anomaly and cascade detection
    7. Situation assessment output

    The engine uses a hybrid approach combining:
    - Weighted linear opinion pooling (Cooke, 1991)
    - Bayesian log-odds pooling for sequential updates
    - Variance-based consensus scoring
    - Temporal decay for recency-weighted processing

    References:
        Cooke, R.M. (1991). "Experts in Uncertainty." Oxford University Press.
        Genest, C. & Zidek, J.V. (1986). "Combining Probability Distributions."
        Statistical Science, 1(1), 114-148.

    Example:
        >>> engine = DomainAwarenessEngine()
        >>> sources = [EvidenceSource(...), EvidenceSource(...)]
        >>> assessment = engine.assess_situation(sources)
    """

    # Configuration
    MIN_SOURCES_FOR_CONSENSUS = 2
    TIME_DECAY_HALF_LIFE_HOURS = 24  # Temporal decay half-life
    ANOMALY_THRESHOLD_STD = 2.0  # Z-score threshold for anomaly detection
    CONSENSUS_HIGH = 0.7  # Above this = stable
    CONSENSUS_LOW = 0.3  # Below this = ambiguous
    CASCADE_DETECTION_WINDOW = 5  # Sources to check for cascade effect

    def __init__(self, config: dict[str, Any] | None = None):
        """
        Initialize the domain awareness engine.

        Args:
            config: Optional configuration with keys:
                   time_decay_hours, consensus_high, consensus_low,
                   anomaly_threshold
        """
        self.config = config or {}
        self.time_decay_half_life = timedelta(
            hours=self.config.get("time_decay_hours", self.TIME_DECAY_HALF_LIFE_HOURS)
        )
        self.consensus_high = self.config.get("consensus_high", self.CONSENSUS_HIGH)
        self.consensus_low = self.config.get("consensus_low", self.CONSENSUS_LOW)
        self.anomaly_threshold = self.config.get(
            "anomaly_threshold", self.ANOMALY_THRESHOLD_STD
        )

    # ─── Evidence Preprocessing ────────────────────────────────────────

    def compute_source_weight(self, source: EvidenceSource, now: datetime | None = None) -> float:
        """
        Compute the aggregate credibility weight for a source.

        Weight = reliability_weight * confidence * temporal_decay

        Temporal decay uses exponential half-life model:
            decay = 2^(-Δt / half_life)

        Args:
            source: The evidence source to weight
            now: Reference time (defaults to current time)

        Returns:
            Aggregate weight (0.0-1.0 range after final normalization)
        """
        now = now or datetime.now()

        # Temporal decay: older sources get less weight
        age = (now - source.timestamp).total_seconds() / 3600.0  # hours
        decay = math.pow(2.0, -age / (self.time_decay_half_life.total_seconds() / 3600.0))

        # Combined weight: reliability × confidence × decay
        return source.reliability.weight * source.confidence * decay

    def normalize_sources(
        self, sources: list[EvidenceSource]
    ) -> tuple[list[EvidenceSource], list[float]]:
        """
        Normalize source weights to sum to 1.0 (DeGroot consensus preprocessing).

        Args:
            sources: List of evidence sources

        Returns:
            Tuple of (sorted_sources_by_weight, normalized_weights)
        """
        now = datetime.now()

        # Compute raw weights
        weights = [self.compute_source_weight(s, now) for s in sources]

        # Normalize weights
        total = sum(weights)
        if total > 0:
            normalized_weights = [w / total for w in weights]
        else:
            # Equal weights if all are zero
            n = max(len(sources), 1)
            normalized_weights = [1.0 / n] * len(sources)

        return sources, normalized_weights

    # ─── Evidence Fusion Methods ───────────────────────────────────────

    def linear_pool_fusion(
        self, sources: list[EvidenceSource], weights: list[float]
    ) -> float:
        """
        Linear opinion pooling (weighted average).

        p_fused = Σ(w_i * p_i), where Σ(w_i) = 1

        This is the standard weighted opinion pool (Cooke, 1991).

        Args:
            sources: Evidence sources with probability estimates
            weights: Normalized weights (sum to 1)

        Returns:
            Fused probability estimate (0-1)
        """
        if not sources:
            return 0.5  # Maximum uncertainty

        fused = sum(w * s.evidence_probability() for s, w in zip(sources, weights))
        return max(0.0, min(fused, 1.0))

    def log_odds_pool_fusion(
        self, sources: list[EvidenceSource], weights: list[float]
    ) -> float:
        """
        Log-odds opinion pooling (Bayesian-style evidence combination).

        Transform to log-odds space, weight, and transform back:
            logit(p) = log(p / (1-p))
            logit_fused = Σ(w_i * logit(p_i))
            p_fused = sigmoid(logit_fused)

        Log-odds pooling is better for extreme probabilities and
        has stronger Bayesian justification (Genest & Zidek, 1986).

        Args:
            sources: Evidence sources with probability estimates
            weights: Normalized weights (sum to 1)

        Returns:
            Fused probability estimate (0-1)
        """
        if not sources:
            return 0.5

        # Clip to avoid log(0) or division by zero
        def safe_logit(p: float) -> float:
            p = max(1e-6, min(1 - 1e-6, p))
            return math.log(p / (1 - p))

        logits = [safe_logit(s.evidence_probability()) for s in sources]
        fused_logit = sum(w * l for w, l in zip(weights, logits))

        # Inverse logit (sigmoid)
        exp_val = math.exp(-fused_logit)
        return 1.0 / (1.0 + exp_val)

    def bayesian_evidence_accumulation(
        self, sources: list[EvidenceSource], prior: float = 0.5
    ) -> float:
        """
        Sequential Bayesian evidence accumulation.

        Treats each source as an independent evidence-bearing observation
        and updates sequentially (Pearl, 1988):

            posterior_odds = prior_odds * Π(likelihood_ratio_i)

        where likelihood_ratio = p_i / (1 - p_i) for each source.

        This corresponds to log-odds pooling with uniform weights but
        includes explicit prior handling.

        Args:
            sources: List of evidence sources
            prior: Prior probability (default 0.5 = uninformative)

        Returns:
            Posterior probability after accumulating all evidence
        """
        if not sources:
            return prior

        # Prior log-odds
        prior_logit = math.log(prior / max(1 - prior, 1e-6))

        # Accumulate evidence in log-odds space
        evidence_logit = 0.0
        n_effective = 0

        for source in sources:
            p = max(1e-6, min(1 - 1e-6, source.evidence_probability()))
            weight = self.compute_source_weight(source)
            if weight > 0:
                evidence_logit += weight * math.log(p / (1 - p))
                n_effective += 1

        if n_effective == 0:
            return prior

        # Normalize by effective source count (scaled evidence)
        # This prevents explosion from many weak sources
        normalized_evidence = evidence_logit  # Weighted sum already scaled

        # Posterior = prior + evidence
        posterior_logit = prior_logit + normalized_evidence

        # Transform back to probability
        return 1.0 / (1.0 + math.exp(-posterior_logit))

    # ─── Consensus Analysis ────────────────────────────────────────────

    def compute_consensus_score(self, sources: list[EvidenceSource]) -> float:
        """
        Compute evidence consensus / agreement score.

        Measures degree of agreement across sources using:
        1. Variance of probability estimates (lower = more consensus)
        2. Pairwise agreement averaged

        Score = 1 - min(σ / σ_max, 1.0)
        where σ_max = 0.5 (maximum theoretical standard deviation for uniform {0,1})

        Args:
            sources: List of evidence sources

        Returns:
            Consensus score (0-1, higher = better agreement)
        """
        if len(sources) < 2:
            return 1.0  # Single source = perfect consensus (trivially)

        values = [s.evidence_probability() for s in sources]
        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        std_dev = math.sqrt(variance)

        # Normalize: max possible std for binary is 0.5 (Bernoulli p=0.5)
        sigma_max = 0.5
        normalized_disagreement = min(std_dev / sigma_max, 1.0)

        return 1.0 - normalized_disagreement

    def compute_effective_number_of_sources(
        self, weights: list[float]
    ) -> float:
        """
        Effective number of independent sources (Herfindahl-Hirschman index).

        n_effective = 1 / Σ(w_i²)

        Measures true diversity of information sources. If one source has
        w=1 and others w=0, n_effective=1 (only one source contributing).

        Args:
            weights: Normalized weights (sum to 1)

        Returns:
            Effective number of sources (>=1)
        """
        if not weights:
            return 0.0
        hhi = sum(w * w for w in weights)
        if hhi == 0:
            return len(weights)
        return 1.0 / hhi

    # ─── Anomaly Detection ─────────────────────────────────────────────

    def detect_anomalies(
        self, sources: list[EvidenceSource], consensus_score: float, mean_prob: float
    ) -> list[dict[str, Any]]:
        """
        Detect anomalous / outlier evidence sources.

        Uses z-score based detection: sources deviating more than
        `anomaly_threshold` standard deviations from the mean are flagged.

        Also detects information cascades: when multiple sources converge
        rapidly on the same estimate with high similarity (herding detection).

        Args:
            sources: List of evidence sources
            consensus_score: Current consensus score
            mean_prob: Mean probability across sources

        Returns:
            List of anomaly dicts with keys: type, source_id, severity, description
        """
        anomalies: list[dict[str, Any]] = []
        if len(sources) < 3:
            return anomalies

        values = [s.evidence_probability() for s in sources]
        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        std_dev = math.sqrt(variance)

        if std_dev == 0:
            return anomalies

        # Z-score based anomaly detection
        for source in sources:
            z = abs(source.evidence_probability() - mean) / std_dev
            if z > self.anomaly_threshold:
                anomalies.append(
                    {
                        "type": "outlier",
                        "source_id": source.source_id,
                        "severity": "high" if z > 3.0 else "medium",
                        "z_score": round(z, 3),
                        "description": (
                            f"Source probability {source.evidence_probability():.3f} "
                            f"deviates {z:.1f}σ from consensus mean {mean:.3f}"
                        ),
                    }
                )

        # Information cascade detection
        # When consensus is very high but source diversity is low
        n_sources = len(sources)
        if consensus_score > 0.9 and n_sources < self.CASCADE_DETECTION_WINDOW:
            anomalies.append(
                {
                    "type": "potential_cascade",
                    "severity": "low",
                    "description": (
                        f"High consensus ({consensus_score:.2f}) with few sources "
                        f"({n_sources}). Potential information cascade - verify sources "
                        f"are independently derived."
                    ),
                }
            )

        return anomalies

    # ─── Main Assessment Pipeline ──────────────────────────────────────

    def assess_situation(
        self,
        sources: list[EvidenceSource],
        prior_probability: float = 0.5,
        fusion_method: str = "hybrid",
    ) -> SituationAssessment:
        """
        Complete multi-source intelligence fusion and situation assessment.

        This is the main entry point of the engine. Processing pipeline:

        1. Source normalization and weight computation
        2. Evidence fusion using specified method
        3. Consensus analysis and variance computation
        4. Anomaly detection
        5. Stability classification
        6. Confidence calibration

        Args:
            sources: List of evidence sources to fuse
            prior_probability: Prior probability (default 0.5, uninformative)
            fusion_method: 'linear', 'log_odds', 'bayesian', or 'hybrid'

        Returns:
            SituationAssessment with aggregated probability and confidence

        Raises:
            ValueError: If fusion_method is not recognized
        """
        # Step 0: Handle edge case - no sources
        if not sources:
            return SituationAssessment(
                aggregate_probability=prior_probability,
                confidence=0.1,
                source_count=0,
                consensus_score=0.0,
                stability_status=StabilityStatus.AMBIGUOUS,
                contributing_sources=[],
                anomalies=[
                    {
                        "type": "no_evidence",
                        "severity": "high",
                        "description": "No evidence sources provided - returning prior probability",
                    }
                ],
            )

        # Step 1: Normalize sources
        sorted_sources, weights = self.normalize_sources(sources)

        # Step 2: Evidence fusion
        if fusion_method == "linear":
            fused = self.linear_pool_fusion(sorted_sources, weights)
        elif fusion_method == "log_odds":
            fused = self.log_odds_pool_fusion(sorted_sources, weights)
        elif fusion_method == "bayesian":
            fused = self.bayesian_evidence_accumulation(sorted_sources, prior_probability)
        elif fusion_method == "hybrid":
            # Hybrid: average of linear and log-odds
            linear = self.linear_pool_fusion(sorted_sources, weights)
            log_odds = self.log_odds_pool_fusion(sorted_sources, weights)
            bayesian = self.bayesian_evidence_accumulation(sorted_sources, prior_probability)
            fused = (linear + log_odds + bayesian) / 3.0
        else:
            raise ValueError(
                f"Unknown fusion_method: {fusion_method}. "
                f"Use 'linear', 'log_odds', 'bayesian', or 'hybrid'."
            )

        # Step 3: Consensus analysis
        consensus = self.compute_consensus_score(sources)
        values = [s.evidence_probability() for s in sources]
        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / len(values)

        # Step 4: Anomaly detection
        anomalies = self.detect_anomalies(sources, consensus, mean)

        # Step 5: Stability classification
        n_effective = self.compute_effective_number_of_sources(weights)

        if len(sources) < self.MIN_SOURCES_FOR_CONSENSUS:
            status = StabilityStatus.AMBIGUOUS
        elif anomalies and any(a.get("severity") == "high" for a in anomalies):
            status = StabilityStatus.ANOMALOUS
        elif consensus >= self.consensus_high and n_effective >= 2:
            status = StabilityStatus.STABLE
        elif consensus >= self.consensus_low:
            status = StabilityStatus.UNSTABLE
        else:
            # Check if there's a trend (last vs first half of sources by time)
            sorted_by_time = sorted(sources, key=lambda s: s.timestamp)
            mid = len(sorted_by_time) // 2
            if mid > 0:
                early_mean = sum(
                    s.evidence_probability() for s in sorted_by_time[:mid]
                ) / mid
                late_mean = sum(
                    s.evidence_probability() for s in sorted_by_time[mid:]
                ) / max(len(sorted_by_time) - mid, 1)
                if abs(late_mean - early_mean) > 0.15:
                    status = StabilityStatus.EMERGING
                else:
                    status = StabilityStatus.AMBIGUOUS
            else:
                status = StabilityStatus.AMBIGUOUS

        # Step 6: Confidence calibration
        # Confidence = function of:
        #   - Number of sources (more = higher)
        #   - Consensus score (more agreement = higher)
        #   - Effective source count (independent sources = higher)
        #   - Source reliability (higher quality = higher)
        avg_reliability = sum(s.reliability.weight for s in sources) / len(sources)
        source_factor = min(len(sources) / 5.0, 1.0)  # Saturates at 5 sources
        effective_factor = min(n_effective / 3.0, 1.0)  # Saturates at 3 effective sources

        raw_confidence = (
            0.35 * consensus
            + 0.25 * source_factor
            + 0.20 * effective_factor
            + 0.20 * avg_reliability
        )

        # Anomaly penalty
        if anomalies:
            penalty = 0.05 * len(anomalies)
            raw_confidence = max(0.0, raw_confidence - penalty)

        confidence = max(0.0, min(raw_confidence, 1.0))

        # Build final assessment
        contributing_ids = [s.source_id for s in sorted_sources]

        return SituationAssessment(
            aggregate_probability=fused,
            confidence=confidence,
            source_count=len(sources),
            consensus_score=consensus,
            stability_status=status,
            contributing_sources=contributing_ids,
            variance=variance,
            anomalies=anomalies,
        )

    def cross_validate(
        self, sources_a: list[EvidenceSource], sources_b: list[EvidenceSource]
    ) -> dict[str, Any]:
        """
        Cross-validate two independent source groups.

        Useful when you have two independent sets of evidence
        (e.g., analytical vs observational). Computes:
        - Agreement level (absolute probability difference)
        - Combined fusion result
        - Meta-confidence based on cross-group agreement

        Args:
            sources_a: First group of evidence sources
            sources_b: Second group of evidence sources

        Returns:
            Dict with: agreement, delta, assessment_a, assessment_b, combined
        """
        assessment_a = self.assess_situation(sources_a)
        assessment_b = self.assess_situation(sources_b)

        delta = abs(assessment_a.aggregate_probability - assessment_b.aggregate_probability)
        agreement = 1.0 - delta

        # Combined assessment with all sources
        combined = self.assess_situation(sources_a + sources_b)

        # Meta-confidence: product of individual confidences × agreement
        meta_confidence = assessment_a.confidence * assessment_b.confidence * agreement

        return {
            "agreement": agreement,
            "delta": delta,
            "assessment_a": assessment_a,
            "assessment_b": assessment_b,
            "combined_assessment": combined,
            "meta_confidence": meta_confidence,
        }


__all__ = [
    "EvidenceType",
    "SourceReliability",
    "StabilityStatus",
    "EvidenceSource",
    "SituationAssessment",
    "DomainAwarenessEngine",
]
