"""
EDP V2.0 最小使用示例（中性场景）

本示例仅用"天气预测"这一完全中性的场景，演示 EDP 的最小可用流程。
更丰富的场景演示见 examples/notebooks/ 下的 .ipynb。

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
)


def example_minimal_weather():
    """最小示例：明天是否下雨（两结果，完全中性场景）。"""
    print("=" * 70)
    print("最小示例：明天是否下雨（中性场景演示）")
    print("=" * 70)

    domain = GenericDomain([
        Outcome("rain", "下雨"),
        Outcome("no_rain", "不下雨"),
    ])
    edp = EDP(domain)
    result = edp.analyze(
        evidence=[
            Evidence("weather_model", "model", {"probability": 0.72},
                     outcome_id="rain", confidence=0.8),
            Evidence("satellite", "sensor", {"probability": 0.68},
                     outcome_id="rain", confidence=0.9),
            Evidence("historical", "model", {"probability": 0.60},
                     outcome_id="rain", confidence=0.5),
        ],
        budget=1000,
    )

    print(f"\n摘要: {result['summary']}")
    print(f"概率: {{'rain': {result['probabilities']['rain']:.3f}, "
          f"'no_rain': {result['probabilities']['no_rain']:.3f}}}")
    if result["assessment"]:
        a = result["assessment"]
        print(f"共识度: {a.consensus_score:.3f} | 稳定性: {a.stability.value}")
    print(f"保形预测集 (覆盖率≥{result['prediction_set'].coverage_target:.0%}): "
          f"{result['prediction_set'].prediction_set}")
    print(f"\n风险警示:")
    for w in result["warnings"]:
        print(f"  {w}")


def example_online_aggregation():
    """在线聚合演示（模型融合，中性数值预测）。"""
    print("\n" + "=" * 70)
    print("在线聚合演示：多模型数值融合（ML-Poly）")
    print("=" * 70)

    agg = OnlineAggregator({"algorithm": "mlpoly"})
    agg.initialize(["model_a", "model_b", "model_c"])

    import random
    random.seed(42)
    for t in range(50):
        actual = 0.6 + 0.01 * t
        preds = {
            "model_a": actual + random.gauss(0, 0.02),
            "model_b": 0.5,
            "model_c": actual + random.gauss(0, 0.1),
        }
        agg.predict(preds)
        agg.update(preds, actual)

    weights = agg.get_weights()
    print(f"\n最终权重（model_a 应最高）:")
    for sid, w in sorted(weights.items(), key=lambda x: -x[1]):
        print(f"  {sid}: {w:.3f}")


if __name__ == "__main__":
    print("EDP V2.0 — 期望域感知方法（Expectation Domain Perception Method）")
    print("通用全域概率态势感知框架")
    print()
    print("⚠️  仅供学术研究与教育用途，不构成任何投资或决策建议。")
    print()

    example_minimal_weather()
    example_online_aggregation()

    print("\n" + "=" * 70)
    print("更丰富的场景演示见 examples/notebooks/ 下的 .ipynb")
    print("EDP V2.0 仅供学术研究，不构成任何决策建议。")
    print("=" * 70)
