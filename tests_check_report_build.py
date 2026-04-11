from arcnical.report.builder import ReportBuilder
from arcnical.schema import Qualification, TargetClassification, PracticeDetection

builder = ReportBuilder()
qualification = Qualification(
    classification=TargetClassification.APPLICATION,
    confidence=0.95,
    signals=[]
)
practice = PracticeDetection(
    architecture_style="layered",
    api_surfaces=[],
    ci_cd="none",
    containerization=False,
    iac=False,
    observability=False,
    docs=True,
    tests=True
)

findings = {
    "l2_findings": [],
    "l3_findings": [],
    "security_findings": []
}
metrics = {
    "complexity_avg": 8,
    "instability_avg": 0.6,
    "circular_dependencies": 0,
    "god_classes": 0
}

try:
    report = builder.build_report(
        qualification=qualification,
        findings=findings,
        metrics=metrics,
        practice=practice,
        repo_path=".",
        repo_name="test-repo"
    )
    print(f"✅ Report built successfully")
    print(f"✅ Report version: {report.metadata.tool_version}")
    print(f"✅ Health scores: {report.scores.overall}/100")
    print(f"✅ Recommendations: {len(report.recommendations)}")
except Exception as e:
    print(f"❌ Report building failed: {e}")
    import traceback
    traceback.print_exc()
