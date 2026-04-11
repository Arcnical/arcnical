from arcnical.report.builder import ReportBuilder
from arcnical.report.formatters import MarkdownFormatter
from arcnical.schema import Qualification, TargetClassification, PracticeDetection

builder = ReportBuilder()
formatter = MarkdownFormatter()

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
metrics = {}

try:
    report = builder.build_report(
        qualification=qualification,
        findings=findings,
        metrics=metrics,
        practice=practice,
        repo_path=".",
        repo_name="test-repo"
    )
    
    markdown = formatter.format_report(report)
    
    # Check key elements
    checks = [
        ("Header", "# Arcnical Architecture Review Report" in markdown),
        ("Health Score", "## Architecture Health Score" in markdown),
        ("Executive Summary", "## Executive Summary" in markdown),
        ("Content length", len(markdown) > 500)
    ]
    
    for check_name, result in checks:
        status = "✅" if result else "❌"
        print(f"{status} {check_name}")
    
    if all(c[1] for c in checks):
        print("✅ Markdown formatting OK")
    else:
        print("❌ Markdown formatting issues")
        
except Exception as e:
    print(f"❌ Markdown formatting failed: {e}")
    import traceback
    traceback.print_exc()
