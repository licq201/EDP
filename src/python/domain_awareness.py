"""
EDP - 期望域感知方法 (Expectation Domain Perception Method) V2.0
全域感知引擎 (Layer 4: Domain Awareness)

本模块实现多源情报融合，将来自不同信息来源（市场、模型、专家、NLP、
传感器、LLM、API）的证据融合为统一的概率态势评估。

融合方法：
    - linear:   线性池（加权平均）
    - log_odds: 对数优比池
    - bayesian: 序贯贝叶斯更新
    - hybrid:   三者均值

源权重计算：
    w_i = reliability_i × confidence_i × 2^{−Δt/t½}

共识分析：
    Consensus = 1 − min(σ/0.5, 1.0)
    σ 越小 → 共识越高

异常检测：
    Z-score > 阈值 → 标记为异常

理论基础：
    Genest, C. & Zidek, J.V. (1986). "Combining Probability Distributions."
        Statistical Science, 1(1), 114-135.
    DeGroot, M.H. (1974). "Reaching a Consensus."
        Journal of the American Statistical Association, 69(345), 118-121.
    Endsley, M.R. (1988). "Design and Evaluation for Situation Awareness."
        Proceedings of the Human Factors Society Annual Meeting.

⚠️ 风险警示 ⚠️
    本模块仅供学术研究与教育用途。融合概率为统计推断产物，
    不构成任何投资建议、决策建议或交易指导。使用者须自行承担
    一切决策风险。
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class EvidenceType(Enum):
    """证据来源类型。"""

    MARKET = "market"
    MODEL = "model"
    EXPERT = "expert"
    NLP = "nlp"
    SENSOR = "sensor"
    LLM = "llm"
    API = "api"
    UNKNOWN = "unknown"


class SourceReliability(Enum):
    """源可靠性等级（STANAG 2511 改编）。"""

    A = (1.00, "完全可靠")
    B = (0.80, "通常可靠")
    C = (0.60, "相当可靠")
    D = (0.40, "通常不可靠")
    E = (0.20, "不可靠")
    F = (0.50, "无法判断")

    def __init__(self, weight: float, description: str):
        self.weight = weight
        self.description = description


class StabilityLevel(Enum):
    """态势稳定性分类。"""

    STABLE = "stable"  # 高共识，低异常
    UNSTABLE = "unstable"  # 低共识，无异常
    EMERGING = "emerging"  # 中共识，强动量
    AMBIGUOUS = "ambiguous"  # 中共识，高分歧
    ANOMALOUS = "anomalous"  # 存在异常


@dataclass
class EvidenceSource:
    """
    证据来源（标准化）。

    Attributes:
        source_id: 来源唯一标识
        evidence_type: 来源类型
        reliability: 可靠性 [0,1]
        timestamp: 证据时间戳
        data: 证据数据（至少含 "probability"）
        confidence: 自报信心 [0,1]
    """

    source_id: str
    evidence_type: EvidenceType
    reliability: SourceReliability
    timestamp: datetime
    data: dict[str, Any]
    confidence: float = 0.7

    @property
    def probability(self) -> float:
        p = self.data.get("probability")
        if p is None:
            return 0.5
        return max(0.0, min(1.0, float(p)))

    @property
    def reliability_weight(self) -> float:
        return float(self.reliability.weight)


@dataclass
class SituationAssessment:
    """多源融合态势评估结果。"""

    aggregate_probability: float
    source_weights: dict[str, float]
    consensus_score: float
    stability: StabilityLevel
    anomaly_flags: list[str] = field(default_factory=list)
    source_count: int = 0
    fusion_method: str = "hybrid"
    confidence: float = 0.5
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_consensus(self) -> bool:
        return self.consensus_score > 0.7

    @property
    def has_anomaly(self) -> bool:
        return len(self.anomaly_flags) > 0

    def get_summary(self) -> dict[str, Any]:
        return {
            "aggregate_probability": self.aggregate_probability,
            "consensus_score": self.consensus_score,
            "stability": self.stability.value,
            "source_count": self.source_count,
            "fusion_method": self.fusion_method,
            "confidence": self.confidence,
            "anomaly_flags": self.anomaly_flags,
        }


class DomainAwarenessEngine:
    """
    全域感知引擎 (L4)。

    融合流程：
        1. 源预处理：reliability × confidence × temporal_decay → 归一化权重
        2. 融合（可选模式）：
           - linear:   加权平均
           - log_odds: 对数优比池
           - bayesian: 序贯贝叶斯
           - hybrid:   三者均值
        3. 共识分析：σ 越小 → 共识越高
        4. 异常检测：Z-score > 阈值 → 标记
        5. 稳定性分类
        6. 置信度校准

    ⚠️ 本引擎仅供学术研究，输出不构成任何决策建议。
    """

    TIME_DECAY_HOURS = 24.0
    CONSENSUS_HIGH = 0.7
    CONSENSUS_LOW = 0.3
    ANOMALY_THRESHOLD = 2.0

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}
        self.time_decay_hours: float = float(
            self.config.get("time_decay_hours", self.TIME_DECAY_HOURS)
        )
        self.consensus_high: float = float(self.config.get("consensus_high", self.CONSENSUS_HIGH))
        self.consensus_low: float = float(self.config.get("consensus_low", self.CONSENSUS_LOW))
        self.anomaly_threshold: float = float(
            self.config.get("anomaly_threshold", self.ANOMALY_THRESHOLD)
        )

    # ------------------------------------------------------------------
    # 源权重计算
    # ------------------------------------------------------------------

    def calculate_source_weight(self, source: EvidenceSource, now: datetime | None = None) -> float:
        """
        计算源权重：
            w_i = reliability_i × confidence_i × 2^{−Δt/t½}
        """
        now = now or datetime.now()
        delta_hours = max((now - source.timestamp).total_seconds() / 3600.0, 0.0)
        temporal_decay = 2.0 ** (-delta_hours / self.time_decay_hours)
        return float(source.reliability_weight * source.confidence * temporal_decay)

    def _normalize_weights(self, weights: dict[str, float]) -> dict[str, float]:
        total = sum(weights.values())
        if total <= 0:
            n = len(weights)
            result: dict[str, float] = dict.fromkeys(weights, 1.0 / n) if n > 0 else {}
            return result
        return {k: v / total for k, v in weights.items()}

    # ------------------------------------------------------------------
    # 融合方法
    # ------------------------------------------------------------------

    def _fuse_linear(self, sources: list[EvidenceSource], weights: dict[str, float]) -> float:
        """线性池：p = Σ(w_i × p_i)。"""
        return sum(weights.get(s.source_id, 0.0) * s.probability for s in sources)

    def _fuse_log_odds(self, sources: list[EvidenceSource], weights: dict[str, float]) -> float:
        """对数优比池：logit(p) = Σ(w_i × logit(p_i))。"""
        eps = 1e-6
        logit_sum = 0.0
        for s in sources:
            p = max(eps, min(1 - eps, s.probability))
            logit = math.log(p / (1 - p))
            logit_sum += weights.get(s.source_id, 0.0) * logit
        # 数值稳定 sigmoid
        if logit_sum >= 0:
            ez = math.exp(-logit_sum)
            return 1.0 / (1.0 + ez)
        ez = math.exp(logit_sum)
        return ez / (1.0 + ez)

    def _fuse_bayesian(
        self,
        sources: list[EvidenceSource],
        weights: dict[str, float],
        prior_probability: float,
    ) -> float:
        """
        序贯贝叶斯：
            log-odds_posterior = log-odds_prior + Σ[logit(p_i) − logit(p_prior)]
        """
        eps = 1e-6
        prior = max(eps, min(1 - eps, prior_probability))
        prior_logodds = math.log(prior / (1 - prior))

        log_odds = prior_logodds
        for s in sources:
            p = max(eps, min(1 - eps, s.probability))
            source_logodds = math.log(p / (1 - p))
            prior_lo = math.log(prior / (1 - prior))
            log_odds += weights.get(s.source_id, 0.0) * (source_logodds - prior_lo)

        if log_odds >= 0:
            ez = math.exp(-log_odds)
            return 1.0 / (1.0 + ez)
        ez = math.exp(log_odds)
        return ez / (1.0 + ez)

    def _fuse_hybrid(
        self,
        sources: list[EvidenceSource],
        weights: dict[str, float],
        prior_probability: float,
    ) -> float:
        """混合：三者均值。"""
        p_linear = self._fuse_linear(sources, weights)
        p_logodds = self._fuse_log_odds(sources, weights)
        p_bayesian = self._fuse_bayesian(sources, weights, prior_probability)
        return (p_linear + p_logodds + p_bayesian) / 3.0

    # ------------------------------------------------------------------
    # 共识与异常分析
    # ------------------------------------------------------------------

    def calculate_consensus(
        self, sources: list[EvidenceSource], weights: dict[str, float]
    ) -> float:
        """
        共识评分：Consensus = 1 − min(σ/0.5, 1.0)
        """
        if not sources:
            return 0.0
        weighted_mean = sum(weights.get(s.source_id, 0.0) * s.probability for s in sources)
        variance = sum(
            weights.get(s.source_id, 0.0) * (s.probability - weighted_mean) ** 2 for s in sources
        )
        std = math.sqrt(max(variance, 0.0))
        return max(0.0, 1.0 - min(std / 0.5, 1.0))

    def detect_anomalies(
        self, sources: list[EvidenceSource], weights: dict[str, float]
    ) -> list[str]:
        """Z-score 异常检测。"""
        if len(sources) < 3:
            return []

        weighted_mean = sum(weights.get(s.source_id, 0.0) * s.probability for s in sources)
        variance = sum(
            weights.get(s.source_id, 0.0) * (s.probability - weighted_mean) ** 2 for s in sources
        )
        std = math.sqrt(max(variance, 0.0))
        if std < 1e-6:
            return []

        anomalies: list[str] = []
        for s in sources:
            z = abs(s.probability - weighted_mean) / std
            if z > self.anomaly_threshold:
                anomalies.append(s.source_id)
        return anomalies

    def classify_stability(
        self,
        consensus: float,
        anomaly_count: int,
        momentum: float = 0.0,
    ) -> StabilityLevel:
        """态势稳定性分类。"""
        if anomaly_count > 0:
            return StabilityLevel.ANOMALOUS
        if consensus >= self.consensus_high:
            return StabilityLevel.STABLE
        if consensus <= self.consensus_low:
            return StabilityLevel.UNSTABLE
        if abs(momentum) > 2.0:
            return StabilityLevel.EMERGING
        return StabilityLevel.AMBIGUOUS

    def _calibrate_confidence(
        self,
        consensus: float,
        source_factor: float,
        effective_factor: float,
        avg_reliability: float,
        anomaly_count: int,
    ) -> float:
        """
        置信度校准：
            confidence = 0.35×consensus + 0.25×source_factor
                       + 0.20×effective_factor + 0.20×avg_reliability
                       − 0.05×anomaly_count
        """
        conf = (
            0.35 * consensus
            + 0.25 * source_factor
            + 0.20 * effective_factor
            + 0.20 * avg_reliability
            - 0.05 * anomaly_count
        )
        return max(0.0, min(1.0, conf))

    # ------------------------------------------------------------------
    # 主接口
    # ------------------------------------------------------------------

    def assess_situation(
        self,
        sources: list[EvidenceSource],
        prior_probability: float = 0.5,
        fusion_method: str = "hybrid",
    ) -> SituationAssessment:
        """
        多源情报融合 → 统一概率态势评估。

        Args:
            sources: 证据来源列表
            prior_probability: 先验概率
            fusion_method: linear / log_odds / bayesian / hybrid
        """
        if not sources:
            return SituationAssessment(
                aggregate_probability=prior_probability,
                source_weights={},
                consensus_score=0.0,
                stability=StabilityLevel.AMBIGUOUS,
                source_count=0,
                fusion_method=fusion_method,
                confidence=0.0,
            )

        # 1. 计算源权重
        raw_weights = {s.source_id: self.calculate_source_weight(s) for s in sources}
        weights = self._normalize_weights(raw_weights)

        # 2. 融合
        if fusion_method == "linear":
            agg_prob = self._fuse_linear(sources, weights)
        elif fusion_method == "log_odds":
            agg_prob = self._fuse_log_odds(sources, weights)
        elif fusion_method == "bayesian":
            agg_prob = self._fuse_bayesian(sources, weights, prior_probability)
        else:  # hybrid
            agg_prob = self._fuse_hybrid(sources, weights, prior_probability)

        agg_prob = max(0.0, min(1.0, agg_prob))

        # 3. 共识分析
        consensus = self.calculate_consensus(sources, weights)

        # 4. 异常检测
        anomalies = self.detect_anomalies(sources, weights)

        # 5. 稳定性分类
        # 用 aggregate 与 prior 的差作为动量近似
        momentum = (agg_prob - prior_probability) * 100.0
        stability = self.classify_stability(consensus, len(anomalies), momentum)

        # 6. 置信度校准
        source_factor = min(len(sources) / 5.0, 1.0)
        effective_weight = sum(raw_weights.values())
        max_possible = len(sources) * 1.0  # 最大可能权重（reliability=1, confidence=1, decay=1）
        effective_factor = min(effective_weight / max(max_possible, 1e-6), 1.0)
        avg_reliability = sum(s.reliability_weight for s in sources) / len(sources)
        confidence = self._calibrate_confidence(
            consensus, source_factor, effective_factor, avg_reliability, len(anomalies)
        )

        return SituationAssessment(
            aggregate_probability=agg_prob,
            source_weights=weights,
            consensus_score=consensus,
            stability=stability,
            anomaly_flags=anomalies,
            source_count=len(sources),
            fusion_method=fusion_method,
            confidence=confidence,
            metadata={
                "prior_probability": prior_probability,
                "raw_weights": raw_weights,
                "momentum_pp": momentum,
                "avg_reliability": avg_reliability,
            },
        )

    def cross_validate(
        self,
        group_a: list[EvidenceSource],
        group_b: list[EvidenceSource],
        prior_probability: float = 0.5,
    ) -> dict[str, Any]:
        """
        两组独立源交叉验证。

        Returns:
            agreement: 两组概率一致性 [0,1]
            delta: 概率差
            combined: 合并后评估
            meta_confidence: 元置信度
        """
        if not group_a or not group_b:
            return {
                "agreement": 0.0,
                "delta": 0.0,
                "combined": None,
                "meta_confidence": 0.0,
            }

        assess_a = self.assess_situation(group_a, prior_probability)
        assess_b = self.assess_situation(group_b, prior_probability)

        delta = abs(assess_a.aggregate_probability - assess_b.aggregate_probability)
        agreement = max(0.0, 1.0 - delta * 2.0)

        combined_sources = group_a + group_b
        combined = self.assess_situation(combined_sources, prior_probability)

        meta_confidence = (
            agreement * 0.5
            + combined.consensus_score * 0.3
            + min(combined.source_count / 8.0, 1.0) * 0.2
        )

        return {
            "agreement": agreement,
            "delta": delta,
            "combined": combined,
            "meta_confidence": meta_confidence,
            "group_a_probability": assess_a.aggregate_probability,
            "group_b_probability": assess_b.aggregate_probability,
        }

    # ------------------------------------------------------------------
    # 模型多样性 / 冗余分析（DTVW 思想，arXiv 2508.07136, 2025）
    # ------------------------------------------------------------------

    @staticmethod
    def model_diversity(sources: list[EvidenceSource]) -> dict[str, float]:
        """
        计算来源间的多样性（非冗余信息量）。

        理论依据：DTVW（Luo, Kang & Luo, 2025）——多样性量化预测差异，
        捕获非冗余信息以补充精度。冗余来源应被降权。

        度量：
            - mean_pairwise_distance: 源间概率的平均绝对差（越大越多样）
            - redundancy: 1 − diversity，冗余度（越大越冗余）
            - effective_sources: 多样性调整后的"有效来源数"
        """
        if len(sources) < 2:
            return {
                "mean_pairwise_distance": 0.0,
                "redundancy": 0.0,
                "diversity": 1.0 if sources else 0.0,
                "effective_sources": float(len(sources)),
            }
        probs = [s.probability for s in sources]
        n = len(probs)
        total_dist = 0.0
        pairs = 0
        for i in range(n):
            for j in range(i + 1, n):
                total_dist += abs(probs[i] - probs[j])
                pairs += 1
        mean_dist = total_dist / max(pairs, 1)
        # diversity ∈ [0,1]，平均距离归一化（0.5 为最大可能距离）
        diversity = min(mean_dist / 0.5, 1.0)
        redundancy = 1.0 - diversity
        # 有效来源数：多样性越高，有效来源越接近真实数量
        effective = 1.0 + (n - 1) * diversity
        return {
            "mean_pairwise_distance": mean_dist,
            "redundancy": redundancy,
            "diversity": diversity,
            "effective_sources": effective,
        }


__all__ = [
    "EvidenceType",
    "SourceReliability",
    "StabilityLevel",
    "EvidenceSource",
    "SituationAssessment",
    "DomainAwarenessEngine",
]
