from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .scanner import Report, scan_repository


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="oss-ready",
        description="Check whether a repository is ready to publish as open source.",
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Repository path to scan. Defaults to the current directory.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print JSON instead of human-readable output.",
    )
    parser.add_argument(
        "--fail-under",
        type=int,
        metavar="SCORE",
        default=None,
        help="Exit with status 1 if the readiness score is below SCORE.",
    )
    return parser


def report_to_dict(report: Report) -> dict[str, object]:
    return {
        "path": str(report.path),
        "score": report.score,
        "max_score": report.max_score,
        "checks": [
            {
                "id": check.id,
                "label": check.label,
                "status": check.status,
                "points": check.points,
                "max_points": check.max_points,
                "message": check.message,
            }
            for check in report.checks
        ],
        "markdown_issues": [
            {
                "severity": issue.severity,
                "path": str(issue.path),
                "line": issue.line,
                "message": issue.message,
            }
            for issue in report.markdown_issues
        ],
    }


def format_report(report: Report) -> str:
    lines = [
        f"oss-ready: {report.path}",
        f"score: {report.score}/{report.max_score}",
        "",
    ]

    width = max(len(check.label) for check in report.checks) if report.checks else 0
    for check in report.checks:
        status = check.status.upper().ljust(5)
        label = check.label.ljust(width)
        lines.append(f"{status}  {label}  {check.message}")

    if report.markdown_issues:
        lines.extend(["", "Markdown issues:"])
        for issue in report.markdown_issues:
            status = issue.severity.upper().ljust(5)
            rel_path = issue.path.relative_to(report.path)
            lines.append(f"{status}  {rel_path}:{issue.line}  {issue.message}")

    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    path = Path(args.path).expanduser().resolve()

    try:
        report = scan_repository(path)
    except FileNotFoundError as exc:
        print(f"oss-ready: {exc}", file=sys.stderr)
        return 2
    except NotADirectoryError as exc:
        print(f"oss-ready: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(report_to_dict(report), indent=2, sort_keys=True))
    else:
        print(format_report(report))

    if args.fail_under is not None and report.score < args.fail_under:
        return 1
    return 0

