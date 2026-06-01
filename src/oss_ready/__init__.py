"""Open-source repository readiness checks."""

from .scanner import CheckResult, MarkdownIssue, Report, scan_repository

__all__ = ["CheckResult", "MarkdownIssue", "Report", "scan_repository"]
__version__ = "0.1.0"

