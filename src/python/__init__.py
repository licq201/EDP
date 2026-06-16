"""
EDP - 期望域感知法 (Expectation Domain Perception Method)

基于多源情报融合 (Multi-Source Intelligence Fusion)、态势感知 (Situation Awareness)、
概率分析 (Probability Analysis)、贝叶斯推断 (Bayesian Inference) 与 Shin 方法
(Shin's Method) 的域感知概率推断框架。

本框架将来自不同情报源的观测证据通过域感知引擎进行一致性评估与可靠性加权，
经由贝叶斯推断形成后验概率分布，并利用概率流梯度图对后验空间进行放大分析，
最终输出可验证的期望域分配方案。

For academic research purposes only.

Example:
    >>> from edp import (
    ...     ProbabilityEngine,
    ...     FlowAmplificationEngine,
    ...     DomainAwarenessEngine,
    ...     AllocationEngine,
    ... )
    >>>
    >>> # 初始化各核心引擎
    >>> engine = ProbabilityEngine()
    >>> amplifier = FlowAmplificationEngine()
    >>> awareness = DomainAwarenessEngine()
    >>> allocator = AllocationEngine()
    >>>
    >>> # 基于观测赔率计算真实概率（Shin 方法）
    >>> result = engine.calculate_true_probability({
    ...     'outcome_a': 1.50,
    ...     'outcome_b': 4.20,
    ...     'outcome_c': 6.00,
    ... })
    >>> print(result.true_probabilities)
"""

from .probability_engine import (
    BayesianPosterior,
    BayesianPrior,
    FlowDirection,
    FlowReport,
    FlowResult,
    IntelligenceSource,
    MarketType,
    ProbabilityEngine,
    ProbabilitySnapshot,
    TrueProbabilityResult,
)
from .flow_amplification import (
    AmplificationLevel,
    AmplificationReport,
    AmplificationResult,
    FlowAmplificationEngine,
    GradientEdge,
    GradientGraph,
)
from .domain_awareness import (
    DomainAwarenessEngine,
    EvidenceSource,
    EvidenceType,
    SituationAssessment,
    SourceReliability,
    StabilityStatus,
)
from .scheme_designer import (
    Allocation,
    AllocationBundle,
    AllocationEngine,
    AllocationLeg,
    RiskLevel,
    ValidationResult,
)

__version__ = "4.1.0"
__author__ = "EDP Research Team"
__license__ = "MIT"

__all__ = [
    # Probability Engine — 概率分析与贝叶斯推断
    "MarketType",
    "FlowDirection",
    "IntelligenceSource",
    "ProbabilitySnapshot",
    "TrueProbabilityResult",
    "BayesianPrior",
    "BayesianPosterior",
    "FlowResult",
    "FlowReport",
    "ProbabilityEngine",
    # Flow Amplification — 概率流梯度放大
    "AmplificationLevel",
    "GradientEdge",
    "GradientGraph",
    "AmplificationResult",
    "AmplificationReport",
    "FlowAmplificationEngine",
    # Domain Awareness — 多源情报融合与态势感知
    "EvidenceType",
    "SourceReliability",
    "StabilityStatus",
    "EvidenceSource",
    "SituationAssessment",
    "DomainAwarenessEngine",
    # Scheme Designer — 期望域分配与风险验证
    "RiskLevel",
    "ValidationResult",
    "AllocationLeg",
    "Allocation",
    "AllocationBundle",
    "AllocationEngine",
]
