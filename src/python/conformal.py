"""
EDP - 期望域感知方法 (Expectation Domain Perception Method) V2.0
保形预测层 (Layer 7: Conformal Prediction)

本模块为 EDP 提供有限样本、分布无关的覆盖率保证——这是 2025 年概率
预测领域最重要的进展。与 Beta-Binomial 后验的渐近保证不同，保形预测
在任意分布、任意模型质量下都能给出可证明的覆盖率保证。

三种模式：
    - Split Conformal:     静态校准集，标准有限样本保证（需 exchangeability）
    - Adaptive CP (ACI):   在线自适应，分布漂移下长程覆盖率收敛到目标
                            （Zaffran et al. 2022, 2025 工业落地）
    - Aggregated ACI:      集成多学习率的 ACI，更稳健

分类预测集：    nonconformity = 1 − p(true_label)
                预测集 = {label : 1 − p(label) ≤ q̂_α}
                覆盖率 ≥ 1 − α（有限样本，任意分布）

ACI 更新（在线，分布漂移鲁棒）：
    α_t+1 = α_t + γ × (err_t − α)
    其中 err_t = 1{actual ∉ prediction_set_t}
    γ 为学习率；区间随近期覆盖率自适应伸缩

理论基础：
    Vovk, V., Gammerman, A. & Shafer, G. (2005). "Algorithmic Learning
        in a Random World." Springer.
    Lei, J. et al. (2013). "Distribution-Free Prediction Sets."
        JASA, 108(501), 279-288.
    Gibbs, I. & Candès, E. (2021). "Adaptive Conformal Inference
        Under Distribution Shift." NeurIPS.
    Zaffran, M. et al. (2022). "Adaptive Conformal Predictions for
        Time Series." ICML.

⚠️ 风险警示 ⚠️
    本模块仅供学术研究与教育用途。覆盖率保证为边际保证，不针对单点。
    分布漂移下的 ACI 保证为长程收敛，非逐点有限样本。不构成任何投资
    建议、决策建议或交易指导。使用者须自行承担一切决策风险。
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any


@dataclass
class ConformalConfig:
    """保形预测配置。"""

    alpha: float = 0.1  # 目标误覆盖率（1−α 为目标覆盖率，默认 90%）
    method: str = "split"  # split / aci / agaci
    aci_gamma: float = 0.01  # ACI 学习率
    agaci_gammas: tuple[float, ...] = (0.001, 0.01, 0.05, 0.1)  # AgACI 学习率集
    window_size: int | None = None  # 校准分数滑动窗口（None=全量）


@dataclass
class PredictionSet:
    """分类预测集结果。"""

    prediction_set: list[str]  # 包含的结果 ID（满足覆盖率保证）
    coverage_target: float  # 目标覆盖率 1−α
    threshold: float  # 使用的 nonconformity 分位数
    alpha_used: float  # 实际使用的 α（ACI 自适应后）
    is_empty: bool = False
    is_full: bool = False
    method: str = "split"
    confidence: float = 1.0

    @property
    def size(self) -> int:
        return len(self.prediction_set)

    def contains(self, outcome: str) -> bool:
        return outcome in self.prediction_set


@dataclass
class CalibrationRecord:
    """单次校准记录（predicted probs + actual outcome）。"""

    predictions: dict[str, float]
    actual: str

    def nonconformity(self) -> float:
        """nonconformity score = 1 − p(actual)。"""
        return 1.0 - self.predictions.get(self.actual, 0.0)


class ConformalEngine:
    """
    保形预测引擎 (L7)。

    提供三种模式：
        1. Split Conformal —— 离线校准，标准有限样本保证
        2. ACI            —— 在线，分布漂移鲁棒
        3. AgACI          —— 集成 ACI，更稳健

    用法（在线 ACI）：
        engine = ConformalEngine(ConformalConfig(method="aci"))
        for preds, actual in stream:
            pset = engine.predict(preds)        # 先预测
            engine.update(preds, actual)         # 后用真实值更新

    ⚠️ 本引擎仅供学术研究，输出不构成任何决策建议。
    """

    def __init__(self, config: ConformalConfig | None = None):
        self.config = config or ConformalConfig()
        if not (0.0 < self.config.alpha < 1.0):
            raise ValueError("alpha must be in (0, 1)")
        self.method = self.config.method

        # 校准集（Split Conformal）
        self.calibration_scores: list[float] = []

        # ACI 状态
        self._aci_alpha: float = self.config.alpha
        self._aci_errors: list[int] = []  # 1=未覆盖

        # AgACI 状态：每个 gamma 一个独立 ACI
        self._agaci_alphas: dict[float, float] = dict.fromkeys(
            self.config.agaci_gammas, self.config.alpha
        )
        self._agaci_weights: dict[float, float] = {
            g: 1.0 / len(self.config.agaci_gammas) for g in self.config.agaci_gammas
        }
        self._agaci_errors: dict[float, list[int]] = {g: [] for g in self.config.agaci_gammas}

        self.n_updates: int = 0

    # ------------------------------------------------------------------
    # 校准集管理
    # ------------------------------------------------------------------

    def calibrate(
        self,
        history: list[tuple[dict[str, float], str]],
    ) -> None:
        """用历史 (predictions, actual) 填充校准集（Split Conformal）。"""
        self.calibration_scores = []
        for preds, actual in history:
            rec = CalibrationRecord(preds, actual)
            self.calibration_scores.append(rec.nonconformity())

    def add_calibration_point(self, predictions: dict[str, float], actual: str) -> None:
        """添加单个校准点。"""
        rec = CalibrationRecord(predictions, actual)
        score = rec.nonconformity()
        self.calibration_scores.append(score)
        if self.config.window_size is not None:
            excess = len(self.calibration_scores) - self.config.window_size
            if excess > 0:
                self.calibration_scores = self.calibration_scores[excess:]

    # ------------------------------------------------------------------
    # 分位数计算
    # ------------------------------------------------------------------

    @staticmethod
    def _quantile(scores: list[float], alpha: float) -> float:
        """
        计算 (1−α) 分位数（带有限样本修正）。

        有限样本保证要求分位数取 ceil((n+1)(1−α))/n 处，确保覆盖率 ≥ 1−α。
        """
        if not scores:
            return 1.0  # 无校准数据：保守地接受所有
        sorted_scores = sorted(scores)
        n = len(sorted_scores)
        # 有限样本修正：取 ceil((n+1)(1-α)) 个，保证 P(score ≤ q̂) ≥ 1−α
        idx = math.ceil((n + 1) * (1.0 - alpha)) - 1
        idx = max(0, min(idx, n - 1))
        return sorted_scores[idx]

    # ------------------------------------------------------------------
    # 预测
    # ------------------------------------------------------------------

    def predict(self, predictions: dict[str, float]) -> PredictionSet:
        """
        生成预测集。

        对于分类：预测集 = {label : 1 − p(label) ≤ threshold}
        """
        if self.method == "split":
            return self._predict_split(predictions)
        elif self.method == "aci":
            return self._predict_aci(predictions)
        elif self.method == "agaci":
            return self._predict_agaci(predictions)
        raise ValueError(f"Unknown method: {self.method}")

    def _build_set(
        self,
        predictions: dict[str, float],
        threshold: float,
        alpha_used: float,
        method: str,
    ) -> PredictionSet:
        pred_set = [oid for oid, p in predictions.items() if (1.0 - p) <= threshold + 1e-12]
        return PredictionSet(
            prediction_set=pred_set,
            coverage_target=1.0 - alpha_used,
            threshold=threshold,
            alpha_used=alpha_used,
            is_empty=len(pred_set) == 0,
            is_full=len(pred_set) == len(predictions),
            method=method,
            confidence=1.0 - alpha_used,
        )

    def _predict_split(self, predictions: dict[str, float]) -> PredictionSet:
        threshold = self._quantile(self.calibration_scores, self.config.alpha)
        return self._build_set(predictions, threshold, self.config.alpha, "split")

    def _predict_aci(self, predictions: dict[str, float]) -> PredictionSet:
        threshold = self._quantile(self.calibration_scores, self._aci_alpha)
        return self._build_set(predictions, threshold, self._aci_alpha, "aci")

    def _predict_agaci(self, predictions: dict[str, float]) -> PredictionSet:
        """AgACI：按权重聚合各 ACI 的预测集（并集，按权重加权）。"""
        # 每个子 ACI 给出阈值
        sub_thresholds: list[tuple[float, float]] = []  # (threshold, weight)
        for gamma, alpha_g in self._agaci_alphas.items():
            thr = self._quantile(self.calibration_scores, alpha_g)
            w = self._agaci_weights[gamma]
            sub_thresholds.append((thr, w))

        # 加权阈值（保守取较高分位数的加权平均）
        total_w = sum(w for _, w in sub_thresholds)
        weighted_threshold = sum(t * w for t, w in sub_thresholds) / max(total_w, 1e-12)
        # AgACI 的有效 α 用加权平均
        weighted_alpha = sum(
            self._agaci_alphas[g] * self._agaci_weights[g] for g in self._agaci_alphas
        ) / max(total_w, 1e-12)
        return self._build_set(predictions, weighted_threshold, weighted_alpha, "agaci")

    # ------------------------------------------------------------------
    # 在线更新（ACI / AgACI）
    # ------------------------------------------------------------------

    def update(self, predictions: dict[str, float], actual: str) -> dict[str, Any]:
        """
        观测真实值后在线更新。

        Returns:
            covered:       实际值是否落在预测集内
            coverage_rate: 滚动覆盖率
            alpha:         更新后的 α（ACI）
        """
        pset = self.predict(predictions)
        covered = pset.contains(actual)
        err = 0 if covered else 1

        # 添加到校准集（供后续分位数计算）
        self.add_calibration_point(predictions, actual)
        self._aci_errors.append(err)
        self.n_updates += 1

        result: dict[str, Any] = {
            "covered": covered,
            "alpha": self._aci_alpha,
        }

        # ACI 更新：α_{t+1} = α_t + γ·(err − α_target)
        if self.method in ("aci", "agaci"):
            self._aci_alpha += self.config.aci_gamma * (err - self.config.alpha)
            self._aci_alpha = max(0.001, min(0.999, self._aci_alpha))
            result["alpha"] = self._aci_alpha

        # AgACI 更新每个子 ACI 与权重
        if self.method == "agaci":
            for gamma in self._agaci_alphas:
                sub_err = err  # 同一观测
                self._agaci_errors[gamma].append(sub_err)
                self._agaci_alphas[gamma] += gamma * (sub_err - self.config.alpha)
                self._agaci_alphas[gamma] = max(0.001, min(0.999, self._agaci_alphas[gamma]))

            # 权重更新：近期覆盖更好的 gamma 获得更高权重（softmax）
            self._update_agaci_weights()

        # 滚动覆盖率
        window = self._aci_errors[-100:]
        result["coverage_rate"] = 1.0 - (sum(window) / max(len(window), 1))
        return result

    def _update_agaci_weights(self) -> None:
        """根据近期覆盖表现更新各 gamma 权重（覆盖越接近目标越好）。"""
        target = 1.0 - self.config.alpha
        scores: dict[float, float] = {}
        for gamma, errs in self._agaci_errors.items():
            window = errs[-50:]
            if not window:
                rate = target
            else:
                rate = 1.0 - (sum(window) / len(window))
            # 偏离目标越远分数越低
            scores[gamma] = -abs(rate - target)

        # softmax
        max_s = max(scores.values())
        exp_s = {g: math.exp(2.0 * (s - max_s)) for g, s in scores.items()}
        total = sum(exp_s.values())
        self._agaci_weights = {g: v / total for g, v in exp_s.items()}

    # ------------------------------------------------------------------
    # 统计
    # ------------------------------------------------------------------

    def coverage_stats(self) -> dict[str, Any]:
        """覆盖率统计。"""
        if not self._aci_errors:
            return {"n_updates": 0, "empirical_coverage": None}
        window = self._aci_errors[-100:]
        return {
            "n_updates": self.n_updates,
            "empirical_coverage": 1.0 - (sum(window) / len(window)),
            "target_coverage": 1.0 - self.config.alpha,
            "current_alpha": self._aci_alpha,
            "calibration_size": len(self.calibration_scores),
            "method": self.method,
        }


__all__ = [
    "ConformalConfig",
    "PredictionSet",
    "CalibrationRecord",
    "ConformalEngine",
]
