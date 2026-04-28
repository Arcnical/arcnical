"""HTML exporter: RecommendationDocument → fully self-contained, print-friendly HTML."""

from arcnical.review.recommendation_doc import IssueDetail, RecommendationDocument

# ── Severity palette ──────────────────────────────────────────────────────────
_SEV = {
    "CRITICAL": {"fg": "#dc2626", "bg": "#fef2f2", "border": "#fecaca"},
    "HIGH":     {"fg": "#ea580c", "bg": "#fff7ed", "border": "#fed7aa"},
    "MEDIUM":   {"fg": "#d97706", "bg": "#fffbeb", "border": "#fde68a"},
    "LOW":      {"fg": "#64748b", "bg": "#f8fafc", "border": "#e2e8f0"},
}

_CSS = """
/* ── Reset ── */
*{box-sizing:border-box;margin:0;padding:0}
html{-webkit-font-smoothing:antialiased;-moz-osx-font-smoothing:grayscale}

/* ── Base ── */
body{
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  font-size:14px;line-height:1.65;color:#0f172a;background:#f1f5f9;
}

/* ── Page container ── */
.page{max-width:840px;margin:0 auto;padding:36px 24px 72px}

/* ════════════════════════════════════════════
   COVER CARD
════════════════════════════════════════════ */
.cover{
  background:#fff;border-radius:12px;border:1px solid #e2e8f0;
  border-top:4px solid #7c3aed;margin-bottom:24px;overflow:hidden;
}
.cover-main{padding:32px 36px 24px;display:flex;align-items:flex-start;justify-content:space-between;gap:24px}

/* logo + meta */
.cover-left{flex:1;min-width:0}
.logo{font-size:18px;font-weight:900;letter-spacing:-0.5px;margin-bottom:10px}
.logo .arc{color:#7c3aed}.logo .nical{color:#f59e0b}
.report-title{font-size:24px;font-weight:800;color:#0f172a;letter-spacing:-0.4px;margin-bottom:12px;line-height:1.2}
.meta-row{font-size:13px;color:#64748b;margin-bottom:3px}
.meta-row strong{color:#1e293b;font-weight:600}

/* score badge */
.score-badge{
  flex-shrink:0;text-align:center;background:#f5f3ff;
  border:1px solid #ede9fe;border-radius:10px;padding:18px 28px;min-width:120px
}
.score-num{font-size:56px;font-weight:900;color:#7c3aed;line-height:1}
.score-denom{font-size:14px;font-weight:600;color:#a78bfa;margin-top:1px}
.score-caption{font-size:10px;color:#94a3b8;text-transform:uppercase;letter-spacing:.8px;margin-top:6px}

/* score breakdown row */
.breakdown{
  display:grid;grid-template-columns:repeat(4,1fr);
  border-top:1px solid #f1f5f9;
}
.bd-cell{padding:14px 0;text-align:center;border-right:1px solid #f1f5f9}
.bd-cell:last-child{border-right:none}
.bd-val{font-size:22px;font-weight:800;color:#334155}
.bd-lbl{font-size:10px;color:#94a3b8;text-transform:uppercase;letter-spacing:.6px;margin-top:3px}

/* ════════════════════════════════════════════
   SEVERITY OVERVIEW
════════════════════════════════════════════ */
.sev-overview{
  display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:24px
}
.sev-card{border-radius:10px;padding:16px 20px;border:1px solid}
.sev-card-count{font-size:32px;font-weight:900;line-height:1;margin-bottom:4px}
.sev-card-label{font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.5px}

/* ════════════════════════════════════════════
   SECTION HEADINGS
════════════════════════════════════════════ */
.section-label{
  font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:1px;
  color:#94a3b8;margin-bottom:12px;padding-bottom:8px;border-bottom:1px solid #e2e8f0
}

/* ════════════════════════════════════════════
   ISSUE CARDS
════════════════════════════════════════════ */
.issue{
  background:#fff;border:1px solid #e2e8f0;border-radius:10px;
  margin-bottom:12px;overflow:hidden;page-break-inside:avoid
}
.issue-stripe{height:3px}
.issue-body{padding:18px 22px}

.issue-header{display:flex;align-items:center;gap:8px;margin-bottom:10px;flex-wrap:wrap}
.issue-id{
  font-family:ui-monospace,"Cascadia Code","Fira Mono",monospace;
  font-size:11px;color:#94a3b8;font-weight:600;
  background:#f8fafc;border:1px solid #e2e8f0;border-radius:4px;padding:1px 7px;flex-shrink:0
}
.issue-title{font-size:15px;font-weight:700;color:#0f172a;flex:1;min-width:0}

.badge{
  display:inline-flex;align-items:center;flex-shrink:0;
  padding:2px 8px;border-radius:4px;font-size:11px;font-weight:700;letter-spacing:.3px;border:1px solid
}

/* description */
.issue-desc{font-size:13px;color:#334155;line-height:1.65;margin-bottom:14px}

/* subsection label inside card */
.card-label{font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.6px;color:#94a3b8;margin-bottom:6px}

/* affected files */
.file-pills{display:flex;flex-wrap:wrap;gap:5px;margin-bottom:14px}
.file-pill{
  font-family:ui-monospace,"Cascadia Code","Fira Mono",monospace;
  font-size:11px;background:#f8fafc;color:#475569;
  padding:3px 9px;border-radius:4px;border:1px solid #e2e8f0
}

/* fix steps */
.fix-list{padding-left:18px;margin-bottom:14px}
.fix-list li{font-size:13px;color:#334155;line-height:1.6;margin-bottom:4px}

/* chips row */
.chip-row{display:flex;gap:6px;flex-wrap:wrap}
.chip{
  display:inline-block;background:#f8fafc;border:1px solid #e2e8f0;
  border-radius:99px;padding:3px 11px;font-size:12px;color:#64748b
}

/* ════════════════════════════════════════════
   PRIORITY TABLE
════════════════════════════════════════════ */
.priority-table{width:100%;border-collapse:collapse;font-size:13px;background:#fff;border-radius:10px;overflow:hidden;border:1px solid #e2e8f0}
.priority-table th{padding:10px 14px;background:#f8fafc;font-size:10px;text-transform:uppercase;letter-spacing:.6px;color:#64748b;font-weight:700;border-bottom:1px solid #e2e8f0;text-align:left}
.priority-table td{padding:10px 14px;border-bottom:1px solid #f1f5f9;vertical-align:middle}
.priority-table tr:last-child td{border-bottom:none}
.priority-table tr:hover td{background:#fafafa}
.col-num{color:#94a3b8;font-size:12px;font-weight:600;width:36px}
.col-id{font-family:ui-monospace,monospace;color:#7c3aed;font-size:11px;font-weight:600;width:72px}
.col-title{color:#1e293b;font-weight:500}
.col-badge{width:90px}

/* ════════════════════════════════════════════
   FOOTER
════════════════════════════════════════════ */
.footer{
  margin-top:48px;padding-top:18px;border-top:1px solid #e2e8f0;
  display:flex;justify-content:space-between;align-items:center;
  font-size:12px;color:#94a3b8
}
.footer-brand{font-size:13px;font-weight:700;color:#64748b}
.footer-brand .arc{color:#7c3aed}.footer-brand .nical{color:#f59e0b}

/* ════════════════════════════════════════════
   PRINT
════════════════════════════════════════════ */
@media print{
  body{background:#fff}
  .page{padding:16px;max-width:100%}
  .issue{page-break-inside:avoid}
  .cover{border-top-color:#7c3aed}
  a{text-decoration:none;color:inherit}
}
"""


