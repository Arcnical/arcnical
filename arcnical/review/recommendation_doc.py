"""Pydantic v2 models for the L4B Reviewer Agent recommendation document."""

from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator


class IssueDetail(BaseModel):
    id: str
    title: str
    severity: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    affected_files: list[str] = Field(default_factory=list)
    description: str
    fix: list[str] = Field(default_factory=list)
    effort: Literal["Low", "Medium", "High"]
    priority: int


class RecommendationDocument(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    repo_name: str
    repo_url: str = ""
    analysis_date: str
    model_used: str
    health_score: float
    severity_summary: dict[str, int] = Field(default_factory=dict)
    issues: list[IssueDetail] = Field(default_factory=list)
    total_issues: int = 0
    next_review_date: str

    @model_validator(mode="after")
    def _sync_derived_fields(self) -> "RecommendationDocument":
        if self.total_issues == 0:
            self.total_issues = len(self.issues)
        if not self.severity_summary:
            counts: dict[str, int] = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
            for iss in self.issues:
                counts[iss.severity] = counts.get(iss.severity, 0) + 1
            self.severity_summary = counts
        return self
