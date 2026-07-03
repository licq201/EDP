"""
EDP V2.0 测试套件 — 概率引擎与顶层接口

⚠️ 本测试仅供学术研究验证，不构成任何决策建议。
"""

import sys
import os
from datetime import datetime, timedelta

# 将 src/python 加入路径（包名 edp）
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src", "python"))

# 以 edp 包名加载
import importlib.util
_spec = importlib.util.spec_from_file_location(
    "edp",
    os.path.join(os.path.dirname(__file__), "..", "..", "src", "python", "__init__.py"),
    submodule_search_locations=[os.path.join(os.path.dirname(__file__), "..", "..", "src", "python")],
)
edp_module = importlib.util.module_from_spec(_spec)
sys.modules["edp"] = edp_module
_spec.loader.exec_module(edp_module)

from edp import (
    EDP,
    GenericDomain,
    Outcome,
    Quote,
    Evidence,
    Snapshot,
    EventGraph,
    ProbabilityEngine,
    OnlineAggregator,
    FlowAmplificationEngine,
    DomainAwarenessEngine,
    AllocationEngine,
    AllocationLeg,
    CalibrationEngine,
    BayesianPrior,
    FlowDirection,
    RiskTier,
)


# ----------------------------------------------------------------------
# Layer 0: 核心数据类型
# ----------------------------------------------------------------------

def test_outcome_creation():
    o = Outcome(id="a", label="结果A")
    assert o.id == "a"
    assert o.label == "结果A"
    assert o.metadata == {}


def test_quote_to_probability():
    # decimal_odds
    q = Quote(outcome_id="a", value=2.0, signal_type="decimal_odds")
    assert abs(q.to_probability() - 0.5) < 1e-6
    # probability
    q = Quote(outcome_id="a", value=0.7, signal_type="probability")
    assert abs(q.to_probability() - 0.7) < 1e-6
    # percentage
    q = Quote(outcome_id="a", value=75.0, signal_type="percentage")
    assert abs(q.to_probability() - 0.75) < 1e-6


def test_evidence_extract_probability():
    e = Evidence(id="e1", source_type="model", content={"probability": 0.8})
    assert abs(e.extract_probability() - 0.8) < 1e-6
    e = Evidence(id="e2", source_type="nlp", content={"direction": "upward"})
    assert abs(e.extract_probability() - 0.65) < 1e-6
    e = Evidence(id="e3", source_type="nlp", content={"direction": "downward"})
    assert abs(e.extract_probability() - 0.35) < 1e-6


def test_snapshot_validation():
    s = Snapshot(timestamp=datetime.now(), probabilities={"a": 0.5, "b": 0.5})
    assert s.validate() is True
    s = Snapshot(timestamp=datetime.now(), probabilities={"a": 0.3, "b": 0.3})
    assert s.validate() is False


def test_event_graph_chain():
    g = EventGraph.chain(["a", "b", "c"])
    assert g.get_adjacent("a") == ["b"]
    assert set(g.get_adjacent("b")) == {"a", "c"}
    assert g.get_adjacent("c") == ["b"]


def test_event_graph_fully_connected():
    g = EventGraph.fully_connected(["a", "b", "c"])
    assert set(g.get_adjacent("a")) == {"b", "c"}
    assert set(g.get_adjacent("b")) == {"a", "c"}


def test_generic_domain():
    domain = GenericDomain([Outcome("a", "A"), Outcome("b", "B")])
    outcomes = domain.get_outcomes()
    assert len(outcomes) == 2
    g = domain.build_event_graph(outcomes)
    assert "a" in g.get_adjacent("b")
    prior = domain.get_prior()
    assert abs(prior["a"] - 0.5) < 1e-6


# ----------------------------------------------------------------------
# Layer 1-3: 概率引擎
# ----------------------------------------------------------------------

def test_shin_normalization():
    engine = ProbabilityEngine()
    # 报价 2.0 / 2.0 → 概率 0.5 / 0.5
    result = engine.calculate_true_probability({"a": 2.0, "b": 2.0})
    assert abs(result.true_probabilities["a"] - 0.5) < 0.01
    assert abs(result.true_probabilities["b"] - 0.5) < 0.01
    assert abs(sum(result.true_probabilities.values()) - 1.0) < 1e-6


def test_shin_with_margin():
    engine = ProbabilityEngine()
    # 带边际的报价：1.5 / 3.0 / 6.0
    result = engine.calculate_true_probability({"a": 1.5, "b": 3.0, "c": 6.0})
    assert result.market_margin > 0  # 存在边际
    assert abs(sum(result.true_probabilities.values()) - 1.0) < 1e-6
    # a 概率最高
    assert result.true_probabilities["a"] > result.true_probabilities["b"]
    assert result.true_probabilities["b"] > result.true_probabilities["c"]