def _badge(severity: str) -> str:
    p = _SEV.get(severity, _SEV["LOW"])
    style = f"color:{p['fg']};background:{p['bg']};border-color:{p['border']}"
    return f'<span class="badge" style="{style}">{severity}</span>'


def _issue_html(iss: IssueDetail) -> str:
    sev = _SEV.get(iss.severity, _SEV["LOW"])
    files = (
        "".join(f'<span class="file-pill">{f}</span>' for f in iss.affected_files)
        or '<span class="file-pill">—</span>'
    )
    steps = "".join(f"<li>{s}</li>" for s in iss.fix) or "<li>—</li>"
    return (
        f'<div class="issue" id="{iss.id}">'
        f'<div class="issue-stripe" style="background:{sev["fg"]}"></div>'
        f'<div class="issue-body">'
        f'<div class="issue-header">'
        f'<span class="issue-id">{iss.id}</span>'
        f'{_badge(iss.severity)}'
        f'<span class="issue-title">{iss.title}</span>'
        f'</div>'
        f'<p class="issue-desc">{iss.description}</p>'
        f'<div class="card-label">Affected files</div>'
        f'<div class="file-pills">{files}</div>'
        f'<div class="card-label">Fix steps</div>'
        f'<ol class="fix-list">{steps}</ol>'
        f'<div class="chip-row">'
        f'<span class="chip">Effort: {iss.effort}</span>'
        f'<span class="chip">Priority #{iss.priority}</span>'
        f'</div>'
        f'</div>'
        f'</div>'
    )


