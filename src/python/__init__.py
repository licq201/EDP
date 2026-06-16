"""
SPAF - Sports Probability Analysis Framework

A domain-aware, situational-awareness-driven, probability-flow-based
sports prediction optimization system.

For academic research and educational purposes only.

Example:
    >>> from spaf import ProbabilityEngine, FlowAnalyzer, SchemeDesigner
    >>>
    >>> # Initialize engines
    >>> engine = ProbabilityEngine()
    >>> analyzer = FlowAnalyzer()
    >>> designer = SchemeDesigner()
    >>>
    >>> # Calculate true probability
    >>> result = engine.calculate_true_probability({
    ...     'home': 1.50,
    ...     'draw': 4.20,
    ...     'away': 6.00
    ... })
    >>> print(result.true_probabilities)
"""

from .probability_engine import (
    MarketType,
    FlowDirection,
    ProbabilitySnapshot,
    TrueProbabilityResult,
    FlowResult,
    FlowReport,
    ProbabilityEngine,
)

from .flow_analyzer import (
    AmplificationLevel,
    AmplificationResult,
    AmplificationReport,
    FlowAnalyzer,
)

from .scheme_designer import (
    RiskLevel,
    ValidationResult,
    SchemeLeg,
    Scheme,
    SchemeBundle,
    SchemeDesigner,
)

__version__ = "4.0.0"
__author__ = "SPAF Team"
__license__ = "MIT"

__all__ = [
    # Probability Engine
    "MarketType",
    "FlowDirection",
    "ProbabilitySnapshot",
    "TrueProbabilityResult",
    "FlowResult",
    "FlowReport",
    "ProbabilityEngine",
    # Flow Analyzer
    "AmplificationLevel",
    "AmplificationResult",
    "AmplificationReport",
    "FlowAnalyzer",
    # Scheme Designer
    "RiskLevel",
    "ValidationResult",
    "SchemeLeg",
    "Scheme",
    "SchemeBundle",
    "SchemeDesigner",
]
