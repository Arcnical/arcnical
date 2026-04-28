"""ReviewerAgent (L4B): Evidence[] → Claude API → RecommendationDocument."""

import json
import logging
from datetime import date, timedelta
from typing import Any

from arcnical.review.llm.base import LLMProvider
from arcnical.schema import Evidence
from arcnical.review.recommendation_doc import IssueDetail, RecommendationDocument

logger = logging.getLogger(__name__)

_SEVERITY_ORDER: dict[str, int] = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}

_SYSTEM_PROMPT = (
    "You are a senior software architect. Analyze the provided Evidence[] "
    "and generate a structured recommendation report. "
    "Respond ONLY in JSON. No preamble, no markdown fences, no explanation."
)

_SCHEMA_EXAMPLE: dict = {
    "issues": [
        {
            "id": "ISS-001",
            "title": "...",
            "severity": "CRITICAL|HIGH|MEDIUM|LOW",
            "affected_files": ["file.py:line"],
            "description": "...",
            "fix": ["step 1", "step 2"],
            "effort": "Low|Medium|High",
            "priority": 1,
        }
    ]
}

_FALLBACK_SEVERITY: dict[str, str] = {
    "circular": "CRITICAL",
    "instability": "HIGH",
    "complexity": "MEDIUM",
    "god": "HIGH",
    "security": "CRITICAL",
}


class ReviewerAgent:
    """L4B Reviewer Agent: turns Evidence[] into a structured RecommendationDocument."""

    def __init__(self, provider: LLMProvider) -> None:
        self._provider = provider

    def run(self, evidence: list[Evidence], report: Any) -> RecommendationDocument:
        """
        Run the review cycle.  Never raises — falls back to a template doc on any error.

        Args:
            evidence: Evidence objects from L3 analysis (sorted CRITICAL→LOW by caller).
            report:   Report (or duck-typed proxy) exposing .scores.overall and .summary.repo.
        """
        try:
            prompt = self._build_prompt(evidence, report)
            raw = self._call_llm(prompt, len(evidence))
            return self._parse_response(raw, evidence, report)
        except Exception as exc:
            logger.warning("ReviewerAgent.run failed, using template fallback: %s", exc)
            return self._build_fallback(evidence, report)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _call_llm(self, prompt: str, finding_count: int) -> str:
        # Cap at 4096 — plenty for structured JSON; avoids the non-streaming limit
        max_tokens = min(max(1000, finding_count * 200), 4096)
        # Duck-type check: ClaudeProvider exposes .client (Anthropic SDK object)
        if hasattr(self._provider, "client"):
            response = self._provider.client.messages.create(  # type: ignore[union-attr]
                model=self._provider.get_model_name(),
                max_tokens=max_tokens,
                system=_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )
            return str(response.content[0].text)
        # Generic fallback via review_code (non-Anthropic providers)
        result = self._provider.review_code(
            code_snippet=f"{_SYSTEM_PROMPT}\n\n{prompt}",
            context={},
            metrics={},
        )
        return " ".join(result.recommendations) if result.recommendations else "{}"

    def _build_prompt(self, evidence: list[Evidence], report: Any) -> str:
        # Limit to top-20 most significant items to keep the prompt token count bounded
        evidence_json = json.dumps(
            [e.model_dump() for e in evidence[:20]], indent=2, default=str
        )
        score = getattr(getattr(report, "scores", None), "overall", 0.0)
        repo = getattr(getattr(report, "summary", None), "repo", "unknown")
        return (
            f"Evidence: {evidence_json}\n"
            f"Health Score: {score}\n"
            f"Repo: {repo}\n\n"
            f"Return JSON matching this exact schema:\n"
            f"{json.dumps(_SCHEMA_EXAMPLE, indent=2)}"
        )

    def _parse_response(
        self, raw: str, evidence: list[Evidence], report: Any
    ) -> RecommendationDocument:
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            parts = cleaned.split("```")
            cleaned = parts[1] if len(parts) > 1 else parts[0]
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
        cleaned = cleaned.strip()
        data = json.loads(cleaned)
        issues_raw: list[dict] = data.get("issues", [])
        issues_raw.sort(key=lambda x: _SEVERITY_ORDER.get(x.get("severity", "LOW"), 9))
        issues = [IssueDetail(**i) for i in issues_raw]
        return self._make_document(issues, report)

    def _build_fallback(
        self, evidence: list[Evidence], report: Any
    ) -> RecommendationDocument:
        issues: list[IssueDetail] = []
        for i, ev in enumerate(evidence, 1):
            sev = next(
                (v for k, v in _FALLBACK_SEVERITY.items() if k in ev.metric.lower()),
                "LOW",
            )
            issues.append(
                IssueDetail(
                    id=f"ISS-{i:03d}",
                    title=f"Elevated {ev.metric} detected",
                    severity=sev,
                    affected_files=[
                        f"{ref.file}:{ref.line or 0}" for ref in ev.references[:3]
                    ],
                    description=(
                        f"Metric '{ev.metric}' value {ev.value:.2f} "
                        "exceeds recommended threshold."
                    ),
                    fix=[
                        "Identify the highest-complexity modules in affected files.",
                        "Refactor to reduce coupling and cyclomatic complexity.",
                        "Add unit tests before refactoring to prevent regressions.",
                    ],
                    effort="Medium",
                    priority=i,
                )
            )
        return self._make_document(issues, report)

    def _make_document(
        self, issues: list[IssueDetail], report: Any
    ) -> RecommendationDocument:
        today = date.today()
        _scores = getattr(report, "scores", None)
        score          = float(getattr(_scores, "overall", 0.0))
        maintainability = float(getattr(_scores, "maintainability", 0.0))
        # Report object uses .structure; _ReportProxy exposes .complexity after Fix 1
        complexity      = float(getattr(_scores, "complexity", None) or getattr(_scores, "structure", 0.0))
        security        = float(getattr(_scores, "security", 100.0))
        repo = getattr(getattr(report, "summary", None), "repo", "unknown")
        summary: dict[str, int] = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for iss in issues:
            summary[iss.severity] = summary.get(iss.severity, 0) + 1
        return RecommendationDocument(
            repo_name=repo,
            repo_url="",
            analysis_date=today.isoformat(),
            model_used=self._provider.get_model_name(),
            health_score=score,
            score_breakdown={
                "Overall": score,
                "Maintainability": maintainability,
                "Complexity": complexity,
                "Security": security,
            },
            severity_summary=summary,
            issues=issues,
            total_issues=len(issues),
            next_review_date=(today + timedelta(days=30)).isoformat(),
        )
