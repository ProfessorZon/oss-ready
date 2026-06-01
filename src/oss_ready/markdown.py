from __future__ import annotations

import re
import urllib.parse
from fnmatch import fnmatch
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence


LINK_RE = re.compile(r"(!)?\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")
FENCE_RE = re.compile(r"^(```|~~~)(.*)$")


@dataclass(frozen=True)
class MarkdownIssue:
    severity: str
    path: Path
    line: int
    message: str


@dataclass(frozen=True)
class MarkdownLink:
    path: Path
    line: int
    target: str
    label: str
    is_image: bool


def iter_markdown_files(root: Path, ignore_patterns: Sequence[str] | None = None) -> Iterable[Path]:
    ignored = {".git", ".hg", ".svn", ".venv", "venv", "node_modules", "dist", "build"}
    for path in root.rglob("*.md"):
        if ignored.intersection(path.parts):
            continue
        if is_ignored_by_pattern(root, path, ignore_patterns or []):
            continue
        yield path


def is_ignored_by_pattern(root: Path, path: Path, ignore_patterns: Sequence[str]) -> bool:
    rel_path = path.relative_to(root).as_posix()
    return any(fnmatch(rel_path, pattern) or fnmatch(path.name, pattern) for pattern in ignore_patterns)


def slugify_heading(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = text.strip().lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"\s+", "-", text)
    return text.strip("-")


def collect_heading_anchors(path: Path) -> set[str]:
    anchors: set[str] = set()
    seen: dict[str, int] = defaultdict(int)
    for line in path.read_text(encoding="utf-8").splitlines():
        match = HEADING_RE.match(line)
        if not match:
            continue
        base = slugify_heading(match.group(2))
        if not base:
            continue
        count = seen[base]
        seen[base] += 1
        anchors.add(base if count == 0 else f"{base}-{count}")
    return anchors


def iter_links(path: Path) -> Iterable[MarkdownLink]:
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        for match in LINK_RE.finditer(line):
            yield MarkdownLink(
                path=path,
                line=line_number,
                target=match.group(3).strip(),
                label=match.group(2).strip(),
                is_image=bool(match.group(1)),
            )


def is_external_target(target: str) -> bool:
    parsed = urllib.parse.urlparse(target)
    return parsed.scheme in {"http", "https", "mailto", "tel"}


def normalize_local_target(source: Path, target: str) -> tuple[Path, str | None]:
    target = target.split("?", 1)[0]
    if "#" in target:
        raw_path, anchor = target.split("#", 1)
    else:
        raw_path, anchor = target, None

    if raw_path:
        decoded = urllib.parse.unquote(raw_path)
        path = (source.parent / decoded).resolve()
    else:
        path = source.resolve()

    return path, anchor


def check_markdown(root: Path, ignore_patterns: Sequence[str] | None = None) -> list[MarkdownIssue]:
    issues: list[MarkdownIssue] = []
    markdown_files = list(iter_markdown_files(root, ignore_patterns=ignore_patterns))
    anchors = {path.resolve(): collect_heading_anchors(path) for path in markdown_files}

    for path in markdown_files:
        issues.extend(check_markdown_style(path))
        for link in iter_links(path):
            if link.is_image and not link.label:
                issues.append(
                    MarkdownIssue("warn", path, link.line, "image is missing alt text")
                )
            if is_external_target(link.target):
                continue

            target_path, anchor = normalize_local_target(path, link.target)
            if not target_path.exists():
                issues.append(
                    MarkdownIssue(
                        "fail",
                        path,
                        link.line,
                        f"local link target does not exist: {link.target}",
                    )
                )
                continue

            if anchor is not None and target_path.suffix.lower() == ".md":
                expected_anchor = slugify_heading(anchor)
                known_anchors = anchors.get(target_path.resolve(), set())
                if expected_anchor and expected_anchor not in known_anchors:
                    issues.append(
                        MarkdownIssue(
                            "fail",
                            path,
                            link.line,
                            f"local heading anchor does not exist: {link.target}",
                        )
                    )

    return issues


def check_markdown_style(path: Path) -> list[MarkdownIssue]:
    issues: list[MarkdownIssue] = []
    in_fence = False
    fence_marker = ""
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        match = FENCE_RE.match(line)
        if not match:
            continue

        marker, info = match.groups()
        if not in_fence:
            in_fence = True
            fence_marker = marker
            if not info.strip():
                issues.append(
                    MarkdownIssue("warn", path, line_number, "fenced code block has no language")
                )
        elif marker == fence_marker:
            in_fence = False
            fence_marker = ""
    return issues
