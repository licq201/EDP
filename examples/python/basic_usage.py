#!/usr/bin/env python3
"""
SPAF Framework - Basic Usage Example

This example demonstrates the core workflow:
1. Calculate true probabilities from bookmaker odds
2. Analyze probability flow between time points
3. Calculate amplification effects
4. Generate optimized schemes

⚠️ DISCLAIMER: This is for ACADEMIC RESEARCH AND EDUCATIONAL PURPOSES ONLY.
Sports prediction involves real financial risk. No system can guarantee profits.
"""

from datetime import datetime, timedelta

# Import SPAF components
import sys
sys.path.insert(0, '/workspace/src/python')

from spaf import (
    ProbabilityEngine,
    FlowAnalyzer,
    SchemeDesigner,
    MarketType,
    ProbabilitySnapshot,
)


def main():
    """Demonstrate basic SPAF framework usage."""

    print("=" * 60)
    print("SPAF - Sports Probability Analysis Framework")
    print("Basic Usage Example")
    print("=" * 60)
    print("\n⚠️  DISCLAIMER: For ACADEMIC RESEARCH AND EDUCATIONAL PURPOSES ONLY")
    print("   Sports prediction involves real financial risk.\n")

    # ============================================================
    # Step 1: Calculate True Probability
    # ============================================================
    print("Step 1: Calculate True Probability")
    print("-" * 40)

    engine = ProbabilityEngine()

    # Example bookmaker odds for a match
    odds = {
        'home': 1.50,   # Home team to win
        'draw': 4.20,   # Draw
        'away': 6.00,   # Away team to win
    }

    result = engine.calculate_true_probability(odds)

    print(f"Bookmaker Odds: {odds}")
    print(f"Overround (Margin): {result.overround:.2%}")
    print(f"\nTrue Probabilities:")
    for outcome, prob in result.true_probabilities.items():
        print(f"  {outcome}: {prob:.1%}")

    most_likely = result.get_most_likely_outcome()
    print(f"\nMost Likely Outcome: {most_likely[0]} ({most_likely[1]:.1%})")

    # ============================================================
    # Step 2: Analyze Probability Flow
    # ============================================================
    print("\n" + "=" * 60)
    print("Step 2: Analyze Probability Flow")
    print("-" * 40)

    # Create initial and latest probability snapshots
    now = datetime.now()

    initial_snapshot = ProbabilitySnapshot(
        timestamp=now - timedelta(hours=24),
        probabilities={
            'home': 0.65,  # 65% implied probability
            'draw': 0.24,
            'away': 0.16,
        },
        source="bookmaker",
        market_type=MarketType.MATCH_RESULT,
    )

    latest_snapshot = ProbabilitySnapshot(
        timestamp=now,
        probabilities={
            'home': 0.68,  # Increased to 68%
            'draw': 0.22,
            'away': 0.14,
        },
        source="bookmaker",
        market_type=MarketType.MATCH_RESULT,
    )

    flow_report = engine.analyze_flow(initial_snapshot, latest_snapshot)

    print(f"Initial Snapshot: {initial_snapshot.timestamp}")
    print(f"Latest Snapshot: {latest_snapshot.timestamp}")
    print(f"\nProbability Flow Analysis:")

    for flow in flow_report.flows:
        direction_symbol = "↑" if flow.flow_pp > 0 else "↓" if flow.flow_pp < 0 else "→"
        print(
            f"  {flow.outcome}: {flow.initial_prob:.1%} → {flow.latest_prob:.1%} "
            f"({direction_symbol} {flow.flow_pp:+.1f}pp) [{flow.significance}]"
        )

    positive_flows = flow_report.get_positive_flows()
    print(f"\nPositive Flow Outcomes: {[f.outcome for f in positive_flows]}")

    # ============================================================
    # Step 3: Calculate Amplification Effect
    # ============================================================
    print("\n" + "=" * 60)
    print("Step 3: Calculate Amplification Effect")
    print("-" * 40)

    analyzer = FlowAnalyzer()

    # Define gradient map for correct score market
    # Adjacent outcomes in same direction
    gradient_map = {
        'home_1_0': ['home_2_0', 'home_2_1', 'home_3_0'],
        'home_2_0': ['home_1_0', 'home_3_0', 'home_2_1'],
        'home_2_1': ['home_1_0', 'home_2_0', 'home_3_1'],
        'home_3_0': ['home_2_0', 'home_3_1', 'home_4_0'],
    }

    # Current probabilities for correct score market
    outcome_probabilities = {
        'home_1_0': 0.15,
        'home_2_0': 0.12,
        'home_2_1': 0.10,
        'home_3_0': 0.08,
        'home_3_1': 0.06,
        'home_4_0': 0.04,
    }

    # Domain confidence from situational awareness
    # Higher confidence when intelligence supports the flow
    domain_confidence = {
        'home_1_0': 0.8,
        'home_2_0': 0.9,  # Strong team + high scoring
        'home_2_1': 0.7,
        'home_3_0': 0.85,
    }

    amp_report = analyzer.calculate_amplification(
        flow_report=flow_report,
        gradient_map=gradient_map,
        outcome_probabilities=outcome_probabilities,
        domain_confidence=domain_confidence,
    )

    print("Amplification Analysis Results:")
    for amp in amp_report.amplifications:
        if amp.level.value != "none":
            print(
                f"  {amp.outcome}: Score={amp.amplification_score:.2f} "
                f"(Base={amp.base_flow_pp:.1f}pp, "
                f"Consistency={amp.directional_consistency:.2f}, "
                f"Position={amp.gradient_position:.2f}) "
                f"[{amp.level.value}]"
            )

    high_amp = amp_report.get_high_amplification()
    print(f"\nHigh Amplification Outcomes: {[a.outcome for a in high_amp]}")

    # ============================================================
    # Step 4: Generate Schemes
    # ============================================================
    print("\n" + "=" * 60)
    print("Step 4: Generate Optimized Schemes")
    print("-" * 40)

    designer = SchemeDesigner()

    match_data = {
        'match_id': 'example_match_001',
        'home_team': 'Team A',
        'away_team': 'Team B',
    }

    bundle = designer.generate_schemes(
        amplification_report=amp_report,
        budget=100,
        match_data=match_data,
        max_schemes=5,
    )

    print(f"Total Budget: ¥{bundle.total_budget}")
    print(f"Allocated Budget: ¥{bundle.allocated_budget:.2f}")
    print(f"Number of Schemes: {len(bundle.schemes)}")

    for i, scheme in enumerate(bundle.schemes, 1):
        print(f"\n  Scheme {i}:")
        print(f"    Type: {scheme.parlay_type}")
        print(f"    Risk Level: {scheme.risk_level.value}")
        print(f"    Legs: {[leg.selection for leg in scheme.legs]}")
        print(f"    Combined Odds: {scheme.combined_odds:.2f}x")
        print(f"    Stake: ¥{scheme.stake_per_combination:.2f}")
        print(f"    Total Cost: ¥{scheme.total_cost:.2f}")
        print(f"    Potential Return: ¥{scheme.potential_return:.2f}")

    # ============================================================
    # Summary
    # ============================================================
    print("\n" + "=" * 60)
    print("Analysis Complete")
    print("=" * 60)
    print("\nKey Findings:")
    print(f"  • Most likely outcome: {most_likely[0]} ({most_likely[1]:.1%})")
    print(f"  • Bookmaker margin: {result.overround:.2%}")
    print(f"  • Positive flow outcomes: {len(positive_flows)}")
    print(f"  • High amplification signals: {len(high_amp)}")
    print(f"  • Generated schemes: {len(bundle.schemes)}")

    print("\n⚠️  Remember: This is for EDUCATIONAL PURPOSES ONLY.")
    print("   No system can guarantee profits in sports prediction.")
    print("   Always gamble responsibly.\n")


if __name__ == "__main__":
    main()
