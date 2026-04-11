import json
from arcnical.report.builder import ReportBuilder
from arcnical.report.formatters import JSONFormatter
from arcnical.schema import Qualification, TargetClassification, PracticeDetection

builder = ReportBuilder()
formatter = JSONFormatter()

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
    
    json_str = formatter.format_report(report)
    
    # Parse JSON
    parsed = json.loads(json_str)
    
    # Check key fields
    checks = [
        ("Is dict", isinstance(parsed, dict)),
        ("Has metadata", "metadata" in parsed),
        ("Has scores", "scores" in parsed),
        ("Has recommendations", "recommendations" in parsed),
        ("Valid JSON", True)
    ]
    
    for check_name, result in checks:
        status = "✅" if result else "❌"
        print(f"{status} {check_name}")
    
    if all(c[1] for c in checks):
        print("✅ JSON formatting OK")
    else:
        print("❌ JSON formatting issues")
        
except Exception as e:
    print(f"❌ JSON formatting failed: {e}")
    import traceback
    traceback.print_exc()
