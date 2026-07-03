"""
EDP - 期望域感知方法 (Expectation Domain Perception Method) V2.0
资源分配引擎 (Layer 5: Resource Allocation)

本模块实现基于概率预测的资源分配方案。给定预算、候选方案的概率
估计与回报倍数，计算最优分配。

核心方法：
    - Kelly 准则:           f* = (p·b − q) / b
    - 分数 Kelly:           f = kelly_fraction × f*
    - Markowitz 再平衡:     多样化目标
    - 三原则验证:           信号对齐 / 非对称潜力 / 合理结构
    - 风险分层:             CONSERVATIVE / BALANCED / AGGRESSIVE / EXTREME

══════════════════════════════════════════════════════════════════════
⚠️⚠️⚠️ 严重风险警示 ⚠️⚠️⚠️
══════════════════════════════════════════════════════════════════════

本模块仅供学术研究与教育用途。它【不构成】任何投资建议、交易指导
或财务规划建议。

1. 资金损失风险：任何基于概率的分配方案都可能导致全部本金损失。
   Kelly 准则在理论上追求长期资本增长，但在有限样本下仍可能产生
   重大回撤甚至破产。

2. 模型风险：本引擎的概率估计依赖输入数据质量。错误概率、过时
   估计或未考虑的尾部风险都会导致分配方案严重失真。

3. 假设风险：Kelly 公式假设已知真实概率与无限可分投资。现实中
   概率为估计值，且存在最小下注单位、流动性约束、交易成本等。

4. 尾部风险：历史概率模式不保证未来结果。"黑天鹅"事件不在
   概率模型覆盖范围内，可能造成超出模型预期的损失。

5. 杠杆风险：Kelly 在高概率/高回报场景下可能建议超过本金的
   分配。本引擎默认使用 quarter-Kelly (0.25) 并施加集中度上限，
   但这【不能】消除风险。

使用者须自行承担一切决策风险。在将本引擎用于任何实际决策前，
请咨询持牌专业人士。
══════════════════════════════════════════════════════════════════════

理论基础：
    Kelly, J.L. (1956). "A New Interpretation of Information Rate."
        Bell System Technical Journal, 35(4), 917-926.
    Markowitz, H.M. (1952). "Portfolio Selection."
        The Journal of Finance, 7(1), 77-91.
    MacLean, L.C., Thorp, E.O. & Ziemba, W.T. (2010).
        "The Kelly Capital Growth Investment Criterion."
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class RiskTier(Enum):
    """风险分层。"""

    CONSERVATIVE = "conservative"  # 保守：极低 Kelly 分数
    BALANCED = "balanced"  # 平衡：低 Kelly 分数
    AGGRESSIVE = "aggressive"  # 进取：中 Kelly 分数
    EXTREME = "extreme"  # 极端：高 Kelly 分数（不推荐）


@dataclass
class AllocationLeg:
    """
    单个候选分配方案（一条"腿"）。

    Attributes:
        outcome_id: 对应结果 ID
        probability: 该结果发生的概率 [0,1]
        return_multiplier: 回报倍数（如 2.0 表示 1 倍回报）
        signal_strength: 信号强度 [0,1]
        confidence: 置信度 [0,1]
        flow_direction: 流向（upward/downward/stable）
    """

    outcome_id: str
    probability: float
    return_multiplier: float
    signal_strength: float = 0.5
    confidence: float = 0.7
    flow_direction: str = "stable"

    @property
    def expected_value(self) -> float:
        """期望价值 EV = p × (b − 1) − (1 − p)。"""
        b = self.return_multiplier - 1.0
        return self.probability * b - (1.0 - self.probability)

    @property
    def kelly_fraction_optimal(self) -> float:
        """最优 Kelly 分数 f* = (p·b − q) / b。"""
        b = self.return_multiplier - 1.0
        if b <= 0:
            return 0.0
        q = 1.0 - self.probability
        f = (self.probability * b - q) / b
        return max(0.0, f)


@dataclass
class AllocationResult:
    """单个结果的分配结果。"""

    outcome_id: str
    allocated_amount: float
    allocation_fraction: float  # 占总预算比例
    kelly_optimal: float
    kelly_applied: float  # 实际应用的 Kelly 分数
    expected_value: float
    risk_score: float  # [0,1]，越高越风险
    reasoning: str = ""

    def is_within_limit(self, max_fraction: float = 0.2) -> bool:
        return self.allocation_fraction <= max_fraction


@dataclass
class AllocationBundle:
    """完整分配方案。"""

    budget: float
    legs: list[AllocationResult] = field(default_factory=list)
    allocated_amount: float = 0.0
    unallocated_amount: float = 0.0
    risk_tier: RiskTier = RiskTier.BALANCED
    diversification_score: float = 0.0
    expected_total_value: float = 0.0
    max_concentration: float = 0.0
    warnings: list[str] = field(default_factory=list)

    @property
    def allocation_ratio(self) -> float:
        if self.budget <= 0:
            return 0.0
        return self.allocated_amount / self.budget

    def get_top_allocations(self, n: int = 5) -> list[AllocationResult]:
        return sorted(self.legs, key=lambda x: x.allocated_amount, reverse=True)[:n]

    def get_summary(self) -> dict[str, Any]:
        return {
            "budget": self.budget,
            "allocated": self.allocated_amount,
            "unallocated": self.unallocated_amount,
            "allocation_ratio": self.allocation_ratio,
            "risk_tier": self.risk_tier.value,
            "diversification": self.diversification_score,
            "expected_value": self.expected_total_value,
            "max_concentration": self.max_concentration,
            "n_legs": len(self.legs),
            "warnings": self.warnings,
        }


class AllocationEngine:
    """
    资源分配引擎 (L5)。

    流程：
        1. 三原则验证（信号对齐 · 非对称潜力 · 合理结构）
        2. Kelly 最优分数（默认 quarter-Kelly）
        3. 集中度约束（单票 ≤ max_concentration）
        4. Markowitz 再平衡（多样化比目标）
        5. 风险分层

    ════════════════════════════════════════════════════════════════
    ⚠️ 严重风险警示 ⚠️
    本引擎输出【仅供参考研究】，不构成投资建议。任何实际决策
    都可能导致本金全部损失。详见模块顶部完整警示。
    ════════════════════════════════════════════════════════════════
    """

    KELLY_FRACTION_DEFAULT = 0.25  # quarter-Kelly
    MAX_CONCENTRATION_DEFAULT = 0.20  # 单票上限 20%
    MIN_PROBABILITY = 0.05  # 概率过低不入选
    MIN_RETURN_MULTIPLIER = 1.1  # 回报过低不入选

    # 风险分层 Kelly 系数
    RISK_TIER_FRACTIONS = {
        RiskTier.CONSERVATIVE: 0.10,
        RiskTier.BALANCED: 0.25,
        RiskTier.AGGRESSIVE: 0.50,
        RiskTier.EXTREME: 1.00,  # 不推荐
    }

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}
        self.kelly_fraction = self.config.get("kelly_fraction", self.KELLY_FRACTION_DEFAULT)
        self.max_concentration = self.config.get(
            "max_concentration", self.MAX_CONCENTRATION_DEFAULT
        )
        self.min_probability = self.config.get("min_probability", self.MIN_PROBABILITY)
        self.min_return_multiplier = self.config.get(
            "min_return_multiplier", self.MIN_RETURN_MULTIPLIER
        )
        self.target_diversification = self.config.get("target_diversification", 0.6)

    # ------------------------------------------------------------------
    # 三原则验证
    # ------------------------------------------------------------------

    def validate_three_principles(self, leg: AllocationLeg) -> tuple[bool, str]:
        """
        三原则验证：
            1. 信号对齐：正流向
            2. 非对称潜力：正期望
            3. 合理结构：概率与回报合理
        """
        # 原则 1：信号对齐（正流向优先）
        if leg.flow_direction == "downward":
            return False, "流向向下，信号不对齐"

        # 原则 2：非对称潜力（正期望）
        if leg.expected_value <= 0:
            return False, f"期望值为负 ({leg.expected_value:.3f})"

        # 原则 3：合理结构
        if leg.probability < self.min_probability:
            return False, f"概率过低 ({leg.probability:.3f} < {self.min_probability})"
        if leg.return_multiplier < self.min_return_multiplier:
            return False, (
                f"回报倍数过低 ({leg.return_multiplier:.3f} " f"< {self.min_return_multiplier})"
            )

        return True, "通过三原则验证"

    # ------------------------------------------------------------------
    # Kelly 计算
    # ------------------------------------------------------------------

    def calculate_kelly(self, leg: AllocationLeg, fraction: float | None = None) -> float:
        """
        计算 Kelly 分数。

            f* = (p·b − q) / b
            f_applied = fraction × f*

        Args:
            leg: 候选方案
            fraction: Kelly 分数（默认用配置的 kelly_fraction）
        """
        frac = fraction if fraction is not None else self.kelly_fraction
        kelly_optimal = leg.kelly_fraction_optimal
        return frac * kelly_optimal

    # ------------------------------------------------------------------
    # 分配生成
    # ------------------------------------------------------------------

    def generate_allocation(
        self,
        budget: float,
        candidates: list[AllocationLeg],
        max_n: int = 10,
        risk_tier: RiskTier = RiskTier.BALANCED,
    ) -> AllocationBundle:
        """
        生成资源分配方案。

        Args:
            budget: 总预算
            candidates: 候选方案列表
            max_n: 最多分配方案数
            risk_tier: 风险分层
        """
        bundle = AllocationBundle(budget=budget, risk_tier=risk_tier)
        bundle.warnings.append(
            "⚠️ 本分配方案仅供学术研究，不构成投资建议。" "实际决策可能导致本金全部损失。"
        )

        if budget <= 0:
            bundle.warnings.append("预算为零或负，无分配。")
            bundle.unallocated_amount = budget
            return bundle

        # 选择风险分层对应的 Kelly 系数
        tier_fraction = self.RISK_TIER_FRACTIONS.get(risk_tier, self.kelly_fraction)
        if risk_tier == RiskTier.EXTREME:
            bundle.warnings.append("⚠️ EXTREME 风险分层使用全 Kelly，破产风险显著，不推荐。")

        # 1. 三原则筛选
        valid_legs: list[tuple[AllocationLeg, str]] = []
        for leg in candidates:
            ok, reason = self.validate_three_principles(leg)
            if ok:
                valid_legs.append((leg, reason))

        if not valid_legs:
            bundle.warnings.append("无候选方案通过三原则验证。")
            bundle.unallocated_amount = budget
            return bundle

        # 2. 按期望价值排序，取前 max_n
        valid_legs.sort(key=lambda x: x[0].expected_value, reverse=True)
        valid_legs = valid_legs[:max_n]

        # 3. 计算每个 leg 的 Kelly 分配
        raw_fractions: dict[str, float] = {}
        for leg, _ in valid_legs:
            kelly_applied = self.calculate_kelly(leg, tier_fraction)
            # 用置信度调整
            kelly_applied *= leg.confidence
            raw_fractions[leg.outcome_id] = kelly_applied

        # 4. 归一化（如果总比例 > 1）
        total_raw = sum(raw_fractions.values())
        if total_raw > 1.0:
            raw_fractions = {k: v / total_raw for k, v in raw_fractions.items()}

        # 5. 集中度约束
        #    每条腿不超过 max_concentration；超额部分不重新分配（留给未分配）
        constrained_fractions = {
            k: min(v, self.max_concentration) for k, v in raw_fractions.items()
        }
        # 如果约束后总和 < 1，剩余部分计入未分配（不强制归一化到 1）
        # 如果约束后总和 > 1（多条腿都接近上限），才归一化
        total_constrained = sum(constrained_fractions.values())
        if total_constrained > 1.0:
            constrained_fractions = {
                k: v / total_constrained for k, v in constrained_fractions.items()
            }

        # 6. 生成分配结果
        leg_map = {leg.outcome_id: leg for leg, _ in valid_legs}
        for oid, fraction in constrained_fractions.items():
            leg = leg_map[oid]
            amount = fraction * budget
            kelly_optimal = leg.kelly_fraction_optimal
            kelly_applied = self.calculate_kelly(leg, tier_fraction) * leg.confidence
            ev = leg.expected_value * amount

            # 风险评分：高 Kelly + 低概率 = 高风险
            risk_score = min(
                kelly_optimal * (1.0 - leg.probability) + (1.0 - leg.confidence) * 0.5,
                1.0,
            )

            bundle.legs.append(
                AllocationResult(
                    outcome_id=oid,
                    allocated_amount=amount,
                    allocation_fraction=fraction,
                    kelly_optimal=kelly_optimal,
                    kelly_applied=kelly_applied,
                    expected_value=ev,
                    risk_score=risk_score,
                    reasoning=f"quarter-Kelly×confidence, EV={leg.expected_value:.3f}",
                )
            )

        bundle.allocated_amount = sum(leg.allocated_amount for leg in bundle.legs)
        bundle.unallocated_amount = budget - bundle.allocated_amount
        bundle.expected_total_value = sum(leg.expected_value for leg in bundle.legs)
        bundle.max_concentration = max(
            (leg.allocation_fraction for leg in bundle.legs), default=0.0
        )

        # 多样化评分
        bundle.diversification_score = self._calculate_diversification(bundle.legs)

        return bundle

    def _calculate_diversification(self, legs: list[AllocationResult]) -> float:
        """
        多样化评分（基于 Herfindahl 指数的逆）。
            HHI = Σ(f_i²)，越高越集中
            Diversification = 1 - HHI
        """
        if not legs:
            return 0.0
        hhi = sum(leg.allocation_fraction**2 for leg in legs)
        return max(0.0, 1.0 - hhi)

    # ------------------------------------------------------------------
    # Markowitz 再平衡
    # ------------------------------------------------------------------

    def optimize_portfolio(
        self,
        bundle: AllocationBundle,
        target_diversification: float | None = None,
    ) -> AllocationBundle:
        """
        Markowitz 再平衡：调整分配使多样化达到目标。

        策略：从最集中的腿中转移部分到其他腿，提升多样化。
        """
        target = target_diversification or self.target_diversification

        if not bundle.legs or bundle.diversification_score >= target:
            return bundle

        # 简化再平衡：将超过平均分配的部分削减， redistribute
        n = len(bundle.legs)
        if n <= 1:
            return bundle

        avg_fraction = 1.0 / n
        # 计算每条腿需要调整的量
        adjustments: dict[str, float] = {}
        surplus = 0.0
        for leg in bundle.legs:
            if leg.allocation_fraction > avg_fraction:
                excess = leg.allocation_fraction - avg_fraction
                # 削减 50% 的超额部分
                cut = excess * 0.5
                adjustments[leg.outcome_id] = -cut
                surplus += cut
            else:
                # 接收方
                deficit = avg_fraction - leg.allocation_fraction
                adjustments[leg.outcome_id] = deficit * 0.5  # 待补充

        # 分配 surplus 到接收方
        receivers = {oid: adj for oid, adj in adjustments.items() if adj > 0}
        total_receiver_demand = sum(receivers.values())
        if total_receiver_demand > 0 and surplus > 0:
            scale = min(surplus / total_receiver_demand, 1.0)
            for oid in receivers:
                adjustments[oid] *= scale
        else:
            # 无接收方，把 surplus 留给未分配
            bundle.unallocated_amount += surplus * bundle.budget

        # 应用调整
        for leg in bundle.legs:
            adj = adjustments.get(leg.outcome_id, 0.0)
            new_fraction = max(0.0, leg.allocation_fraction + adj)
            leg.allocation_fraction = new_fraction
            leg.allocated_amount = new_fraction * bundle.budget

        # 重新归一化
        total = sum(leg.allocation_fraction for leg in bundle.legs)
        if total > 0:
            for leg in bundle.legs:
                leg.allocation_fraction = leg.allocation_fraction / total
                leg.allocated_amount = leg.allocation_fraction * bundle.budget

        bundle.allocated_amount = sum(leg.allocated_amount for leg in bundle.legs)
        bundle.unallocated_amount = bundle.budget - bundle.allocated_amount
        bundle.diversification_score = self._calculate_diversification(bundle.legs)
        bundle.max_concentration = max(
            (leg.allocation_fraction for leg in bundle.legs), default=0.0
        )

        return bundle


__all__ = [
    "RiskTier",
    "AllocationLeg",
    "AllocationResult",
    "AllocationBundle",
    "AllocationEngine",
]
