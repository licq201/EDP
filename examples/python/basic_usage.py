"""
EDP V2.0 基础使用示例

⚠️ 本示例仅供学术研究与教育用途，不构成任何投资建议或决策建议。
   实际决策可能导致损失，使用者须自行承担风险。

运行方式：
    cd /workspace
    PYTHONPATH=src/python python examples/python/basic_usage.py
"""

import os
import sys

# 将 src/python 加入路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src", "python"))

import importlib.util

_spec = importlib.util.spec_from_file_location(
    "edp",
    os.path.join(os.path.dirname(__file__), "..", "..", "src", "python", "__init__.py"),
    submodule_search_locations=[
        os.path.join(os.path.dirname(__file__), "..", "..", "src", "python")
    ],
)
edp_module = importlib.util.module_from_spec(_spec)
sys.modules["edp"] = edp_module
_spec.loader.exec_module(edp_module)

from edp import (
    EDP,
    GenericDomain,
    Outcome,
    Evidence,
    OnlineAggregator,
    CalibrationEngine,
    RiskTier,
)


def example_1_two_outcomes():
    """示例 1：全域问题（两结果）— 天气预测。"""
    print("=" * 70)
    print("示例 1：全域问题（两结果）— 明天是否下雨")
    print("=" * 70)

    domain = GenericDomain([
        Outcome("rain", "下雨"),
        Outcome("no_rain", "不下雨"),
    ])
    edp = EDP(domain)
    result = edp.analyze(
        evidence=[
            Evidence("weather_model", "model", {"probability": 0.72}, confidence=0.8),
            Evidence("satellite", "sensor", {"probability": 0.68}, confidence=0.9),
            Evidence("historical", "model", {"probability": 0.60}, confidence=0.5),
        ],
        budget=1000,
    )

    print(f"\n摘要: {result['summary']}")
    print(f"概率: {result['probabilities']}")
    if result["assessment"]:
        a = result["assessment"]
        print(f"共识度: {a.consensus_score:.3f} | 稳定性: {a.stability.value}")
        print(f"融合方法: {a.fusion_method} | 来源数: {a.source_count}")
    print(f"\n风险警示:")
    for w in result["warnings"]:
        print(f"  {w}")


def example_2_market_quotes():
    """示例 2：市场报价 Shin 归一化。"""
    print("\n" + "=" * 70)
    print("示例 2：市场报价 Shin 归一化（三结果）")
    print("=" * 70)

    domain = GenericDomain([
        Outcome("a", "结果A"),
        Outcome("b", "结果B"),
        Outcome("c", "结果C"),
    ])
    edp = EDP(domain)
    # 小数报价：1.5 / 3.0 / 6.0（含市场边际）
    result = edp.analyze(
        raw_data={"a": 1.5, "b": 3.0, "c": 6.0},
        budget=5000,
        return_multipliers={"a": 1.5, "b": 3.0, "c": 6.0},
    )

    print(f"\n摘要: {result['summary']}")
    print(f"真实概率（Shin 归一化后）:")
    for oid, p in sorted(result["probabilities"].items(), key=lambda x: -x[1]):
        print(f"  {oid}: {p:.3f} ({p*100:.1f}%)")

    if result["allocation"].legs:
        print(f"\n分配方案（quarter-Kelly，仅供研究）:")
        for leg in result["allocation"].get_top_allocations():
            print(f"  {leg.outcome_id}: {leg.allocated_amount:.2f} "
                  f"({leg.allocation_fraction*100:.1f}%)")
        print(f"  未分配: {result['allocation'].unallocated_amount:.2f}")


def example_3_online_aggregation():
    """示例 3：在线专家聚合。"""
    print("\n" + "=" * 70)
    print("示例 3：在线专家聚合（ML-Poly 算法）")
    print("=" * 70)

    agg = OnlineAggregator({"algorithm": "mlpoly"})
    agg.initialize(["model_a", "model_b", "model_c"])

    # 模拟 50 个时间步：model_a 总是最准
    import random
    random.seed(42)
    for t in range(50):
        actual = 0.6 + 0.01 * t  # 趋势上升
        preds = {
            "model_a": actual + random.gauss(0, 0.02),  # 最准
            "model_b": 0.5,                              # 恒定，不准
            "model_c": actual + random.gauss(0, 0.1),    # 噪声大
        }
        agg.predict(preds)
        agg.update(preds, actual)

    weights = agg.get_weights()
    print(f"\n最终权重（model_a 应最高）:")
    for sid, w in sorted(weights.items(), key=lambda x: -x[1]):
        print(f"  {sid}: {w:.3f}")

    perf = agg.get_performance()
    print(f"\n各来源历史表现:")
    for sid, p in perf.items():
        print(f"  {sid}: avg_loss={p['avg_loss']:.4f}, weight={p['weight']:.3f}")