def test_bayesian_update():
    engine = ProbabilityEngine()
    prior = BayesianPrior(alpha=1.0, beta=1.0)  # 均匀先验
    posterior = engine.bayesian_update(prior, evidence_successes=7, evidence_trials=10)
    # 后验均值应接近 0.7
    assert 0.6 < posterior.expected_probability < 0.8
    assert posterior.credible_interval[0] < posterior.expected_probability
    assert posterior.credible_interval[1] > posterior.expected_probability


def test_flow_analysis():
    engine = ProbabilityEngine()
    t0 = datetime.now()
    t1 = t0 + timedelta(hours=1)
    s0 = Snapshot(timestamp=t0, probabilities={"a": 0.5, "b": 0.5})
    s1 = Snapshot(timestamp=t1, probabilities={"a": 0.6, "b": 0.4})
    report = engine.analyze_flow(s0, s1)
    assert len(report.flows) == 2
    a_flow = next(f for f in report.flows if f.outcome == "a")
    assert a_flow.direction == FlowDirection.UPWARD
    assert abs(a_flow.flow_pp - 10.0) < 0.01  # 0.6 - 0.5 = 0.1 = 10pp


def test_glicko2_rating():
    engine = ProbabilityEngine()
    engine.update_glicko_rating("team_a", [(1.0, 1500.0, 200.0)])  # 胜
    rating = engine.glicko_ratings["team_a"]
    assert rating.rating > 1500.0  # 胜后评分上升
    assert rating.games_played == 1


# ----------------------------------------------------------------------
# Layer 2: 在线聚合
# ----------------------------------------------------------------------

def test_online_aggregator_mlpoly():
    agg = OnlineAggregator({"algorithm": "mlpoly"})
    agg.initialize(["m1", "m2", "m3"])
    # m1 总是更准确
    for t in range(20):
        preds = {"m1": 0.7, "m2": 0.5, "m3": 0.3}
        agg.predict(preds)
        agg.update(preds, 0.7)  # 实际值 0.7
    weights = agg.get_weights()
    assert weights["m1"] > weights["m2"]
    assert weights["m2"] > weights["m3"]


def test_online_aggregator_ewa():
    agg = OnlineAggregator({"algorithm": "ewa", "eta": 2.0})
    agg.initialize(["a", "b"])
    for t in range(10):
        preds = {"a": 0.9, "b": 0.1}
        agg.predict(preds)
        agg.update(preds, 0.9)
    weights = agg.get_weights()
    assert weights["a"] > weights["b"]


# ----------------------------------------------------------------------
# Layer 3: 流向倍增
# ----------------------------------------------------------------------

def test_flow_amplification():
    engine = ProbabilityEngine()
    flow_engine = FlowAmplificationEngine()
    t0 = datetime.now()
    t1 = t0 + timedelta(hours=1)
    s0 = Snapshot(timestamp=t0, probabilities={"a": 0.3, "b": 0.7})
    s1 = Snapshot(timestamp=t1, probabilities={"a": 0.5, "b": 0.5})
    flow_report = engine.analyze_flow(s0, s1)
    graph = EventGraph.chain(["a", "b"])
    amp_report = flow_engine.calculate_amplification(
        flow_report, {"a": 0.5, "b": 0.5}, graph
    )
    assert len(amp_report.amplifications) == 2
    a_amp = next(a for a in amp_report.amplifications if a.outcome == "a")
    # a 流向上升（0.3→0.5），应有正向倍增
    assert a_amp.base_flow_pp > 0


# ----------------------------------------------------------------------
# Layer 4: 全域感知
# ----------------------------------------------------------------------

def test_domain_awareness():
    from edp import EvidenceSource, EvidenceType, SourceReliability
    engine = DomainAwarenessEngine()
    now = datetime.now()
    sources = [
        EvidenceSource("s1", EvidenceType.MODEL, SourceReliability.B, now,
                       {"probability": 0.7}, confidence=0.8),
        EvidenceSource("s2", EvidenceType.SENSOR, SourceReliability.A, now,
                       {"probability": 0.68}, confidence=0.9),
        EvidenceSource("s3", EvidenceType.MODEL, SourceReliability.C, now,
                       {"probability": 0.65}, confidence=0.5),
    ]
    assessment = engine.assess_situation(sources)
    assert 0.6 < assessment.aggregate_probability < 0.8
    assert assessment.consensus_score > 0.5  # 三源接近，共识高
    assert assessment.source_count == 3


# ----------------------------------------------------------------------
# Layer 5: 资源分配
# ----------------------------------------------------------------------

def test_allocation_three_principles():
    engine = AllocationEngine()
    # 满足三原则：正向流向 + 正期望 + 合理结构
    leg = AllocationLeg(
        outcome_id="a", probability=0.6, return_multiplier=2.0,
        flow_direction="upward", confidence=0.8,
    )
    ok, _ = engine.validate_three_principles(leg)
    assert ok is True
    # 不满足：负期望
    leg = AllocationLeg(
        outcome_id="a", probability=0.3, return_multiplier=1.5,
        flow_direction="upward", confidence=0.8,
    )
    ok, _ = engine.validate_three_principles(leg)
    assert ok is False


