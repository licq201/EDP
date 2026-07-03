"""
EDP - 期望域感知方法 (Expectation Domain Perception Method) V2.0
预测评估与校准引擎 (Layer 6: Calibration)

本模块实现 EDP 预测质量的评估与校准：
    - Brier Score + 分解 (REL − RES + UNC)
    - Log Score
    - CRPS（连续预测）
    - 校准曲线（预测概率 vs 实际频率）
    - 长期表现追踪

用途：
    - 回测 EDP 预测质量
    - 比较不同配置
    - 校准源可靠性
    - 自动调整融合权重

理论基础：
    Brier, G.W. (1950). "Verification of Forecasts Expressed in Terms
        of Probability." Monthly Weather Review, 78(1), 1-3.
    Gneiting, T. & Raftery, A.E. (2007). "Strictly Proper Scoring Rules,
        Prediction, and Estimation." Journal of the American
        Statistical Association, 102(477), 359-378.

⚠️ 风险警示 ⚠️
    本模块仅供学术研究与教育用途。校准结果为统计评估产物，
    不构成任何投资建议、决策建议或交易指导。历史表现不保证
    未来结果。使用者须自行承担一切决策风险。
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any


@dataclass
class PredictionRecord:
    """单次预测记录。"""

    timestamp: str
    predicted_probabilities: dict[str, float]
    actual_outcome: str
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def predicted_top_outcome(self) -> str:
        if not self.predicted_probabilities:
            return ""
        return max(self.predicted_probabilities.items(), key=lambda x: x[1])[0]

    @property
    def is_top1_correct(self) -> bool:
        return self.predicted_top_outcome == self.actual_outcome

    @property
    def predicted_actual_probability(self) -> float:
        return self.predicted_probabilities.get(self.actual_outcome, 0.0)


class CalibrationEngine:
    """
    预测评估与校准引擎 (L6)。

    功能：
        - evaluate():                 单次预测评估
        - brier_decomposition():       BS = REL − RES + UNC
        - calibration_curve():         预测概率 vs 实际频率
        - log_score():                 对数得分
        - crps():                      连续预测 CRPS
        - long_term_performance():     长期表现统计

    ⚠️ 本引擎仅供学术研究，输出不构成任何决策建议。
    """

    DEFAULT_N_BINS = 10

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}
        self.n_bins = self.config.get("n_bins", self.DEFAULT_N_BINS)
        self.history: list[PredictionRecord] = []

    # ------------------------------------------------------------------
    # 单次评估
    # ------------------------------------------------------------------

    def evaluate(
        self,
        predictions: dict[str, float],
        actual_outcome: str,
        timestamp: str | None = None,
    ) -> dict[str, Any]:
        """
        单次预测评估。

        Returns:
            brier_score:         Brier 分数（越低越好）
            log_score:           对数得分（越低越好）
            top1_correct:        Top-1 是否正确
            actual_probability:  实际结果的预测概率
        """
        from datetime import datetime

        ts = timestamp or datetime.now().isoformat()
        record = PredictionRecord(
            timestamp=ts,
            predicted_probabilities=dict(predictions),
            actual_outcome=actual_outcome,
        )
        self.history.append(record)

        brier = self._compute_brier(predictions, actual_outcome)
        log_s = self._compute_log_score(predictions, actual_outcome)
        actual_prob = predictions.get(actual_outcome, 0.0)

        return {
            "brier_score": brier,
            "log_score": log_s,
            "top1_correct": record.is_top1_correct,
            "actual_probability": actual_prob,
            "timestamp": ts,
        }

    @staticmethod
    def _compute_brier(
        predictions: dict[str, float], actual_outcome: str
    ) -> float:
        """Brier Score: BS = (1/N) Σ(f_t − o_t)²。"""
        n = len(predictions)
        if n == 0:
            return 0.0
        total = 0.0
        for outcome, prob in predictions.items():
            actual = 1.0 if outcome == actual_outcome else 0.0
            total += (prob - actual) ** 2
        return total / n

    @staticmethod
    def _compute_log_score(
        predictions: dict[str, float], actual_outcome: str
    ) -> float:
        """
        Log Score: LS = −[y·log(p) + (1−y)·log(1−p)]
        对极端错误惩罚更重。
        """
        eps = 1e-10
        p = max(eps, min(1 - eps, predictions.get(actual_outcome, 0.0)))
        return -math.log(p)

    # ------------------------------------------------------------------
    # Brier 分解
    # ------------------------------------------------------------------

    def brier_decomposition(
        self,
        history: list[tuple[float, float]] | None = None,
        n_bins: int | None = None,
    ) -> dict[str, float]:
        """
        Brier 分解：BS = REL − RES + UNC

            REL（可靠性）= (1/N) Σ_k n_k(f̄_k − ō_k)²  — 越小越好
            RES（分辨力）= (1/N) Σ_k n_k(ō_k − ō)²    — 越大越好
            UNC（不确定性）= ō(1−ō)

        Args:
            history: [(predicted_prob, actual_outcome(0/1)), ...]
                     若为 None，使用内部累积历史
            n_bins: 分箱数
        """
        if history is None:
            history = self._extract_binary_history()

        if not history:
            return {
                "brier_score": 0.0,
                "reliability": 0.0,
                "resolution": 0.0,
                "uncertainty": 0.0,
                "net_score": 0.0,
            }

        bins = n_bins or self.n_bins
        n_total = len(history)
        overall_actual = sum(h[1] for h in history) / n_total
        uncertainty = overall_actual * (1.0 - overall_actual)

        # 分箱
        bin_data: dict[int, list[tuple[float, float]]] = {}
        for pred, actual in history:
            bin_idx = min(int(pred * bins), bins - 1)
            bin_data.setdefault(bin_idx, []).append((pred, actual))

        reliability = 0.0
        resolution = 0.0
        brier_total = 0.0

        for bin_idx, records in bin_data.items():
            n_k = len(records)
            mean_forecast = sum(r[0] for r in records) / n_k
            mean_actual = sum(r[1] for r in records) / n_k

            reliability += n_k * (mean_forecast - mean_actual) ** 2
            resolution += n_k * (mean_actual - overall_actual) ** 2

            for pred, actual in records:
                brier_total += (pred - actual) ** 2

        reliability /= n_total
        resolution /= n_total
        brier_score = brier_total / n_total
        net_score = resolution - reliability  # 越大越好（分辨力减去不可靠性）

        return {
            "brier_score": brier_score,
            "reliability": reliability,
            "resolution": resolution,
            "uncertainty": uncertainty,
            "net_score": net_score,
        }

    def _extract_binary_history(self) -> list[tuple[float, float]]:
        """从内部历史提取二分类历史（实际结果的预测概率 vs 0/1）。"""
        history: list[tuple[float, float]] = []
        for record in self.history:
            actual_prob = record.predicted_actual_probability
            history.append((actual_prob, 1.0))
        return history

    # ------------------------------------------------------------------
    # 校准曲线
    # ------------------------------------------------------------------

    def calibration_curve(
        self,
        history: list[tuple[float, float]] | None = None,
        n_bins: int | None = None,
    ) -> list[tuple[float, float, int]]:
        """
        校准曲线数据点。

        Returns:
            [(predicted_mean, observed_freq, count), ...]
            完美校准：predicted_mean ≈ observed_freq
        """
        if history is None:
            history = self._extract_binary_history()

        if not history:
            return []

        bins = n_bins or self.n_bins
        bin_data: dict[int, list[tuple[float, float]]] = {}

        for pred, actual in history:
            bin_idx = min(int(pred * bins), bins - 1)
            bin_data.setdefault(bin_idx, []).append((pred, actual))

        curve: list[tuple[float, float, int]] = []
        for bin_idx in sorted(bin_data.keys()):
            records = bin_data[bin_idx]
            n_k = len(records)
            mean_pred = sum(r[0] for r in records) / n_k
            obs_freq = sum(r[1] for r in records) / n_k
            curve.append((mean_pred, obs_freq, n_k))

        return curve

    # ------------------------------------------------------------------
    # CRPS（连续预测）
    # ------------------------------------------------------------------

    @staticmethod
    def crps(
        forecast_cdf: list[tuple[float, float]],
        actual_value: float,
    ) -> float:
        """
        连续预测的 CRPS：
            CRPS = ∫[F(x) − 𝟙(x≥y)]² dx

        Args:
            forecast_cdf: [(x, F(x)), ...] 累积分布函数采样点
            actual_value: 实际值 y
        """
        if not forecast_cdf:
            return 0.0

        sorted_cdf = sorted(forecast_cdf, key=lambda p: p[0])
        total = 0.0

        for i in range(len(sorted_cdf) - 1):
            x_i, f_i = sorted_cdf[i]
            x_next, _ = sorted_cdf[i + 1]
            dx = x_next - x_i
            if dx <= 0:
                continue
            indicator = 1.0 if x_i >= actual_value else 0.0
            total += (f_i - indicator) ** 2 * dx

        return total

    # ------------------------------------------------------------------
    # 长期表现
    # ------------------------------------------------------------------

    def long_term_performance(self) -> dict[str, Any]:
        """长期表现统计。"""
        if not self.history:
            return {
                "total_predictions": 0,
                "top1_accuracy": 0.0,
                "avg_brier": 0.0,
                "avg_log_score": 0.0,
                "avg_actual_probability": 0.0,
            }

        n = len(self.history)
        top1_correct = sum(1 for r in self.history if r.is_top1_correct)
        brier_scores = [
            self._compute_brier(r.predicted_probabilities, r.actual_outcome)
            for r in self.history
        ]
        log_scores = [
            self._compute_log_score(r.predicted_probabilities, r.actual_outcome)
            for r in self.history
        ]
        actual_probs = [r.predicted_actual_probability for r in self.history]

        # Brier 分解
        binary_history = self._extract_binary_history()
        decomp = self.brier_decomposition(binary_history)

        return {
            "total_predictions": n,
            "top1_accuracy": top1_correct / n,
            "avg_brier": sum(brier_scores) / n,
            "avg_log_score": sum(log_scores) / n,
            "avg_actual_probability": sum(actual_probs) / n,
            "brier_decomposition": decomp,
        }

    def reset(self) -> None:
        """清空历史。"""
        self.history.clear()


__all__ = [
    "PredictionRecord",
    "CalibrationEngine",
]
