from arcnical.report.builder import HealthScoreCalculator
from arcnical.schema import Severity

calculator = HealthScoreCalculator()

# Test 1: No findings = high score
findings_empty = {
    "l2_findings": [],
    "l3_findings": [],
    "security_findings": []
}
metrics = {}

try:
    score1 = calculator.calculate_health_score(findings_empty, metrics)
    print(f"✅ No findings score: {score1.overall}/100 (expected ~100)")

    # Test 2: With findings = lower score
    from arcnical.heuristics.l2_detector import L2Finding
    from arcnical.schema import RecommendationCategory

    finding = L2Finding(
        id="L2-001",
        title="Test",
        severity=Severity.HIGH,
        evidence_data={},
        category=RecommendationCategory.ARCHITECTURE
    )

    findings_with_issues = {
        "l2_findings": [finding],
        "l3_findings": [],
        "security_findings": []
    }

    score2 = calculator.calculate_health_score(findings_with_issues, metrics)
    print(f"✅ With HIGH finding score: {score2.overall}/100 (expected < 100)")

    # Verify score2 < score1
    if score2.overall < score1.overall:
        print("✅ Scoring is working correctly")
    else:
        print("❌ Scoring issue: high finding didn't reduce score")

    # Check clamping
    if 0 <= score1.overall <= 100 and 0 <= score2.overall <= 100:
        print("✅ Scores properly clamped 0-100")
    else:
        print("❌ Score clamping issue")

    print("✅ Health score calculation OK")

except Exception as e:
    print(f"❌ Health score calculation failed: {e}")
    import traceback
    traceback.print_exc()