def test_allocation_generation():
    engine = AllocationEngine()
    candidates = [
        AllocationLeg("a", 0.6, 2.0, flow_direction="upward", confidence=0.8),
        AllocationLeg("b", 0.5, 2.2, flow_direction="upward", confidence=0.7),
    ]
    bundle = engine.generate_allocation(1000, candidates)
    assert bundle.budget == 1000
    assert len(bundle.warnings) > 0  # 应有风险警示
    assert any("不构成投资建议" in w for w in bundle.warnings)


def test_allocation_concentration_limit():
    engine = AllocationEngine({"max_concentration": 0.2})
    candidates = [
        AllocationLeg("a", 0.9, 3.0, flow_direction="upward", confidence=0.9),
        AllocationLeg("b", 0.5, 2.0, flow_direction="upward", confidence=0.7),
        AllocationLeg("c", 0.5, 2.0, flow_direction="upward", confidence=0.7),
        AllocationLeg("d", 0.5, 2.0, flow_direction="upward", confidence=0.7),
        AllocationLeg("e", 0.5, 2.0, flow_direction="upward", confidence=0.7),
    ]
    bundle = engine.generate_allocation(1000, candidates)
    for leg in bundle.legs:
        assert leg.allocation_fraction <= 0.21  # 允许归一化后小幅浮动


# ----------------------------------------------------------------------
# Layer 6: 校准
# ----------------------------------------------------------------------

def test_calibration_brier():
    calib = CalibrationEngine()
    result = calib.evaluate({"a": 0.7, "b": 0.3}, "a")
    assert 0 <= result["brier_score"] <= 1
    assert result["top1_correct"] is True


def test_calibration_brier_decomposition():
    calib = CalibrationEngine()
    history = [(0.7, 1), (0.3, 0), (0.8, 1), (0.4, 0), (0.6, 1), (0.2, 0)]
    decomp = calib.brier_decomposition(history)
    assert "reliability" in decomp
    assert "resolution" in decomp
    assert "uncertainty" in decomp
    assert decomp["brier_score"] >= 0


def test_calibration_curve():
    calib = CalibrationEngine()
    history = [(0.1, 0), (0.3, 0), (0.5, 1), (0.7, 1), (0.9, 1)]
    curve = calib.calibration_curve(history, n_bins=5)
    assert len(curve) > 0
    for pred, obs, count in curve:
        assert 0 <= pred <= 1
        assert 0 <= obs <= 1
        assert count > 0


# ----------------------------------------------------------------------
# 顶层 EDP 接口
# ----------------------------------------------------------------------

def test_edp_analyze_two_outcomes():
    domain = GenericDomain([Outcome("rain", "下雨"), Outcome("no_rain", "不下雨")])
    edp = EDP(domain)
    result = edp.analyze(
        evidence=[
            Evidence("m1", "model", {"probability": 0.72}, confidence=0.8),
            Evidence("s1", "sensor", {"probability": 0.68}, confidence=0.9),
            Evidence("h1", "model", {"probability": 0.60}, confidence=0.5),
        ],
        budget=1000,
    )
    assert "probabilities" in result
    assert "summary" in result
    assert "warnings" in result
    assert len(result["warnings"]) > 0  # 应有风险警示
    assert abs(sum(result["probabilities"].values()) - 1.0) < 0.05


def test_edp_analyze_with_market_quotes():
    domain = GenericDomain([Outcome("a", "A"), Outcome("b", "B"), Outcome("c", "C")])
    edp = EDP(domain)
    result = edp.analyze(
        raw_data={"a": 1.5, "b": 3.0, "c": 6.0},
        budget=5000,
        return_multipliers={"a": 1.5, "b": 3.0, "c": 6.0},
    )
    probs = result["probabilities"]
    assert probs["a"] > probs["b"]
    assert probs["b"] > probs["c"]
    assert abs(sum(probs.values()) - 1.0) < 0.01


def test_edp_version():
    assert edp_module.__version__ == "2.0.0"


def test_edp_warnings_contain_risk_disclaimer():
    domain = GenericDomain([Outcome("a", "A"), Outcome("b", "B")])
    edp = EDP(domain)
    result = edp.analyze(evidence=[Evidence("e1", "model", {"probability": 0.6})])
    warning_text = " ".join(result["warnings"])
    assert "不构成" in warning_text or "学术研究" in warning_text


if __name__ == "__main__":
    # 手动运行所有测试
    test_funcs = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    passed = 0
    failed = 0
    for func in test_funcs:
        try:
            func()
            print(f"PASS  {func.__name__}")
            passed += 1
        except Exception as e:
            print(f"FAIL  {func.__name__}: {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed, {len(test_funcs)} total")
    sys.exit(0 if failed == 0 else 1)
