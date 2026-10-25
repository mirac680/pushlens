"""Terminal and Markdown renderers. Neither renderer prints matched content values."""

from __future__ import annotations

import re

from .models import Finding, ScanResult

SEVERITY_GLYPH = {"critical": "✖", "warning": "!", "info": "·"}


def _finding_location(finding: Finding) -> str:
    return f"{finding.path}:{finding.line}" if finding.line is not None else finding.path


def _code_span(value: str) -> str:
    value = value.replace("\r", " ").replace("\n", " ").replace("|", "\\|")
    longest = max((len(run) for run in re.findall(r"`+", value)), default=0)
    fence = "`" * (longest + 1)
    padding = " " if value.startswith(("`", " ")) or value.endswith(("`", " ")) else ""
    return f"{fence}{padding}{value}{padding}{fence}"


def render_text(result: ScanResult) -> str:
    lines = [
        f"PushLens  ·  {result.root.name}",
        "─" * 64,
        f"{result.status}  |  {len(result.files):,} files  |  {result.total_bytes / (1024 * 1024):.2f} MiB  |  {result.skipped_links:,} links skipped",
    ]
    if result.findings:
        lines.append("")
        for finding in result.findings:
            glyph = SEVERITY_GLYPH.get(finding.severity, "-")
            lines.append(f"{glyph} [{finding.severity.upper():8}] {finding.rule}  {_finding_location(finding)}")
            lines.append(f"  {finding.message}")
    else:
        lines.extend(["", "No known issues found by the built-in checks."])
    lines.extend([
        "",
        "Privacy: scanned locally. No file contents, matched values, or telemetry are sent anywhere.",
        "Limits: pattern checks can miss secrets. Review every file before making a repository public.",
    ])
    return "\n".join(lines)


def render_markdown(result: ScanResult) -> str:
    lines = [
        f"# PushLens report: {_code_span(result.root.name)}",
        "",
        f"**Status:** {result.status}  ",
        f"**Files:** {len(result.files):,}  ",
        f"**Total size:** {result.total_bytes / (1024 * 1024):.2f} MiB",
        f"**Symbolic links skipped:** {result.skipped_links:,}",
        "",
        "| Severity | Rule | Location | Finding |",
        "|---|---|---|---|",
    ]
    if result.findings:
        for finding in result.findings:
            location = _code_span(_finding_location(finding))
            message = finding.message.replace("|", "\\|")
            lines.append(f"| {finding.severity} | `{finding.rule}` | {location} | {message} |")
    else:
        lines.append("| info | — | — | No known issues found by the built-in checks. |")
    lines.extend([
        "",
        "> This local heuristic report is not a security guarantee. Review every file before sharing or publishing.",
    ])
    return "\n".join(lines) + "\n"
