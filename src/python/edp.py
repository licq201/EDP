"""
EDP - 期望域感知方法 (Expectation Domain Perception Method) V2.0
顶层接口

本模块提供 EDP 框架的统一入口。一个使用者只需：
    1. 传入域适配器（DomainAdapter）
    2. 传入信息来源（raw_data / evidence）
    3. 调用 analyze()

即可获得完整的概率态势分析：
    - 融合概率
    - 流向分析
    - 倍增信号
    - 资源分配方案（仅供研究，不构成决策建议）
    - 预测评估

══════════════════════════════════════════════════════════════════════
⚠️⚠️⚠️ 严重风险警示 ⚠️⚠️⚠️
══════════════════════════════════════════════════════════════════════

EDP 仅供学术研究与教育用途。它【不构成】任何投资建议、决策建议、
交易指导或财务规划建议。

1. 概率预测的不确定性：所有概率均为估计值，存在显著不确定性。
   实际发生的结果可能与预测概率完全不符。

2. 历史不代表未来：本框架基于历史数据与统计模式，但历史概率
   模式【不保证】未来结果。"黑天鹅"事件不在模型覆盖范围内。

3. 资金损失风险：AllocationEngine 输出的分配方案可能导致全部
   本金损失。任何实际决策都存在重大风险。

4. 模型局限性：框架依赖输入数据质量、域适配器的正确实现、
   以及各引擎的数学假设。任何环节的错误都会传播到最终结果。

5. 非专业建议：本框架的输出【不是】持牌专业人士的建议。在
   做任何实际决策前，请咨询合格的专业人士。

使用者须自行承担一切决策风险。
══════════════════════════════════════════════════════════════════════
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from .core import (
    DomainAdapter,
    EventGraph,
    Evidence,
    GenericDomain,
    Outcome,
    Quote,
    Snapshot,
)
from .probability_engine import (
    FlowReport,
    ProbabilityEngine,
)
from .online_aggregator import OnlineAggregator
from .flow_amplification import (
    AmplificationReport,
    FlowAmplificationEngine,
)
from .domain_awareness import (
    DomainAwarenessEngine,
    EvidenceSource,
    EvidenceType,
    SituationAssessment,
    SourceReliability,
)
from .allocation_engine import (
    AllocationBundle,
    AllocationEngine,
    AllocationLeg,
    RiskTier,
)
from .calibration import CalibrationEngine
from .domain_awareness import StabilityLevel


class EDP:
    """
    EDP V2.0 顶层接口。

    一个使用者只需：
        1. 传入域适配器（或用内置的 GenericDomain）
        2. 传入信息来源（raw_data / evidence）
        3. 调用 analyze()

    即可获得：融合概率、流向分析、倍增信号、资源分配方案。

    ════════════════════════════════════════════════════════════════
    ⚠️ 严重风险警示 ⚠️
    EDP 仅供学术研究，输出不构成任何决策建议。详见模块顶部警示。
    ════════════════════════════════════════════════════════════════

    用法示例：
        from edp import EDP, GenericDomain, Outcome, Evidence

        domain = GenericDomain([
            Outcome("a", "结果A"), Outcome("b", "结果B"),
        ])
        edp = EDP(domain)
        result = edp.analyze(
            evidence=[
                Evidence("src1", "model", {"probability": 0.7}, confidence=0.8),
                Evidence("src2", "expert", {"probability": 0.65}, confidence=0.6),
            ],
            budget=1000,
        )
        print(result["summary"])
    """

    VERSION = "2.0"

    def __init__(
        self,
        domain: DomainAdapter,
        config: dict[str, Any] | None = None,
    ):
        """
        Args:
            domain: 域适配器
            config: 全局配置（传给各子引擎）
        """
        self.domain = domain
        self.config = config or {}

        # 初始化各层引擎
        self.prob_engine = ProbabilityEngine(self.config.get("probability", {}))
        self.aggregator = OnlineAggregator(self.config.get("aggregator", {}))
        self.flow_engine = FlowAmplificationEngine(self.config.get("flow", {}))
        self.domain_engine = DomainAwarenessEngine(self.config.get("domain", {}))
        self.alloc_engine = AllocationEngine(self.config.get("allocation", {}))
        self.calib_engine = CalibrationEngine(self.config.get("calibration", {}))

        # 运行时状态
        self.snapshots: list[Snapshot] = []
        self.probabilities: dict[str, float] = {}
        self.event_graph: EventGraph | None = None
        self.outcomes: list[Outcome] = []

    # ------------------------------------------------------------------
    # 初始化
    # ------------------------------------------------------------------

    def initialize(self, context: dict | None = None) -> None:
        """初始化：获取结果、构建关系图、设置先验。"""
        self.outcomes = self.domain.get_outcomes(context)
        self.event_graph = self.domain.build_event_graph(self.outcomes)
        self.probabilities = self.domain.get_prior(context)

    # ------------------------------------------------------------------
    # 信号摄取
    # ------------------------------------------------------------------

    def ingest_signals(self, raw_data: Any) -> None:
        """
        摄取信号 → Shin 归一化 → 更新概率。

        Args:
            raw_data: 原始数据（由域适配器 normalize_signals 解析）
        """
        quotes = self.domain.normalize_signals(raw_data)
        if not quotes:
            return

        # 按 signal_type 分组
        decimal_quotes: dict[str, float] = {}
        direct_probs: dict[str, float] = {}

        for q in quotes:
            if q.signal_type == "decimal_odds" and q.value > 1.0:
                decimal_quotes[q.outcome_id] = q.value
            else:
                direct_probs[q.outcome_id] = q.to_probability()

        # Shin 归一化处理市场报价
        if decimal_quotes:
            # 补全缺失的结果（用直接概率的倒数估算）
            for oid in self.probabilities:
                if oid not in decimal_quotes and oid in direct_probs:
                    p = max(direct_probs[oid], 0.01)
                    decimal_quotes[oid] = 1.0 / p

            if len(decimal_quotes) >= 2:
                try:
                    result = self.prob_engine.calculate_true_probability(decimal_quotes)
                    self.probabilities.update(result.true_probabilities)
                except ValueError:
                    # 归一化失败，回退到直接概率
                    for oid, q in decimal_quotes.items():
                        direct_probs[oid] = 1.0 / q if q > 1.0 else 0.5

        # 直接概率更新
        if direct_probs:
            total = sum(direct_probs.values())
            if total > 1.05:
                # 归一化
                direct_probs = {k: v / total for k, v in direct_probs.items()}
            self.probabilities.update(direct_probs)

        # 最终归一化
        self._normalize_probabilities()

    def _normalize_probabilities(self) -> None:
        total = sum(self.probabilities.values())
        if total > 0:
            self.probabilities = {k: v / total for k, v in self.probabilities.items()}

    # ------------------------------------------------------------------
    # 证据融合
    # ------------------------------------------------------------------

    def add_evidence(self, evidence: list[Evidence]) -> SituationAssessment:
        """
        添加证据 → 多源融合 → 更新概率。

        Args:
            evidence: 证据列表
        """
        if not evidence:
            return SituationAssessment(
                aggregate_probability=0.5,
                source_weights={},
                consensus_score=0.0,
                stability=StabilityLevel.AMBIGUOUS,
                source_count=0,
            )

        # 转换为标准 EvidenceSource
        reliability_map = self.domain.get_reliability_map()
        sources: list[EvidenceSource] = []
        for e in evidence:
            # 来源类型映射
            try:
                etype = EvidenceType(e.source_type)
            except ValueError:
                etype = EvidenceType.UNKNOWN

            # 可靠性映射
            rel_weight = reliability_map.get(e.source_type, 0.5)
            reliability = self._match_reliability(rel_weight)

            prob = e.extract_probability()
            sources.append(
                EvidenceSource(
                    source_id=e.id,
                    evidence_type=etype,
                    reliability=reliability,
                    timestamp=e.timestamp,
                    data={"probability": prob},
                    confidence=e.confidence,
                )
            )

        # 融合
        prior = sum(self.probabilities.values()) / max(len(self.probabilities), 1)
        assessment = self.domain_engine.assess_situation(
            sources, prior_probability=prior
        )

        # 用融合结果更新每个结果的概率（按 aggregate 调整）
        # 这里简化处理：将 aggregate 作为整体趋势，按结果概率加权分布
        if self.probabilities:
            # 计算调整方向
            adjustment = assessment.aggregate_probability - prior
            new_probs: dict[str, float] = {}
            for oid, p in self.probabilities.items():
                # 按结果概率与调整方向的乘积调整
                adjusted = p * (1.0 + adjustment)
                new_probs[oid] = max(adjusted, 0.001)
            self.probabilities = new_probs
            self._normalize_probabilities()

        return assessment

    @staticmethod
    def _match_reliability(weight: float) -> SourceReliability:
        """将数值权重映射到最近的 SourceReliability 等级。"""
        if weight >= 0.9:
            return SourceReliability.A
        elif weight >= 0.7:
            return SourceReliability.B
        elif weight >= 0.5:
            return SourceReliability.C
        elif weight >= 0.3:
            return SourceReliability.D
        else:
            return SourceReliability.E

    # ------------------------------------------------------------------
    # 快照与流向分析
    # ------------------------------------------------------------------

    def snapshot(self, source: str = "edp") -> Snapshot:
        """保存概率快照。"""
        snap = Snapshot(
            timestamp=datetime.now(),
            probabilities=dict(self.probabilities),
            source=source,
        )
        self.snapshots.append(snap)
        return snap

    def analyze_flow(self) -> FlowReport | None:
        """流向分析（需 ≥2 个快照）。"""
        if len(self.snapshots) < 2:
            return None
        return self.prob_engine.analyze_flow(
            self.snapshots[-2], self.snapshots[-1]
        )

    def analyze_amplification(self, flow: FlowReport) -> AmplificationReport | None:
        """倍增分析。"""
        if not self.event_graph or not flow:
            return None
        return self.flow_engine.calculate_amplification(
            flow, self.probabilities, self.event_graph
        )

    # ------------------------------------------------------------------
    # 资源分配
    # ------------------------------------------------------------------

    def allocate(
        self,
        budget: float,
        return_multipliers: dict[str, float] | None = None,
        risk_tier: RiskTier = RiskTier.BALANCED,
    ) -> AllocationBundle:
        """
        资源分配。

        ⚠️ 警示：本方法输出仅供研究，不构成投资建议。
            实际决策可能导致本金全部损失。

        Args:
            budget: 总预算
            return_multipliers: {outcome_id: return_multiplier}
            risk_tier: 风险分层
        """
        candidates: list[AllocationLeg] = []
        for oid, prob in self.probabilities.items():
            odds = (return_multipliers or {}).get(oid, 2.0)
            flow_dir = "stable"
            signal = 0.5
            if len(self.snapshots) >= 2:
                prev = self.snapshots[-2].probabilities.get(oid, 0.5)
                curr = self.snapshots[-1].probabilities.get(oid, 0.5)
                flow_dir = "upward" if curr > prev else ("downward" if curr < prev else "stable")
                signal = min(abs(curr - prev) * 20, 1.0)
            candidates.append(
                AllocationLeg(
                    outcome_id=oid,
                    probability=prob,
                    return_multiplier=odds,
                    signal_strength=signal,
                    confidence=0.7,
                    flow_direction=flow_dir,
                )
            )
        bundle = self.alloc_engine.generate_allocation(
            budget, candidates, risk_tier=risk_tier
        )
        return self.alloc_engine.optimize_portfolio(bundle)

    # ------------------------------------------------------------------
    # 预测评估
    # ------------------------------------------------------------------

    def evaluate(self, actual_outcome: str) -> dict[str, Any]:
        """预测评估。"""
        return self.calib_engine.evaluate(self.probabilities, actual_outcome)

    # ------------------------------------------------------------------
    # 一键分析
    # ------------------------------------------------------------------

    def analyze(
        self,
        raw_data: Any = None,
        evidence: list[Evidence] | None = None,
        budget: float = 1000.0,
        return_multipliers: dict[str, float] | None = None,
        context: dict | None = None,
        risk_tier: RiskTier = RiskTier.BALANCED,
    ) -> dict[str, Any]:
        """
        一键分析：L0 → L6 完整流程。

        Args:
            raw_data: 原始信号数据（可选）
            evidence: 证据列表（可选）
            budget: 分配预算
            return_multipliers: 各结果回报倍数
            context: 域上下文
            risk_tier: 风险分层

        Returns:
            {
                "outcomes": list[Outcome],
                "probabilities": dict[str, float],
                "assessment": SituationAssessment | None,
                "flow": FlowReport | None,
                "amplification": AmplificationReport | None,
                "allocation": AllocationBundle,
                "summary": str,
                "warnings": list[str],
            }
        """
        warnings: list[str] = [
            "⚠️ EDP 输出仅供学术研究，不构成任何投资或决策建议。"
            "实际决策可能导致损失，使用者须自行承担风险。"
        ]

        # L0: 初始化
        self.initialize(context)

        # L1: 摄取信号
        if raw_data:
            self.ingest_signals(raw_data)
        self.snapshot("after_signals")

        # L4: 证据融合
        assessment = None
        if evidence:
            assessment = self.add_evidence(evidence)
            self.snapshot("after_evidence")

        # L3: 流向分析
        flow = self.analyze_flow()
        amp = self.analyze_amplification(flow) if flow else None

        # L5: 资源分配
        allocation = self.allocate(budget, return_multipliers, risk_tier)
        warnings.extend(allocation.warnings)

        # 生成摘要
        top = sorted(self.probabilities.items(), key=lambda x: x[1], reverse=True)
        top_str = f"{top[0][0]} ({top[0][1]:.1%})" if top else "N/A"
        consensus_str = (
            f"{assessment.consensus_score:.2f}" if assessment else "N/A"
        )
        summary = (
            f"最可能: {top_str} | "
            f"来源: {len(evidence or [])} | "
            f"共识: {consensus_str} | "
            f"分配: {allocation.allocated_amount:.0f}/{budget:.0f}"
        )

        return {
            "outcomes": self.outcomes,
            "probabilities": dict(self.probabilities),
            "assessment": assessment,
            "flow": flow,
            "amplification": amp,
            "allocation": allocation,
            "summary": summary,
            "warnings": warnings,
        }


__all__ = [
    "EDP",
    "DomainAdapter",
    "GenericDomain",
    "Outcome",
    "Quote",
    "Evidence",
    "Snapshot",
    "EventGraph",
    "ProbabilityEngine",
    "OnlineAggregator",
    "FlowAmplificationEngine",
    "DomainAwarenessEngine",
    "AllocationEngine",
    "CalibrationEngine",
    "AllocationLeg",
    "AllocationBundle",
    "RiskTier",
    "EvidenceSource",
    "EvidenceType",
    "SourceReliability",
    "SituationAssessment",
]

