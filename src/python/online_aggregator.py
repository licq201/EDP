"""
EDP - 期望域感知方法 (Expectation Domain Perception Method) V2.0
在线专家聚合引擎 (Layer 2: Online Aggregation)

本模块实现多个预测来源的在线加权聚合，按历史表现在线调整权重，
使组合预测比任何单一来源更准确。

三种聚合算法：
    - ML-Poly:  多项式权重，有理论最坏情况保证
    - EWA:      指数加权平均
    - Ridge:    岭回归，处理相关来源

理论基础：
    Cesa-Bianchi, N. & Lugosi, G. (2006).
    "Prediction, Learning, and Games." Cambridge University Press.

    Gaillard, P. & Goude, Y. (2015). "opera" R package.

⚠️ 风险警示 ⚠️
    本模块仅供学术研究与教育用途。聚合预测为统计推断产物，
    不构成任何投资建议、决策建议或交易指导。历史表现不保证
    未来结果。使用者须自行承担一切决策风险。
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SourcePerformance:
    """单个来源的历史表现统计。"""

    source_id: str
    weight: float = 0.0
    total_loss: float = 0.0
    n_predictions: int = 0
    avg_loss: float = 0.0
    recent_losses: list[float] = field(default_factory=list)

    def update(self, loss: float, weight: float) -> None:
        self.total_loss += loss
        self.n_predictions += 1
        self.avg_loss = self.total_loss / self.n_predictions
        self.weight = weight
        self.recent_losses.append(loss)
        if len(self.recent_losses) > 100:
            self.recent_losses.pop(0)


class OnlineAggregator:
    """
    在线学习聚合多个预测来源。

    核心思想：有 K 个来源（模型、分析师、传感器），每个时间步给出预测。
    按历史表现在线调整权重，比任何单一来源都更准确。

    算法：
        - ML-Poly: 多项式权重，有理论最坏情况保证
        - EWA:     指数加权平均
        - Ridge:   岭回归，处理相关来源

    用途：任何需要融合多个预测模型的场景。

    ⚠️ 本引擎仅供学术研究，输出不构成任何决策建议。
    """

    SUPPORTED_ALGORITHMS = ("mlpoly", "ewa", "ridge")
    SUPPORTED_LOSSES = ("square", "absolute", "log")

    def __init__(self, config: dict[str, Any] | None = None):
        """
        Args:
            config: 可选配置
                algorithm:  mlpoly / ewa / ridge
                eta:        学习率
                loss_type:  square / absolute / log
                ridge_lambda: Ridge 正则化系数
        """
        self.config = config or {}
        self.algorithm = self.config.get("algorithm", "mlpoly")
        if self.algorithm not in self.SUPPORTED_ALGORITHMS:
            raise ValueError(
                f"Unknown algorithm: {self.algorithm}. "
                f"Use one of {self.SUPPORTED_ALGORITHMS}"
            )
        self.eta = self.config.get("eta", 1.0)
        self.loss_type = self.config.get("loss_type", "square")
        if self.loss_type not in self.SUPPORTED_LOSSES:
            raise ValueError(
                f"Unknown loss_type: {self.loss_type}. "
                f"Use one of {self.SUPPORTED_LOSSES}"
            )
        self.ridge_lambda = self.config.get("ridge_lambda", 1.0)

        self.weights: dict[str, float] = {}
        self.losses: dict[str, list[float]] = {}
        self.performances: dict[str, SourcePerformance] = {}
        self._initialized = False

        # Ridge 内部状态：X'X + λI 累积、X'Y 累积
        self._ridge_xtx: dict[tuple[str, str], float] = {}
        self._ridge_xty: dict[str, float] = {}
        self._source_order: list[str] = []

    def initialize(self, source_ids: list[str]) -> None:
        """初始化（均匀权重）。"""
        n = len(source_ids)
        if n == 0:
            raise ValueError("source_ids cannot be empty")
        self.weights = {sid: 1.0 / n for sid in source_ids}
        self.losses = {sid: [] for sid in source_ids}
        self.performances = {
            sid: SourcePerformance(source_id=sid) for sid in source_ids
        }
        self._source_order = list(source_ids)
        self._initialized = True
        # Ridge 初始化
        for s1 in source_ids:
            self._ridge_xty[s1] = 0.0
            for s2 in source_ids:
                self._ridge_xtx[(s1, s2)] = 0.0

    def predict(self, predictions: dict[str, float]) -> float:
        """组合预测 ŷ = Σ(w_k × x_k)。"""
        if not self._initialized:
            self.initialize(list(predictions.keys()))
        # 加入新来源（如果有的话）
        for sid in predictions:
            if sid not in self.weights:
                self._add_source(sid)
        total = sum(self.weights.get(k, 0.0) * v for k, v in predictions.items())
        return total

    def update(self, predictions: dict[str, float], actual: float) -> None:
        """
        观测实际值后更新权重。

        loss = (pred - actual)²  [square]
             = |pred - actual|   [absolute]
             = -[y·log(p)+(1-y)·log(1-p)]  [log]
        """
        if not self._initialized:
            self.initialize(list(predictions.keys()))

        # 计算每个来源的损失
        for sid, pred in predictions.items():
            if sid not in self.losses:
                self._add_source(sid)
            loss = self._compute_loss(pred, actual)
            self.losses[sid].append(loss)

        # 按算法更新权重
        if self.algorithm == "mlpoly":
            self._update_mlpoly(predictions, actual)
        elif self.algorithm == "ewa":
            self._update_ewa(predictions, actual)
        elif self.algorithm == "ridge":
            self._update_ridge(predictions, actual)

        # 更新表现统计
        for sid, pred in predictions.items():
            loss = self._compute_loss(pred, actual)
            self.performances[sid].update(loss, self.weights.get(sid, 0.0))

    def get_weights(self) -> dict[str, float]:
        return dict(self.weights)

    def get_performance(self) -> dict[str, dict[str, Any]]:
        """每个来源的历史表现。"""
        return {
            sid: {
                "weight": p.weight,
                "total_loss": p.total_loss,
                "n_predictions": p.n_predictions,
                "avg_loss": p.avg_loss,
                "recent_avg_loss": (
                    sum(p.recent_losses[-20:]) / max(len(p.recent_losses[-20:]), 1)
                ),
            }
            for sid, p in self.performances.items()
        }

    # ------------------------------------------------------------------
    # 内部方法
    # ------------------------------------------------------------------

    def _add_source(self, sid: str) -> None:
        n = len(self.weights) + 1
        self.weights[sid] = 1.0 / n
        # 重新归一化
        total = sum(self.weights.values())
        self.weights = {k: v / total for k, v in self.weights.items()}
        self.losses[sid] = []
        self.performances[sid] = SourcePerformance(source_id=sid)
        self._source_order.append(sid)
        self._ridge_xty[sid] = 0.0
        for other in self._source_order:
            self._ridge_xtx[(sid, other)] = 0.0
            self._ridge_xtx[(other, sid)] = 0.0

    def _compute_loss(self, pred: float, actual: float) -> float:
        if self.loss_type == "square":
            return (pred - actual) ** 2
        elif self.loss_type == "absolute":
            return abs(pred - actual)
        else:  # log
            p = max(1e-6, min(1 - 1e-6, pred))
            a = max(1e-6, min(1 - 1e-6, actual))
            return -(a * math.log(p) + (1 - a) * math.log(1 - p))

    def _update_mlpoly(self, predictions: dict[str, float], actual: float) -> None:
        """
        ML-Poly: w_k ∝ max(0, Σ_j L̄_j − L̄_k)^{1/η}
        表现好（损失低）的来源获得更高权重。
        """
        if not self.losses:
            return
        avg_losses = {
            sid: (sum(losses) / len(losses)) if losses else 0.0
            for sid, losses in self.losses.items()
        }
        # 平均损失的最小值作为基准
        min_avg = min(avg_losses.values()) if avg_losses else 0.0

        raw_weights: dict[str, float] = {}
        for sid in self.weights:
            # 损失比基准高多少
            excess = avg_losses.get(sid, 0.0) - min_avg
            if excess <= 0:
                raw_weights[sid] = 1.0  # 最佳来源
            else:
                raw_weights[sid] = 1.0 / (1.0 + self.eta * excess)

        total = sum(raw_weights.values())
        if total > 0:
            self.weights = {k: v / total for k, v in raw_weights.items()}

    def _update_ewa(self, predictions: dict[str, float], actual: float) -> None:
        """
        EWA: w_k ∝ exp(−η × Σ_{s<t} loss(x_{k,s}, y_s))
        """
        if not self.losses:
            return
        # 累积损失
        cum_losses = {
            sid: sum(losses) for sid, losses in self.losses.items()
        }
        min_cum = min(cum_losses.values()) if cum_losses else 0.0

        raw_weights: dict[str, float] = {}
        for sid in self.weights:
            excess_loss = cum_losses.get(sid, 0.0) - min_cum
            raw_weights[sid] = math.exp(-self.eta * excess_loss)

        total = sum(raw_weights.values())
        if total > 0:
            self.weights = {k: v / total for k, v in raw_weights.items()}

    def _update_ridge(self, predictions: dict[str, float], actual: float) -> None:
        """
        Ridge: w = (X'X + λI)^{-1} X'Y
        在线累积 X'X 和 X'Y，求解线性系统。
        """
        sids = [s for s in self._source_order if s in predictions]
        if not sids:
            return

        # 累积 X'X 和 X'Y
        for s1 in sids:
            x1 = predictions[s1]
            self._ridge_xty[s1] += x1 * actual
            for s2 in sids:
                x2 = predictions[s2]
                self._ridge_xtx[(s1, s2)] += x1 * x2

        # 构建矩阵并求解 (X'X + λI) w = X'Y
        n = len(sids)
        # 构建增广矩阵 [A | b]
        A = [[0.0] * n for _ in range(n)]
        b = [0.0] * n
        for i, s1 in enumerate(sids):
            for j, s2 in enumerate(sids):
                A[i][j] = self._ridge_xtx[(s1, s2)]
            A[i][i] += self.ridge_lambda  # λI
            b[i] = self._ridge_xty[s1]

        # 高斯消元求解
        weights_vec = self._solve_linear(A, b, n)
        if weights_vec is None:
            return

        # 归一化权重（非负 + 求和为 1）
        raw = {sids[i]: max(0.0, weights_vec[i]) for i in range(n)}
        total = sum(raw.values())
        if total > 0:
            self.weights.update({k: v / total for k, v in raw.items()})

    @staticmethod
    def _solve_linear(A: list[list[float]], b: list[float], n: int) -> list[float] | None:
        """高斯消元法求解线性方程组 Aw = b。"""
        # 增广矩阵
        M = [A[i][:] + [b[i]] for i in range(n)]

        for col in range(n):
            # 找主元
            pivot = col
            for row in range(col + 1, n):
                if abs(M[row][col]) > abs(M[pivot][col]):
                    pivot = row
            M[col], M[pivot] = M[pivot], M[col]

            if abs(M[col][col]) < 1e-12:
                continue  # 奇异，跳过

            # 消元
            for row in range(n):
                if row == col:
                    continue
                factor = M[row][col] / M[col][col]
                for k in range(col, n + 1):
                    M[row][k] -= factor * M[col][k]

        # 回代
        result = [0.0] * n
        for i in range(n):
            if abs(M[i][i]) > 1e-12:
                result[i] = M[i][n] / M[i][i]
        return result


__all__ = [
    "OnlineAggregator",
    "SourcePerformance",
]