def export_to_html(doc: RecommendationDocument) -> str:
    """Return a fully self-contained HTML string for the given RecommendationDocument."""

    # ── Score breakdown row ───────────────────────────────────────────────────
    breakdown = doc.score_breakdown or {"Overall": doc.health_score}
    breakdown_cells = "".join(
        f'<div class="bd-cell">'
        f'<div class="bd-val">{v:.0f}</div>'
        f'<div class="bd-lbl">{k}</div>'
        f'</div>'
        for k, v in breakdown.items()
    )

    # ── Cover ────────────────────────────────────────────────────────────────
    repo_url_html = (
        f' &mdash; <a href="{doc.repo_url}" style="color:#7c3aed">{doc.repo_url}</a>'
        if doc.repo_url else ""
    )
    cover = (
        f'<div class="cover">'
        f'<div class="cover-main">'
        f'<div class="cover-left">'
        f'<div class="logo"><span class="arc">Arc</span><span class="nical">nical</span></div>'
        f'<div class="report-title">Recommendation Report</div>'
        f'<div class="meta-row">Repository: <strong>{doc.repo_name}</strong>{repo_url_html}</div>'
        f'<div class="meta-row">Analysis date: <strong>{doc.analysis_date}</strong></div>'
        f'<div class="meta-row">Model: <strong>{doc.model_used}</strong></div>'
        f'</div>'
        f'<div class="score-badge">'
        f'<div class="score-num">{doc.health_score:.0f}</div>'
        f'<div class="score-denom">/ 100</div>'
        f'<div class="score-caption">Overall Health</div>'
        f'</div>'
        f'</div>'
        f'<div class="breakdown">{breakdown_cells}</div>'
        f'</div>'
    )

    # ── Severity overview ────────────────────────────────────────────────────
    sev_overview = '<div class="sev-overview">' + "".join(
        f'<div class="sev-card" style="'
        f'background:{_SEV[s]["bg"]};'
        f'border-color:{_SEV[s]["border"]};'
        f'">'
        f'<div class="sev-card-count" style="color:{_SEV[s]["fg"]}">'
        f'{doc.severity_summary.get(s, 0)}</div>'
        f'<div class="sev-card-label" style="color:{_SEV[s]["fg"]}">{s}</div>'
        f'</div>'
        for s in ("CRITICAL", "HIGH", "MEDIUM", "LOW")
    ) + "</div>"

    # ── Issues ───────────────────────────────────────────────────────────────
    sorted_issues = sorted(doc.issues, key=lambda i: i.priority)
    issues_html = "\n".join(_issue_html(iss) for iss in sorted_issues)
    no_issues = (
        '<p style="color:#64748b;font-size:13px;padding:16px 0">No issues found.</p>'
        if not doc.issues else ""
    )

    # ── Priority table ───────────────────────────────────────────────────────
    priority_rows = "".join(
        f'<tr>'
        f'<td class="col-num">#{iss.priority}</td>'
        f'<td class="col-id">{iss.id}</td>'
        f'<td class="col-title">{iss.title}</td>'
        f'<td class="col-badge">{_badge(iss.severity)}</td>'
        f'</tr>'
        for iss in sorted_issues
    )
    priority_table = (
        f'<table class="priority-table">'
        f'<thead><tr>'
        f'<th class="col-num">#</th>'
        f'<th class="col-id">ID</th>'
        f'<th>Issue</th>'
        f'<th>Severity</th>'
        f'</tr></thead>'
        f'<tbody>{priority_rows}</tbody>'
        f'</table>'
    ) if priority_rows else ""

    # ── Footer ───────────────────────────────────────────────────────────────
    footer = (
        f'<div class="footer">'
        f'<div class="footer-brand">'
        f'<span class="arc">Arc</span><span class="nical">nical</span>'
        f' &mdash; Architectural Analysis</div>'
        f'<div>Next review: <strong>{doc.next_review_date}</strong></div>'
        f'</div>'
    )

    # ── Assemble ─────────────────────────────────────────────────────────────
    body = (
        f'<div class="page">'
        f'{cover}'
        f'<div class="section-label">Severity Overview</div>'
        f'{sev_overview}'
        f'<div class="section-label">Issues &mdash; {doc.total_issues} found</div>'
        f'{issues_html}{no_issues}'
        + (
            f'<div class="section-label" style="margin-top:32px">Recommended Fix Order</div>'
            f'{priority_table}'
            if priority_table else ""
        )
        + footer
        + f'</div>'
    )

    return (
        "<!DOCTYPE html>"
        '<html lang="en"><head>'
        '<meta charset="UTF-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<title>Arcnical &mdash; {doc.repo_name}</title>'
        f'<style>{_CSS}</style>'
        '</head><body>'
        f'{body}'
        '</body></html>'
    )
