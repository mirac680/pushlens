"""Small immutable result objects shared by the scanner and output renderers."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from ._version import __version__


@dataclass(frozen=True, slots=True)
class Finding:
    rule: str
    severity: str
    path: str
    message: str
    line: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ScanResult:
    root: Path
    files: tuple[str, ...]
    total_bytes: int
    findings: tuple[Finding, ...]
    skipped_links: int = 0

    @property
    def blocked(self) -> bool:
        return any(f.severity == "critical" for f in self.findings)

    @property
    def status(self) -> str:
        if self.blocked:
            return "BLOCKED"
        if any(f.severity == "warning" for f in self.findings):
            return "REVIEW"
        return "READY"

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool": "PushLens",
            "version": __version__,
            "status": self.status,
            "root": self.root.name,
            "file_count": len(self.files),
            "files": list(self.files),
            "total_bytes": self.total_bytes,
            "skipped_links": self.skipped_links,
            "findings": [finding.to_dict() for finding in self.findings],
        }
