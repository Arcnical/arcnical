"""HTML exporter: RecommendationDocument → fully self-contained, print-friendly HTML."""

from arcnical.review.recommendation_doc import IssueDetail, RecommendationDocument

_BADGE_STYLE: dict[str, str] = {
    "CRITICAL": "background:#dc2626;color:#fff",
    "HIGH":     "background:#ea580c;color:#fff",
    "MEDIUM":   "background:#ca8a04;color:#fff",
    "LOW":      "background:#6b7280;color:#fff",
}

_CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:Arial,Helvetica,sans-serif;font-size:14px;color:#1a1a2e;background:#fff;padding:32px}
h1{font-size:28px;font-weight:800;margin-bottom:4px}
h2{font-size:20px;font-weight:700;margin:32px 0 12px}
h3{font-size:15px;font-weight:700;margin-bottom:8px}
.cover{border-bottom:3px solid #d902ee;padding-bottom:24px;margin-bottom:32px}
.logo{font-size:32px;font-weight:900;letter-spacing:-1px}
.logo .arc{color:#d902ee}.logo .nical{color:#e6b84a}
.sub{color:#6b7280;font-size:13px;margin-top:4px}
.score{font-size:72px;font-weight:900;color:#d902ee;line-height:1;margin:16px 0 8px}
.score-label{font-size:13px;color:#6b7280;text-transform:uppercase;letter-spacing:1px}
.sev-table{border-collapse:collapse;margin:16px 0}
.sev-table td,.sev-table th{padding:6px 16px;border:1px solid #e5e7eb;font-size:13px}
.sev-table th{background:#f9fafb;font-weight:700}
.badge{display:inline-block;padding:2px 9px;border-radius:4px;font-size:11px;font-weight:700;letter-spacing:.4px;vertical-align:middle}
.issue{border:1px solid #e5e7eb;border-radius:8px;padding:20px;margin-bottom:20px;page-break-inside:avoid}
.issue-header{display:flex;align-items:center;gap:10px;margin-bottom:12px}
.issue-id{font-family:monospace;font-size:12px;color:#6b7280;font-weight:600}
.issue-title{font-size:15px;font-weight:700}
.issue p{margin:8px 0 4px;font-size:13px}
.mono-list{list-style:none;padding-left:0}
.mono-list li{font-family:monospace;font-size:12px;background:#f9fafb;padding:3px 8px;border-radius:4px;margin-bottom:3px;display:inline-block;margin-right:6px}
ol{padding-left:20px;font-size:13px;margin-top:4px}
ol li{margin-bottom:4px}
.chip{display:inline-block;background:#f3f4f6;border:1px solid #e5e7eb;border-radius:99px;padding:2px 10px;font-size:12px;margin-right:6px;margin-top:8px}
.closing{border-top:1px solid #e5e7eb;margin-top:40px;padding-top:24px;color:#374151;font-size:13px}
.closing h2{margin-top:0}
.priority-list{padding-left:20px;margin-top:8px}
.priority-list li{margin-bottom:4px}
@media print{
  body{padding:16px}
  .issue{page-break-inside:avoid}
  a{text-decoration:none;color:inherit}
}
"""


def _badge(severity: str) -> str:
    style = _BADGE_STYLE.get(severity, _BADGE_STYLE["LOW"])
    return f'<span class="badge" style="{style}">{severity}</span>'


def _issue_html(iss: IssueDetail) -> str:
    files = "".join(f"<li>{f}</li>" for f in iss.affected_files) or "<li>—</li>"
    steps = "".join(f"<li>{s}</li>" for s in iss.fix) or "<li>—</li>"
    return (
        f'<div class="issue" id="{iss.id}">'
        f'<div class="issue-header">'
        f'<span class="issue-id">{iss.id}</span>{_badge(iss.severity)}'
        f'<span class="issue-title">{iss.title}</span>'
        f"</div>"
        f"<p><strong>Description:</strong> {iss.description}</p>"
        f"<p><strong>Affected files:</strong></p>"
        f'<ul class="mono-list">{files}</ul>'
        f"<p><strong>Fix steps:</strong></p>"
        f"<ol>{steps}</ol>"
        f'<p><span class="chip">Effort: {iss.effort}</span>'
        f'<span class="chip">Priority: #{iss.priority}</span></p>'
        f"</div>"
    )


def export_to_html(doc: RecommendationDocument) -> str:
    """Return a fully self-contained HTML string for the given RecommendationDocument."""
    sev_rows = "".join(
        f"<tr><td>{_badge(s)}</td><td>{doc.severity_summary.get(s, 0)}</td></tr>"
        for s in ("CRITICAL", "HIGH", "MEDIUM", "LOW")
    )

    cover = (
        f'<div class="cover">'
        f'<div class="logo"><span class="arc">Arc</span><span class="nical">nical</span></div>'
        f"<h1>Recommendation Report</h1>"
        f'<div class="sub">Repository: <strong>{doc.repo_name}</strong>'
        + (f' &mdash; <a href="{doc.repo_url}">{doc.repo_url}</a>' if doc.repo_url else "")
        + f"</div>"
        f'<div class="sub">Analysis date: {doc.analysis_date}'
        f" &nbsp;|&nbsp; Model: {doc.model_used}</div>"
        f'<div class="score">{doc.health_score:.0f}</div>'
        f'<div class="score-label">Health Score / 100</div>'
        f"<h2>Severity Summary</h2>"
        f'<table class="sev-table"><thead>'
        f"<tr><th>Severity</th><th>Count</th></tr></thead>"
        f"<tbody>{sev_rows}</tbody></table>"
        f"</div>"
    )

    issues_html = "\n".join(
        _issue_html(iss) for iss in sorted(doc.issues, key=lambda i: i.priority)
    )
    issues_section = f"<h2>Issues ({doc.total_issues})</h2>\n{issues_html}"

    priority_items = "".join(
        f"<li><strong>{iss.id}</strong> &mdash; {iss.title} {_badge(iss.severity)}</li>"
        for iss in sorted(doc.issues, key=lambda i: i.priority)
    )
    closing = (
        f'<div class="closing">'
        f"<h2>Summary</h2>"
        f"<p>Total issues found: <strong>{doc.total_issues}</strong></p>"
        f"<p><strong>Recommended fix order:</strong></p>"
        f'<ol class="priority-list">{priority_items}</ol>'
        f"<p style='margin-top:16px'>Next review suggested: <strong>{doc.next_review_date}</strong></p>"
        f"</div>"
    )

    return (
        "<!DOCTYPE html>"
        '<html lang="en"><head>'
        '<meta charset="UTF-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>Arcnical Recommendations &mdash; {doc.repo_name}</title>"
        f"<style>{_CSS}</style>"
        "</head><body>"
        f"{cover}"
        f"{issues_section}"
        f"{closing}"
        "</body></html>"
    )
