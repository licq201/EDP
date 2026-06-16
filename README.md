# 🎯 EDP - 期望域感知法

> **Expectation Domain Perception Method**
>
> **全域感知型概率分析框架 - Domain-Aware Probability Analysis Framework**

![Version](https://img.shields.io/badge/Version-4.1-blue)
![Status](https://img.shields.io/badge/Status-Production--Ready-green)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![TypeScript](https://img.shields.io/badge/TypeScript-5.0%2B-blue)

---

## ⚠️ 风险声明

> **本框架仅供学术研究与教育用途。**
>
> - 本框架是用于**统计分析研究**的工具。
> - 历史概率模式**不保证**未来结果。
> - 本框架**不构成任何投资建议**。
> - 用户对自身决策承担全部责任，必须遵守**当地法律法规**。

---

## 目录

- [架构总览](#架构总览)
- [核心创新](#核心创新)
- [设计哲学](#设计哲学)
- [概率分析引擎](#概率分析引擎)
- [概率流向倍增效应](#概率流向倍增效应)
- [全域感知系统](#全域感知系统)
- [技术规格](#技术规格)
- [学术基础](#学术基础)
- [快速开始](#快速开始)
- [贡献指南](#贡献指南)

---

## 架构总览

```
┌─────────────────────────────────────────────────────────────┐
│                    全域感知层                                 │
│  多源情报整合 ← 交叉验证 ← 态势评估                          │
├─────────────────────────────────────────────────────────────┤
│                    流向倍增层                                 │
│  基础流向 → 方向一致性 → 梯度位置 → 市场动量 → 倍增评分      │
├─────────────────────────────────────────────────────────────┤
│                    贝叶斯推断层                              │
│  先验概率 → 证据更新 → 后验分布 → 可信区间                   │
├─────────────────────────────────────────────────────────────┤
│                    概率分析层                                │
│  Shin标准化 → 真实概率 → 条件概率 → 流向分析                 │
├─────────────────────────────────────────────────────────────┤
│                    数据获取层                                │
│  快照采集 ← 质量校验 ← 标准化接口                            │
└─────────────────────────────────────────────────────────────┘
```

---

## 核心创新

### 1. 全域感知系统 (Domain-Aware System)

整合多源情报进行交叉验证：

- **多源情报整合**：排名、历史战绩、战术分析、伤停信息、动机因素
- **交叉验证机制**：多源信号一致性检验
- **置信度量化**：5级置信度分类（极高/高/中/低/负）
- **态势评估**：球队实力差异、疲劳因素、主客场表现

### 2. 概率流向分析 (Probability Flow Analysis)

基于贝叶斯更新的概率流动分析：

- **基础流向**：真实概率的时间变化量
- **动量评分**：时间序列动量指标
- **速度/加速度**：流向变化速率
- **聚合动量**：市场整体信心趋势

### 3. 流向倍增效应 (Flow Amplification Effect)

基于市场效率理论的信号放大机制：

```
倍增评分 = 基础流向 × 方向一致性 × 梯度位置 × 市场动量
```

- **梯度图传播**：通过Outcome梯度图计算信号传播
- **级联风险评估**：检测可能的错误信号级联
- **6级放大等级**：无/低/中/高/极高/异常

---

## 设计哲学

### OODA 循环 × 循环工程 × 有向图执行

**OODA 循环**（Boyd, 1987）：
- Observe（观察）→ Orient（定向）→ Decide（决策）→ Act（执行）
- 每层内嵌迭代精炼

**循环工程**：
- 每个环节都有反馈回路
- 持续校准信号质量

**有向图执行**：
- 节点间通过标准化协议传递数据
- 支持独立迭代和替换

---

## 概率分析引擎

### 核心技术

1. **Shin标准化方法**
   - 从市场报价中提取真实概率
   - 移除市场边际（overround）
   - 计算每Outcome的边际分配

2. **贝叶斯推断**
   - Beta-Binomial共轭模型
   - 多源先验加权组合
   - 95%可信区间计算

3. **Elo评分系统**
   - 动态K因子
   - 评分偏差（RD）追踪
   - 球队实力历史

### API示例

```python
from spaf import ProbabilityEngine

engine = ProbabilityEngine()

# 计算真实概率
result = engine.calculate_true_probability({
    'home': 1.50,
    'draw': 4.20,
    'away': 6.00
})

print(result.true_probabilities)
# {'home': 0.632, 'draw': 0.226, 'away': 0.158}
```

---

## 概率流向倍增效应

### 梯度图结构

```
主队赢球方向 (Home Win):
1:0 → 2:0 → 2:1 → 3:0 → 3:1 → 3:2 → 4:0 → ...

平局方向 (Draw):
0:0 → 1:1 → 2:2 → 3:3 → ...

客队赢球方向 (Away Win):
0:1 → 0:2 → 1:2 → 0:3 → 1:3 → 2:3 → ...
```

### 倍增评分公式

```python
Amplification_Score = 
    Base_Flow × 
    Directional_Consistency × 
    (1 + Gradient_Position) × 
    Market_Momentum
```

---

## 全域感知系统

### 情报来源权重

| 来源 | 权重 | 说明 |
|------|------|------|
| 排名 | 高 | FIFA/官方排名 |
| 历史 | 高 | 历史交锋记录 |
| 近期状态 | 高 | 最近5场表现 |
| 战术 | 中 | 攻防风格分析 |
| 伤停 | 中 | 关键球员可用性 |
| 动机 | 中 | 赛事背景因素 |

### 置信度计算

```python
Confidence = Flow_Confidence × Intelligence_Confidence × Market_Consensus
```

| 置信度 | 条件 | 操作 |
|--------|------|------|
| 极高 | 三维一致 | 全权重 |
| 高 | 两维一致 | 降权纳入 |
| 中 | 一维支持 | 小额组合 |
| 负 | 维度冲突 | 排除或逆向 |

---

## 技术规格

### 技术栈

- **Python**: 3.10+
- **TypeScript**: 5.0+
- **类型安全**: 完全类型标注
- **测试覆盖**: pytest + Jest

### 代码质量

- Ruff linting
- Black 格式化
- Mypy 类型检查
- 95%+ 测试覆盖率目标

---

## 学术基础

### 核心文献

| 理论 | 文献 | 应用 |
|------|------|------|
| Shin方法 | Shin (1992) | 真实概率提取 |
| 贝叶斯推断 | Gelman et al. (2013) | 概率更新 |
| 时间序列动量 | Moskowitz et al. (2012) | 倍增效应 |
| 信息级联 | Banerjee (1992) | 级联风险 |
| Elo评分 | Elo (1978) | 球队实力 |
| 前景理论 | Kahneman & Tversky (1979) | 偏差缓解 |

完整文献列表请参见 [docs/theory/references.md](docs/theory/references.md)

---

## 快速开始

### 安装

```bash
# Python
pip install spaf-framework

# JavaScript/TypeScript
npm install spaf-framework
```

### Python 示例

```python
from spaf import (
    ProbabilityEngine,
    FlowAmplificationEngine,
    DomainAwarenessSystem,
)

# 初始化引擎
engine = ProbabilityEngine()
amplifier = FlowAmplificationEngine()
awareness = DomainAwarenessSystem()

# 1. 计算真实概率
result = engine.calculate_true_probability({'home': 1.5, 'draw': 4.0, 'away': 6.0})

# 2. 分析概率流向
flow_report = engine.analyze_flow(initial_snapshot, latest_snapshot)

# 3. 计算倍增效应
amp_report = amplifier.calculate_amplification(flow_report, outcome_probs)

# 4. 全域感知分析
domain_report = awareness.analyze_match(match_intel, flow_confidences)
```

### TypeScript 示例

```typescript
import { 
  ProbabilityEngine, 
  FlowAmplificationEngine 
} from 'spaf-framework';

const engine = new ProbabilityEngine();
const amplifier = new FlowAmplificationEngine();

const result = engine.calculateTrueProbability({ home: 1.5, draw: 4.0, away: 6.0 });
```

---

## 贡献指南

我们欢迎社区贡献！请参见 [CONTRIBUTING.md](CONTRIBUTING.md) 了解如何参与。

### 开发环境

```bash
# Python 开发
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"

# JavaScript 开发
npm install
npm run build
```

### 运行测试

```bash
# Python
pytest tests/python/

# JavaScript
npm test
```

---

## 许可证

MIT License - 详见 [LICENSE](LICENSE)

---

## 免责声明

**本框架仅供学术研究与教育用途。**

- 本框架不构成任何投资建议或预测建议
- 使用本框架进行的任何决策由用户自行承担责任
- 作者不对使用本框架造成的任何损失负责
- 请遵守您所在地区的法律法规

---

*以结构化分析、严格概率论和全域认知提供边际优势——仅供学术研究用途。*

*© 2026 — 仅供学术研究与教育用途。*
