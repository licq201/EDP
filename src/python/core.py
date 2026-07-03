"""
EDP - 期望域感知方法 (Expectation Domain Perception Method) V2.0
核心数据抽象层 (Layer 0: Data Abstraction)

本模块定义 EDP 框架的基础数据类型与域适配器接口：
    - Outcome:    一个可能的结果
    - Quote:      对某个结果的信号/报价
    - Evidence:   一条证据
    - Snapshot:   某一时刻所有结果的概率快照
    - EventGraph: 结果间的关系图（决定流向传播与倍增计算）
    - DomainAdapter: 域适配器基类（让 EDP 适配任意问题域）

设计哲学：
    不要问"这是什么领域的问题"。
    要问"有多少个信息来源，多少个可能结果，它们之间是什么关系"。

⚠️ 风险警示 ⚠️
    本框架仅供学术研究与教育用途。它不构成任何投资建议、决策建议或
    交易指导。框架输出的概率、信号、分配方案均为统计研究产物，
    历史概率模式不保证未来结果。使用者须自行承担一切决策风险。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


# ======================================================================
# 基本数据类型
# ======================================================================

@dataclass
class Outcome:
    """
    一个可能的结果。

    Attributes:
        id: 结果的唯一标识符
        label: 人类可读的标签
        metadata: 附加元数据
    """

    id: str
    label: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Quote:
    """
    对某个结果的信号/报价。

    支持多种信号类型，通过 to_probability() 统一转换为概率。

    Attributes:
        outcome_id: 对应的结果 ID
        value: 信号值（如小数报价、概率、百分比等）
        signal_type: 信号类型
            - "decimal_odds": 小数报价（>1.0），概率 = 1/value
            - "probability": 直接概率 [0,1]
            - "percentage": 百分比 [0,100]
            - "price": 价格（需外部归一化）
            - "score": 评分（需外部归一化）
        source: 信号来源标识
        timestamp: 信号时间戳
    """

    outcome_id: str
    value: float
    signal_type: str = "decimal_odds"
    source: str = "unknown"
    timestamp: datetime = field(default_factory=datetime.now)

    def to_probability(self) -> float:
        """将信号值转换为 [0,1] 概率。"""
        if self.signal_type == "probability":
            return max(0.0, min(1.0, self.value))
        elif self.signal_type == "decimal_odds":
            return 1.0 / self.value if self.value > 1.0 else 0.0
        elif self.signal_type == "percentage":
            return max(0.0, min(1.0, self.value / 100.0))
        # price / score / 其它：截断到 [0,1]
        return max(0.0, min(1.0, self.value))


@dataclass
class Evidence:
    """
    一条证据。

    Evidence 是从某个信息来源提取的一条结构化证据，content 中至少
    应包含 "probability" / "direction" / "value" 之一。

    定向证据（推荐）：通过 outcome_id 指明该证据支持的具体结果，
    融合引擎将对该结果做定向 log-odds 更新，不影响其它结果。
    若 outcome_id 为 None，则视为对该问题整体的"方向性"证据，
    按其概率对所有结果做加权调整。

    Attributes:
        id: 证据唯一标识
        source_type: 来源类型
            market / model / expert / nlp / sensor / llm / api
        content: 证据内容字典
        outcome_id: 该证据指向的结果 ID（None 表示非定向证据）
        confidence: 来源自报信心 [0,1]
        reliability: 来源可靠性 [0,1]
        timestamp: 证据时间戳
        metadata: 附加元数据
    """

    id: str
    source_type: str
    content: dict[str, Any]
    outcome_id: str | None = None
    confidence: float = 0.7
    reliability: float = 0.8
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)

    def extract_probability(self) -> float:
        """从 content 中提取概率估计 [0,1]。"""
        # 若显式指定 outcome_id 与该 outcome 的概率，优先用 content["probability"]
        if "probability" in self.content:
            return max(0.0, min(1.0, float(self.content["probability"])))
        elif "value" in self.content:
            return max(0.0, min(1.0, float(self.content["value"])))
        elif "direction" in self.content:
            d = str(self.content["direction"]).lower()
            return {
                "upward": 0.65, "bullish": 0.65, "positive": 0.65,
                "downward": 0.35, "bearish": 0.35, "negative": 0.35,
            }.get(d, 0.5)
        return 0.5


@dataclass
class Snapshot:
    """
    某一时刻所有结果的概率快照。

    Attributes:
        timestamp: 快照时间戳
        probabilities: {outcome_id: probability}
        source: 快照来源
        confidence: 数据质量信心 [0,1]
    """

    timestamp: datetime
    probabilities: dict[str, float]
    source: str = "unknown"
    confidence: float = 1.0

    def validate(self) -> bool:
        """验证概率和是否在合理范围内 [0.95, 1.05]。"""
        total = sum(self.probabilities.values())
        return 0.95 <= total <= 1.05


# ======================================================================
# EventGraph — 事件关系图
# ======================================================================

class EventGraph:
    """
    结果间的关系图。

    不同问题的拓扑不同：
        全域示例（两结果）：     A ↔ B
        全域示例（三结果）：     A ↔ B ↔ C（链式）
        近似全域示例：           A ↔ B ↔ C ↔ D ↔ E（有序链）
        复杂关系示例：           完全连接 / 自定义拓扑

    梯度图决定了流向如何传播、倍增如何计算。
    """

    def __init__(self) -> None:
        self.nodes: dict[str, dict[str, Any]] = {}
        self.adjacency: dict[str, list[str]] = {}
        self.edges: list[tuple[str, str, float]] = []  # (src, tgt, distance)

    def add_node(self, node_id: str, **meta: Any) -> None:
        """添加节点。"""
        self.nodes[node_id] = meta
        if node_id not in self.adjacency:
            self.adjacency[node_id] = []

    def add_edge(self, source: str, target: str, distance: float = 1.0) -> None:
        """添加无向边。"""
        # 确保节点存在
        if source not in self.nodes:
            self.add_node(source)
        if target not in self.nodes:
            self.add_node(target)
        self.edges.append((source, target, distance))
        if target not in self.adjacency[source]:
            self.adjacency[source].append(target)
        if source not in self.adjacency[target]:
            self.adjacency[target].append(source)

    def get_adjacent(self, node_id: str) -> list[str]:
        """获取相邻节点。"""
        return self.adjacency.get(node_id, [])

    def get_outcomes(self) -> list[str]:
        """获取所有节点 ID。"""
        return list(self.nodes.keys())

    @staticmethod
    def chain(ids: list[str], distance: float = 1.0) -> "EventGraph":
        """有序链：A ↔ B ↔ C ↔ ..."""
        g = EventGraph()
        for i in ids:
            g.add_node(i)
        for i in range(len(ids) - 1):
            g.add_edge(ids[i], ids[i + 1], distance)
        return g

    @staticmethod
    def fully_connected(ids: list[str]) -> "EventGraph":
        """完全连接。"""
        g = EventGraph()
        for i in ids:
            g.add_node(i)
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                g.add_edge(ids[i], ids[j])
        return g


# ======================================================================
# DomainAdapter — 域适配器基类
# ======================================================================

class DomainAdapter(ABC):
    """
    域适配器基类。

    每个域实现一个适配器，告诉 EDP：
        1. 这个问题有哪些可能的结果
        2. 这些结果之间是什么关系（链、环、完全连接、自定义）
        3. 原始数据如何转换为标准 Quote/Evidence

    EDP 不关心域的具体内容。它只关心结果数量、关系拓扑、信息来源。

    ⚠️ 本适配器仅用于学术研究，不构成任何领域决策建议。
    """

    @abstractmethod
    def get_outcomes(self, context: dict | None = None) -> list[Outcome]:
        """该情境下的所有可能结果。"""
        ...

    @abstractmethod
    def build_event_graph(self, outcomes: list[Outcome]) -> EventGraph:
        """结果间关系。"""
        ...

    @abstractmethod
    def normalize_signals(self, raw_data: Any) -> list[Quote]:
        """将原始数据转为标准 Quote。"""
        ...

    def get_prior(self, context: dict | None = None) -> dict[str, float]:
        """先验概率（默认均匀）。"""
        outcomes = self.get_outcomes(context)
        n = len(outcomes)
        return {o.id: 1.0 / n for o in outcomes} if n > 0 else {}

    def get_reliability_map(self) -> dict[str, float]:
        """不同来源类型的默认可靠性。"""
        return {
            "market": 0.95, "model": 0.70, "expert": 0.60,
            "nlp": 0.50, "sensor": 0.80, "llm": 0.55, "api": 0.75,
        }

    def extract_evidence(self, raw_data: Any) -> list[Evidence]:
        """从原始数据提取证据（默认空，子类可重写）。"""
        return []


class GenericDomain(DomainAdapter):
    """
    通用域适配器：无需自定义子类即可使用。

    适用于快速原型、教学演示、任意"结果+信号"问题。
    """

    def __init__(
        self,
        outcomes: list[Outcome] | list[str],
        graph_type: str = "chain",
    ) -> None:
        # 允许传入字符串列表，自动转为 Outcome
        self._outcomes: list[Outcome] = []
        for o in outcomes:
            if isinstance(o, Outcome):
                self._outcomes.append(o)
            else:
                self._outcomes.append(Outcome(id=str(o), label=str(o)))
        self.graph_type = graph_type

    def get_outcomes(self, context: dict | None = None) -> list[Outcome]:
        return list(self._outcomes)

    def build_event_graph(self, outcomes: list[Outcome]) -> EventGraph:
        ids = [o.id for o in outcomes]
        if self.graph_type == "fully_connected":
            return EventGraph.fully_connected(ids)
        # 默认 chain
        return EventGraph.chain(ids)

    def normalize_signals(self, raw_data: Any) -> list[Quote]:
        """raw_data: {outcome_id: value} 或 {outcome_id: (value, signal_type)}。"""
        quotes: list[Quote] = []
        if not isinstance(raw_data, dict):
            return quotes
        for oid, val in raw_data.items():
            if isinstance(val, tuple):
                value, stype = val
            else:
                value, stype = float(val), "decimal_odds"
            quotes.append(Quote(outcome_id=oid, value=value, signal_type=stype))
        return quotes


__all__ = [
    "Outcome",
    "Quote",
    "Evidence",
    "Snapshot",
    "EventGraph",
    "DomainAdapter",
    "GenericDomain",
]
