# 🎯 EDP - Expectation Domain Perception Method

> **期望域感知法**
>
> **Domain-Aware Probability Analysis Framework - 全域感知型概率分析框架**

![Version](https://img.shields.io/badge/Version-4.1-blue)
![Status](https://img.shields.io/badge/Status-Production--Ready-green)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![TypeScript](https://img.shields.io/badge/TypeScript-5.0%2B-blue)

---

## ⚠️ Academic Disclaimer

> **This framework is for ACADEMIC RESEARCH AND EDUCATIONAL PURPOSES ONLY.**
>
> - This framework is an academic tool for **probability analysis and statistical research**.
> - Historical probability patterns do **NOT guarantee** future results.
> - This framework does **NOT constitute any investment advice or decision-making advice**.
> - Users bear full responsibility for their own decisions and must comply with **local laws and regulations**.

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Core Innovations](#core-innovations)
- [Design Philosophy](#design-philosophy)
- [Probability Analysis Engine](#probability-analysis-engine)
- [Probability Flow Amplification Effect](#probability-flow-amplification-effect)
- [Domain Awareness System](#domain-awareness-system)
- [Technical Specifications](#technical-specifications)
- [Academic Foundation](#academic-foundation)
- [Quick Start](#quick-start)
- [Contributing](#contributing)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Domain Awareness Layer                    │
│  Multi-source Intelligence ← Cross-validation ← Assessment  │
├─────────────────────────────────────────────────────────────┤
│                    Flow Amplification Layer                  │
│  Base Flow → Directional Consistency → Gradient → Momentum  │
├─────────────────────────────────────────────────────────────┤
│                    Bayesian Inference Layer                  │
│  Prior Probability → Evidence Update → Posterior → CI       │
├─────────────────────────────────────────────────────────────┤
│                    Probability Analysis Layer                │
│  Shin Normalization → True Probability → Conditional → Flow │
├─────────────────────────────────────────────────────────────┤
│                    Data Acquisition Layer                    │
│  Snapshot Collection ← Quality Validation ← Standard API    │
└─────────────────────────────────────────────────────────────┘
```

---

## Core Innovations

### 1. Domain-Aware System

Multi-source intelligence integration with cross-validation:

- **Multi-source Integration**: Rankings, historical records, tactical analysis, status information, motivational factors
- **Cross-validation Mechanism**: Multi-source signal consistency verification
- **Confidence Quantification**: 5-level confidence classification (Very High/High/Medium/Low/Negative)
- **Situation Assessment**: Strength differential, fatigue factors, home/away performance

### 2. Probability Flow Analysis

Probability flow analysis based on Bayesian updating:

- **Base Flow**: Time-varying change in true probability
- **Momentum Score**: Time series momentum indicator
- **Velocity/Acceleration**: Rate of flow change
- **Aggregate Momentum**: Market-wide confidence trend

### 3. Flow Amplification Effect

Signal amplification mechanism based on market efficiency theory:

```
Amplification_Score = Base_Flow × Directional_Consistency × Gradient_Position × Market_Momentum
```

- **Gradient Graph Propagation**: Signal propagation through Outcome gradient graph
- **Cascade Risk Assessment**: Detection of potential false signal cascades
- **6 Amplification Levels**: None/Low/Medium/High/Very High/Exceptional

---

## Design Philosophy

### OODA Loop × Loop Engineering × DAG Execution

**OODA Loop** (Boyd, 1987):
- Observe → Orient → Decide → Act
- Iterative refinement embedded in each layer

**Loop Engineering**:
- Feedback loops at each stage
- Continuous signal quality calibration

**DAG Execution**:
- Standardized protocols for data transfer between nodes
- Supports independent iteration and replacement

---

## Probability Analysis Engine

### Core Technologies

1. **Shin Normalization Method**
   - Extract true probability from market quotes
   - Remove market margin (overround)
   - Calculate per-outcome margin allocation

2. **Bayesian Inference**
   - Beta-Binomial conjugate model
   - Multi-source prior weighted combination
   - 95% credible interval calculation

3. **Elo Rating System**
   - Dynamic K-factor
   - Rating deviation (RD) tracking
   - Strength history modeling

### API Example

```python
from edp import ProbabilityEngine

engine = ProbabilityEngine()

# Calculate true probability
result = engine.calculate_true_probability({
    'home': 1.50,
    'draw': 4.20,
    'away': 6.00
})

print(result.true_probabilities)
# {'home': 0.632, 'draw': 0.226, 'away': 0.158}
```

---

## Probability Flow Amplification Effect

### Gradient Graph Structure

```
Home Advantage Direction:
1:0 → 2:0 → 2:1 → 3:0 → 3:1 → 3:2 → 4:0 → ...

Draw Direction:
0:0 → 1:1 → 2:2 → 3:3 → ...

Away Advantage Direction:
0:1 → 0:2 → 1:2 → 0:3 → 1:3 → 2:3 → ...
```

### Amplification Score Formula

```python
Amplification_Score =
    Base_Flow ×
    Directional_Consistency ×
    (1 + Gradient_Position) ×
    Market_Momentum
```

---

## Domain Awareness System

### Intelligence Source Weights

| Source | Weight | Description |
|--------|--------|-------------|
| Rankings | High | Official ranking data |
| History | High | Historical head-to-head records |
| Recent Form | High | Recent performance data |
| Tactics | Medium | Offensive/defensive style analysis |
| Status | Medium | Key factor availability |
| Motivation | Medium | Event background factors |

### Confidence Calculation

```python
Confidence = Flow_Confidence × Intelligence_Confidence × Market_Consensus
```

| Confidence | Condition | Action |
|------------|-----------|--------|
| Very High | Three dimensions aligned | Full weight |
| High | Two dimensions aligned | Downweighted inclusion |
| Medium | One dimension supporting | Small weight combination |
| Negative | Dimensional conflict | Exclude or use as contrarian signal |

---

## Technical Specifications

### Tech Stack

- **Python**: 3.10+
- **TypeScript**: 5.0+
- **Type Safety**: Full type annotations
- **Test Coverage**: pytest + Jest

### Code Quality

- Ruff linting
- Black formatting
- Mypy type checking
- 95%+ test coverage target

---

## Academic Foundation

### Core Literature

| Theory | Literature | Application |
|--------|------------|-------------|
| Shin Method | Shin (1992) | True probability extraction |
| Bayesian Inference | Gelman et al. (2013) | Probability updating |
| Time Series Momentum | Moskowitz et al. (2012) | Amplification effect |
| Information Cascade | Banerjee (1992) | Cascade risk |
| Elo Rating | Elo (1978) | Strength modeling |
| Prospect Theory | Kahneman & Tversky (1979) | Bias mitigation |

For complete reference list, see [docs/theory/references.md](docs/theory/references.md)

---

## Quick Start

### Installation

```bash
# Python
pip install edp-framework

# JavaScript/TypeScript
npm install edp-framework
```

### Python Example

```python
from edp import ProbabilityEngine, FlowAmplificationEngine, DomainAwarenessSystem

# Initialize engines
engine = ProbabilityEngine()
amplifier = FlowAmplificationEngine()
awareness = DomainAwarenessSystem()

# Calculate true probability
result = engine.calculate_true_probability({'home': 1.5, 'draw': 4.0, 'away': 6.0})

# Analyze probability flow
flow_report = engine.analyze_flow(initial_snapshot, latest_snapshot)

# Calculate amplification effect
amp_report = amplifier.calculate_amplification(flow_report, outcome_probs)

# Domain awareness analysis
domain_report = awareness.analyze_match(match_intel, flow_confidences)
```

### TypeScript Example

```typescript
import { ProbabilityEngine, FlowAmplificationEngine } from 'edp-framework';

const engine = new ProbabilityEngine();
const amplifier = new FlowAmplificationEngine();

const result = engine.calculateTrueProbability({ home: 1.5, draw: 4.0, away: 6.0 });
```

---

## Contributing

We welcome community contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) to learn how to participate.

### Development Setup

```bash
# Python development
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"

# JavaScript development
npm install
npm run build
```

### Running Tests

```bash
# Python
pytest tests/python/

# JavaScript
npm test
```

---

## License

MIT License - See [LICENSE](LICENSE) file for details.

---

## Disclaimer

**This framework is for ACADEMIC RESEARCH AND EDUCATIONAL PURPOSES ONLY.**

- This framework does not constitute any investment advice or decision-making advice
- Any decisions made using this framework are the user's sole responsibility
- The author is not responsible for any losses incurred through use of this framework
- Please comply with laws and regulations in your jurisdiction

---

*Providing academic research support through structured analysis, rigorous probability theory, and domain cognition—for academic research purposes only.*

*© 2026 — For Academic Research and Educational Purposes Only.*
