"""
EDP - 期望域感知方法 (Expectation Domain Perception Method) V2.0
流向倍增引擎 (Layer 3: Flow Amplification)

本模块实现概率流向的倍增效应分析。当一个结果的概率发生显著变化时，
该信号会沿 EventGraph 传播到相邻结果，产生倍增效应。

核心公式：
    AmpScore = BaseFlow × (0.5 + 0.5×Consistency)
             × (1 + GradientPos) × MarketMomentum

    - BaseFlow:       基础概率流向（百分点）
    - Consistency:    EventGraph 上相邻结果的同向比例
    - GradientPos:    低概率结果有更高倍增潜力
    - MarketMomentum: 整体市场动量

信号沿 EventGraph BFS 传播，衰减率 decay=0.7，最大深度 3。
级联检测：高动量 + 低一致性 = 可能的信息级联（羊群效应）。

理论基础：
    Banerjee, A.V. (1992). "A Simple Model of Herd Behavior."
        The Quarterly Journal of Economics, 107(3), 797-817.
    Moskowitz, T.J., Ooi, Y.H. & Pedersen, L.H. (2012).
        "Time Series Momentum." Journal of Financial Economics, 104(2), 228-250.

⚠️ 风险警示 ⚠️
    本模块仅供学术研究与教育用途。倍增信号为统计推断产物，
    不构成任何投资建议、决策建议或交易指导。使用者须自行承担
    一切决策风险。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from .core import EventGraph
from .probability_engine import FlowDirection, FlowReport


class AmplificationLevel(Enum):
    """倍增等级分类（基于评分绝对值）。"""

    NONE = "none"  # < 1
    LOW = "low"  # 1 - 3
    MEDIUM = "medium"  # 3 - 6
    HIGH = "high"  # 6 - 10
    VERY_HIGH = "very_high"  # 10 - 15
    EXCEPTIONAL = "exceptional"  # >= 15


@dataclass
class AmplificationResult:
    """单个结果的倍增分析结果。"""

    outcome: str
    base_flow_pp: float
    directional_consistency: float  # [0, 1]
    gradient_position: float  # [0, 1]
    market_momentum: float  # ~[0.7, 1.5]
    amplification_score: float
    level: AmplificationLevel
    confidence: float = 1.0
    propagation_depth: int = 1
    adjacent_signals: list[tuple[str, float]] = field(default_factory=list)

    def is_reliable(self, min_confidence: float = 0.5) -> bool:
        return self.confidence >= min_confidence and self.level != AmplificationLevel.NONE

    def get_signal_strength(self) -> float:
        return min(abs(self.amplification_score) / 10.0, 1.0)


@dataclass
class AmplificationReport:
    """完整倍增分析报告。"""

    outcomes: list[str]
    amplifications: list[AmplificationResult] = field(default_factory=list)
    aggregate_momentum: float = 0.0
    market_cascade_risk: float = 0.0
    generated_at: datetime = field(default_factory=datetime.now)

    @property
    def match_id(self) -> str:
        return f"amp_{self.generated_at.timestamp():.0f}"

    def get_high_amplification(self) -> list[AmplificationResult]:
        """返回 HIGH / VERY_HIGH / EXCEPTIONAL 等级的倍增。"""
        strong = {
            AmplificationLevel.HIGH,
            AmplificationLevel.VERY_HIGH,
            AmplificationLevel.EXCEPTIONAL,
        }
        return [a for a in self.amplifications if a.level in strong]

    def get_reliable_amplifications(self, min_confidence: float = 0.5) -> list[AmplificationResult]:
        return [a for a in self.amplifications if a.is_reliable(min_confidence)]

    def get_cascading_signals(self) -> dict[str, list[str]]:
        """获取呈现级联传播特征的信号。"""
        cascading: dict[str, list[str]] = {}
        for amp in self.get_high_amplification():
            if amp.propagation_depth > 1:
                cascading[amp.outcome] = [
                    adj[0] for adj in amp.adjacent_signals[: amp.propagation_depth]
                ]
        return cascading

    def get_summary(self) -> dict[str, Any]:
        return {
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
    概率流向倍增引擎 (L3)。

    倍增效应发生在概率流向沿 EventGraph 传播时：一个结果的流向
    信号会传播到相邻结果，形成"级联放大"。

    分析原则：
        1. 仅正向（概率上升）流向获得完整倍增
        2. 负向流向获得衰减倍增（×0.3）
        3. 相邻结果同向比例越高，一致性越强
        4. 低概率结果具有更高倍增潜力
        5. 整体市场动量作为乘数

    ⚠️ 本引擎仅供学术研究，输出不构成任何决策建议。
    """

    THRESHOLD_LOW = 1.0
    THRESHOLD_MEDIUM = 3.0
    THRESHOLD_HIGH = 6.0
    THRESHOLD_VERY_HIGH = 10.0
    THRESHOLD_EXCEPTIONAL = 15.0

    MIN_BASE_FLOW_THRESHOLD = 1.0
    PROPAGATION_DECAY = 0.7
    MAX_PROPAGATION_DEPTH = 3

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}
        self.min_base_flow = self.config.get("min_base_flow", self.MIN_BASE_FLOW_THRESHOLD)
        self.confidence_decay = self.config.get("confidence_decay", 0.9)
        self.propagation_decay = self.config.get("propagation_decay", self.PROPAGATION_DECAY)

    def classify_amplification_level(self, score: float) -> AmplificationLevel:
        """将倍增评分分类为等级。"""
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
        计算方向一致性。

        Consistency = (同向数 + 0.5×稳定数) / 相邻总数
        """
        if not adjacent_outcomes:
            return 0.0

        flow_map = {f.outcome: f for f in flow_report.flows}
        outcome_flow = flow_map.get(outcome)
        if outcome_flow is None:
            return 0.0

        primary_direction = outcome_flow.direction
        consistent_count = 0.0

        for adj in adjacent_outcomes:
            adj_flow = flow_map.get(adj)
            if adj_flow is None:
                continue

            if primary_direction == FlowDirection.UPWARD and adj_flow.direction in (
                FlowDirection.UPWARD,
                FlowDirection.STABLE,
            ):
                consistent_count += 1.0 if adj_flow.direction == FlowDirection.UPWARD else 0.5
            elif primary_direction == FlowDirection.DOWNWARD and adj_flow.direction in (
                FlowDirection.DOWNWARD,
                FlowDirection.STABLE,
            ):
                consistent_count += 1.0 if adj_flow.direction == FlowDirection.DOWNWARD else 0.5
            elif (
                primary_direction == FlowDirection.STABLE
                and adj_flow.direction == FlowDirection.STABLE
            ):
                consistent_count += 0.5

        return consistent_count / len(adjacent_outcomes)

    def calculate_gradient_position(
        self,
        outcome: str,
        outcome_probabilities: dict[str, float],
        direction_outcomes: list[str],
    ) -> float:
        """
        计算归一化梯度位置。

        低概率结果有更高位置（更高倍增潜力）。
            Position = (max_prob - outcome_prob) / (max_prob - min_prob)
        """
        if outcome not in outcome_probabilities:
            return 0.0

        direction_probs = [outcome_probabilities.get(o, 0.0) for o in direction_outcomes]
        if not direction_probs:
            return 0.5

        max_prob = max(direction_probs)
        min_prob = min(direction_probs)

        if max_prob == min_prob:
            return 0.5

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
        计算市场动量乘数。

        相邻结果同向 → 增强；反向 → 减弱。
        返回值范围约 [0.7, 1.5]。
        """
        if not adjacent_flows:
            return 1.0

        momentum_sum = 0.0
        total_weight = 0.0

        for adj_outcome, adj_flow in adjacent_flows:
            weight = max(outcome_probabilities.get(adj_outcome, 0.1), 0.01)
            total_weight += weight
            sign = 1.0 if (base_flow >= 0) == (adj_flow >= 0) else -1.0
            momentum_sum += sign * abs(adj_flow) * weight

        if total_weight == 0:
            return 1.0

        avg_momentum = momentum_sum / total_weight

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
        event_graph: EventGraph,
        flow_report: FlowReport,
        max_depth: int = 3,
    ) -> tuple[int, list[tuple[str, float]]]:
        """
        BFS 计算信号沿 EventGraph 的传播深度。

        signal_depth_d = base_flow × decay^d
        信号持续直到 < min_base_flow 阈值。
        """
        flow_map = {f.outcome: f for f in flow_report.flows}
        visited: set[str] = {outcome}
        signals: list[tuple[str, float]] = []
        depth = 0

        current_outcomes = event_graph.get_adjacent(outcome)
        current_signal = abs(flow_pp)

        for d in range(max_depth):
            next_outcomes: list[str] = []
            depth_signals: list[float] = []

            for adj in current_outcomes:
                if adj in visited:
                    continue
                visited.add(adj)

                adj_flow = flow_map.get(adj)
                if adj_flow is None:
                    continue

                signal_strength = current_signal * self.propagation_decay ** (d + 1)

                # 仅同向传播
                if (adj_flow.flow_pp >= 0) == (flow_pp >= 0):
                    depth_signals.append(signal_strength)
                    signals.append((adj, signal_strength))
                    next_outcomes.extend(event_graph.get_adjacent(adj))

            if depth_signals and max(depth_signals) >= self.min_base_flow:
                depth = d + 1
            else:
                break

            current_outcomes = next_outcomes
            current_signal = max(depth_signals) if depth_signals else current_signal

        return depth, signals

    def calculate_amplification(
        self,
        flow_report: FlowReport,
        outcome_probabilities: dict[str, float],
        event_graph: EventGraph | None = None,
        confidence_modifiers: dict[str, float] | None = None,
    ) -> AmplificationReport:
        """
        计算所有结果的倍增评分。

        AmpScore = BaseFlow × (0.5 + 0.5×Consistency)
                 × (1 + GradientPos) × MarketMomentum

        仅正向（UPWARD）流向获得完整倍增；负向流向获得衰减倍增（×0.3）。
        """
        # 如果没有 EventGraph，构建一个空图（无传播）
        if event_graph is None:
            event_graph = EventGraph()
            for f in flow_report.flows:
                event_graph.add_node(f.outcome)

        confidence_modifiers = confidence_modifiers or {}
        flow_map = {f.outcome: f for f in flow_report.flows}

        amplifications: list[AmplificationResult] = []

        for flow_result in flow_report.flows:
            outcome = flow_result.outcome
            base_flow = flow_result.flow_pp

            # 基础流向不足，跳过
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

            adjacent = event_graph.get_adjacent(outcome)

            directional_consistency = self.calculate_directional_consistency(
                flow_report, outcome, adjacent
            )

            same_direction = [
                o for o, f in flow_map.items() if f.direction == flow_result.direction
            ]
            gradient_position = self.calculate_gradient_position(
                outcome, outcome_probabilities, same_direction
            )

            adjacent_flows = [
                (f.outcome, f.flow_pp) for f in flow_report.flows if f.outcome in adjacent
            ]

            market_momentum = self.calculate_market_momentum(
                outcome, base_flow, adjacent_flows, outcome_probabilities
            )

            propagation_depth, adjacent_signals = self.calculate_propagation_depth(
                outcome, base_flow, event_graph, flow_report
            )

            # 计算倍增评分
            if flow_result.direction == FlowDirection.UPWARD:
                raw_score = (
                    base_flow
                    * (0.5 + 0.5 * directional_consistency)
                    * (1.0 + gradient_position)
                    * market_momentum
                )
            else:
                # 负向流向衰减倍增
                raw_score = base_flow * 0.3 * directional_consistency

            confidence = confidence_modifiers.get(outcome, 1.0)
            adjusted_score = raw_score * confidence

            level = self.classify_amplification_level(adjusted_score)

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

        # 聚合统计
        aggregate_momentum = sum(a.amplification_score for a in amplifications) / max(
            len(amplifications), 1
        )

        # 级联风险：高动量 + 低一致性
        high_momentum = [a for a in amplifications if a.amplification_score > 5.0]
        cascade_risk = 0.0
        if high_momentum:
            for amp in high_momentum:
                if amp.directional_consistency < 0.5:
                    cascade_risk += 0.2 / len(high_momentum)
            cascade_risk = min(cascade_risk, 1.0)

        return AmplificationReport(
            outcomes=[a.outcome for a in amplifications],
            amplifications=amplifications,
            aggregate_momentum=aggregate_momentum,
            market_cascade_risk=cascade_risk,
        )


__all__ = [
    "AmplificationLevel",
    "AmplificationResult",
    "AmplificationReport",
    "FlowAmplificationEngine",
]