def example_4_calibration():
    """示例 4：预测校准与 Brier 分解。"""
    print("\n" + "=" * 70)
    print("示例 4：预测校准（Brier 分解）")
    print("=" * 70)

    calib = CalibrationEngine()

    # 模拟 30 次预测：预测概率 0.7 时，实际发生 70% 的情况
    import random
    random.seed(123)
    for i in range(30):
        pred_prob = 0.7
        actual = "a" if random.random() < pred_prob else "b"
        calib.evaluate({"a": pred_prob, "b": 1 - pred_prob}, actual)

    perf = calib.long_term_performance()
    print(f"\n长期表现:")
    print(f"  预测总数: {perf['total_predictions']}")
    print(f"  Top-1 准确率: {perf['top1_accuracy']:.3f}")
    print(f"  平均 Brier: {perf['avg_brier']:.4f}")

    decomp = perf["brier_decomposition"]
    print(f"\nBrier 分解 (BS = REL − RES + UNC):")
    print(f"  BS  (Brier 分数):     {decomp['brier_score']:.4f}")
    print(f"  REL (可靠性，越小越好): {decomp['reliability']:.4f}")
    print(f"  RES (分辨力，越大越好): {decomp['resolution']:.4f}")
    print(f"  UNC (不确定性):        {decomp['uncertainty']:.4f}")

    curve = calib.calibration_curve(n_bins=5)
    print(f"\n校准曲线（预测概率 vs 实际频率）:")
    print(f"  {'预测概率':>10} | {'实际频率':>10} | {'样本数':>6}")
    for pred, obs, count in curve:
        print(f"  {pred:>10.3f} | {obs:>10.3f} | {count:>6d}")


def example_5_custom_domain():
    """示例 5：自定义域适配器。"""
    print("\n" + "=" * 70)
    print("示例 5：自定义域适配器（五结果近似全域）")
    print("=" * 70)

    from edp import DomainAdapter, EventGraph, Quote

    class PriceDirectionDomain(DomainAdapter):
        """价格方向预测域：大跌/小跌/持平/小涨/大涨。"""

        def get_outcomes(self, context=None):
            return [
                Outcome("strong_down", "大跌"),
                Outcome("down", "小跌"),
                Outcome("flat", "持平"),
                Outcome("up", "小涨"),
                Outcome("strong_up", "大涨"),
            ]

        def build_event_graph(self, outcomes):
            # 有序链：大跌 ↔ 小跌 ↔ 持平 ↔ 小涨 ↔ 大涨
            return EventGraph.chain([o.id for o in outcomes])

        def normalize_signals(self, raw_data):
            # raw_data: {outcome_id: probability}
            quotes = []
            for oid, val in raw_data.items():
                quotes.append(Quote(outcome_id=oid, value=val, signal_type="probability"))
            return quotes

    domain = PriceDirectionDomain()
    edp = EDP(domain)
    result = edp.analyze(
        evidence=[
            Evidence("flow_1", "market", {"probability": 0.72}, confidence=0.85),
            Evidence("flow_2", "market", {"probability": 0.68}, confidence=0.80),
            Evidence("sentiment", "nlp", {"direction": "upward"}, confidence=0.60),
            Evidence("model", "model", {"probability": 0.65}, confidence=0.70),
        ],
        budget=10000,
        return_multipliers={
            "strong_up": 5.0, "up": 2.5, "flat": 1.8,
            "down": 3.0, "strong_down": 8.0,
        },
        risk_tier=RiskTier.CONSERVATIVE,
    )

    print(f"\n摘要: {result['summary']}")
    print(f"\n各结果概率:")
    for oid, p in sorted(result["probabilities"].items(), key=lambda x: -x[1]):
        print(f"  {oid:12s}: {p:.3f}")

    if result["flow"]:
        print(f"\n流向分析:")
        for f in result["flow"].flows:
            print(f"  {f.outcome:12s}: {f.flow_pp:+.2f}pp ({f.direction.value})")


if __name__ == "__main__":
    print("EDP V2.0 — 期望域感知方法（Expectation Domain Perception Method）")
    print("通用全域概率态势感知框架")
    print()
    print("⚠️  仅供学术研究与教育用途，不构成任何投资或决策建议。")
    print("    实际决策可能导致损失，使用者须自行承担风险。")
    print()

    example_1_two_outcomes()
    example_2_market_quotes()
    example_3_online_aggregation()
    example_4_calibration()
    example_5_custom_domain()

    print("\n" + "=" * 70)
    print("所有示例运行完毕。")
    print("EDP V2.0 仅供学术研究，不构成任何决策建议。")
    print("=" * 70)
