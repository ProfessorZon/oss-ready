from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .markdown import MarkdownIssue, check_markdown


@dataclass(frozen=True)
class CheckResult:
    id: str
    label: str
    status: str
    points: int
    max_points: int
    message: str


@dataclass(frozen=True)
class Report:
    path: Path
    checks: list[CheckResult]
    markdown_issues: list[MarkdownIssue]

    @property
    def score(self) -> int:
        return sum(check.points for check in self.checks)

    @property
    def max_score(self) -> int:
        return sum(check.max_points for check in self.checks)


def scan_repository(path: Path) -> Report:
    root = path.resolve()
    if not root.exists():
        raise FileNotFoundError(f"path does not exist: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"path is not a directory: {root}")

    markdown_issues = check_markdown(root)
    checks = [
        check_readme(root),
        check_license(root),
        check_project_metadata(root),
        check_tests(root),
        check_ci(root),
        check_community_files(root),
        check_gitignore(root),
        check_markdown_health(markdown_issues),
    ]
    return Report(root, checks, markdown_issues)


def check_readme(root: Path) -> CheckResult:
    readme = find_first(root, ["README.md", "readme.md"])
    if readme is None:
        return fail("readme", "README", 20, "README.md is missing")

    text = readme.read_text(encoding="utf-8")
    has_title = any(line.startswith("# ") for line in text.splitlines())
    lower = text.lower()
    has_install = "install" in lower or "setup" in lower
    has_usage = "usage" in lower or "example" in lower

    if has_title and has_install and has_usage:
        return passed("readme", "README", 20, "README.md has a title, install notes, and usage")
    if has_title:
        return warn("readme", "README", 20, 14, "README.md exists but could use install or usage sections")
    return warn("readme", "README", 20, 10, "README.md exists but has no top-level title")


def check_license(root: Path) -> CheckResult:
    license_file = find_first(root, ["LICENSE", "LICENSE.md", "COPYING", "UNLICENSE"])
    if license_file is None:
        return fail("license", "License", 15, "License file is missing")
    return passed("license", "License", 15, f"License file found: {license_file.name}")


def check_project_metadata(root: Path) -> CheckResult:
    metadata_files = [
        "pyproject.toml",
        "package.json",
        "Cargo.toml",
        "go.mod",
        "Gemfile",
        "composer.json",
        "pom.xml",
        "build.gradle",
    ]
    found = find_first(root, metadata_files)
    if found is None:
        return fail("metadata", "Metadata", 15, "No common project metadata file found")
    return passed("metadata", "Metadata", 15, f"Project metadata found: {found.name}")


def check_tests(root: Path) -> CheckResult:
    test_paths = [
        root / "tests",
        root / "test",
        root / "__tests__",
        root / "spec",
    ]
    if any(path.exists() and any(path.rglob("*")) for path in test_paths):
        return passed("tests", "Tests", 15, "Test directory found")

    patterns = ["test_*.py", "*_test.py", "*.spec.ts", "*.test.ts", "*.spec.js", "*.test.js"]
    if any(next(root.rglob(pattern), None) is not None for pattern in patterns):
        return passed("tests", "Tests", 15, "Test files found")

    return fail("tests", "Tests", 15, "No test directory or common test files found")


def check_ci(root: Path) -> CheckResult:
    ci_paths = [
        root / ".github" / "workflows",
        root / ".gitlab-ci.yml",
        root / ".circleci" / "config.yml",
        root / "azure-pipelines.yml",
    ]
    for path in ci_paths:
        if path.is_dir() and any(path.glob("*.yml")):
            return passed("ci", "CI", 10, f"CI workflow found: {path.relative_to(root)}")
        if path.is_file():
            return passed("ci", "CI", 10, f"CI config found: {path.relative_to(root)}")
    return warn("ci", "CI", 10, 4, "No CI configuration found")


def check_community_files(root: Path) -> CheckResult:
    files = {
        "CONTRIBUTING.md": (root / "CONTRIBUTING.md").exists(),
        "CODE_OF_CONDUCT.md": (root / "CODE_OF_CONDUCT.md").exists(),
    }
    count = sum(files.values())
    if count == 2:
        return passed("community", "Community", 10, "Contribution and conduct files found")
    if count == 1:
        found = next(name for name, exists in files.items() if exists)
        return warn("community", "Community", 10, 6, f"{found} found; add the other community file")
    return warn("community", "Community", 10, 2, "Add CONTRIBUTING.md or CODE_OF_CONDUCT.md")


def check_gitignore(root: Path) -> CheckResult:
    if (root / ".gitignore").exists():
        return passed("gitignore", "Gitignore", 5, ".gitignore found")
    return warn("gitignore", "Gitignore", 5, 0, ".gitignore is missing")


def check_markdown_health(markdown_issues: list[MarkdownIssue]) -> CheckResult:
    failures = sum(1 for issue in markdown_issues if issue.severity == "fail")
    warnings = sum(1 for issue in markdown_issues if issue.severity == "warn")
    if failures:
        return fail("markdown", "Markdown", 10, f"{failures} broken local Markdown link issue(s)")
    if warnings:
        points = max(5, 10 - min(warnings, 5))
        return warn("markdown", "Markdown", 10, points, f"{warnings} Markdown style warning(s)")
    return passed("markdown", "Markdown", 10, "Markdown links and style checks passed")


def find_first(root: Path, names: list[str]) -> Path | None:
    for name in names:
        path = root / name
        if path.exists():
            return path
    return None


def passed(id: str, label: str, points: int, message: str) -> CheckResult:
    return CheckResult(id, label, "pass", points, points, message)


def warn(id: str, label: str, max_points: int, points: int, message: str) -> CheckResult:
    return CheckResult(id, label, "warn", points, max_points, message)


def fail(id: str, label: str, max_points: int, message: str) -> CheckResult:
    return CheckResult(id, label, "fail", 0, max_points, message)

