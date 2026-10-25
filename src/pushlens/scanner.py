"""Read-only project inventory and conservative pre-publish checks.

Secret detection is heuristic by design. Findings report rule, file, and line,
never the matched value or surrounding source text.
"""

from __future__ import annotations

import fnmatch
import os
import re
import stat
from pathlib import Path

from .models import Finding, ScanResult

MAX_FILE_COUNT = 100_000
MAX_FINDINGS = 5_000
MAX_FINDINGS_PER_FILE = 50
MAX_TEXT_SCAN_BYTES = 2 * 1024 * 1024
GITHUB_WEB_FILE_LIMIT = 25 * 1024 * 1024
GITHUB_WEB_BATCH_LIMIT = 100

IGNORED_DIRS = {
    ".git", ".hg", ".svn", "__pycache__", ".mypy_cache", ".pytest_cache",
    ".ruff_cache", ".tox", ".nox", ".venv", "venv", "env", "node_modules",
    ".next", ".nuxt", "build", "dist", "coverage", "htmlcov", "site-packages",
    ".idea", ".gradle", "target", ".pushlens-cache",
}
IGNORED_FILES = {".ds_store", "thumbs.db", "desktop.ini", "npm-debug.log", "yarn-error.log"}
SENSITIVE_NAMES = {
    ".env", ".env.local", ".env.production", ".env.development.local",
    "id_rsa", "id_dsa", "id_ecdsa", "id_ed25519", "credentials.json",
    "credentials", "service-account.json", "secrets.json", "secrets.yaml", "secrets.yml",
}
SAFE_ENV_NAMES = {".env.example", ".env.sample", ".env.template", ".env.dist"}
SENSITIVE_SUFFIXES = {".pem", ".p12", ".pfx", ".key", ".keystore"}

SECRET_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("private-key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----")),
    ("aws-access-key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("aws-secret-key", re.compile(r"(?i)\bAWS_SECRET_ACCESS_KEY[\"']?\s*[:=]\s*[\"']?([A-Za-z0-9/+=]{20,})")),
    ("github-token", re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,})\b")),
    ("gitlab-token", re.compile(r"\bglpat-[A-Za-z0-9_-]{20,}\b")),
    ("slack-token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b")),
    ("stripe-secret", re.compile(r"\b(?:sk|rk)_(?:live|test)_[A-Za-z0-9]{16,}\b")),
    ("google-api-key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
    ("huggingface-token", re.compile(r"\bhf_[A-Za-z0-9]{20,}\b")),
    ("openai-token", re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{32,}\b")),
    ("npm-token", re.compile(r"(?i)(?:_authToken|NPM_TOKEN)\s*[:=]\s*[\"']?([A-Za-z0-9_./+=:-]{20,})")),
    ("generic-secret-assignment", re.compile(
        r"(?i)\b(?:api[_-]?key|access[_-]?(?:token|key)|secret[_-]?(?:key|token)|client[_-]?secret|password|passwd|private[_-]?key|token|secret)"
        r"\b[\"']?\s*[:=]\s*[\"']?([A-Za-z0-9_./+=:-]{20,})"
    )),
    ("authorization-bearer", re.compile(r"(?i)\bauthorization\s*[:=]\s*bearer\s+[A-Za-z0-9._~+/=-]{20,}")),
    ("credential-url", re.compile(r"\bhttps?://[^/\s:@]+:[^/\s@]{8,}@[^/\s]+")),
)
PLACEHOLDER_MARKERS = ("your_", "your-", "example", "placeholder", "changeme", "change_me", "replace_me", "<", "${")


def _relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _is_sensitive_filename(path: Path) -> bool:
    name = path.name.lower()
    if name in SAFE_ENV_NAMES:
        return False
    if name in SENSITIVE_NAMES:
        return True
    return path.suffix.lower() in SENSITIVE_SUFFIXES or name.startswith(".env.") and name not in SAFE_ENV_NAMES


def _is_linked_directory(path: Path) -> bool:
    if path.is_symlink():
        return True
    if os.name != "nt":
        return False
    try:
        attributes = getattr(path.lstat(), "st_file_attributes", 0)
    except OSError:
        return False
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    return bool(reparse_flag and attributes & reparse_flag)


def _read_ignore_patterns(root: Path) -> tuple[str, ...]:
    ignore_file = root / ".pushlensignore"
    if ignore_file.is_symlink():
        raise ValueError(".pushlensignore must be a regular file, not a symbolic link.")
    if not ignore_file.is_file():
        return ()
    try:
        with ignore_file.open("rb") as stream:
            raw = stream.read(64 * 1024 + 1)
        if len(raw) > 64 * 1024:
            raise ValueError(".pushlensignore is larger than the 64 KiB safety limit; shorten it and retry.")
        content = raw.decode("utf-8-sig")
        patterns = tuple(
            line.strip().replace("\\", "/")
            for line in content.splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        )
        if len(patterns) > 512 or any(len(pattern) > 512 for pattern in patterns):
            raise ValueError(".pushlensignore supports up to 512 patterns of at most 512 characters each.")
        return patterns
    except UnicodeError as exc:
        raise ValueError(".pushlensignore must be UTF-8 text; fix it or remove it before scanning.") from exc


def _ignored(rel: str, patterns: tuple[str, ...]) -> bool:
    parts = rel.split("/")
    if any(part.lower() in IGNORED_DIRS for part in parts[:-1]):
        return True
    if parts[-1].lower() in IGNORED_FILES:
        return True
    for pattern in patterns:
        normalized = pattern.lstrip("/")
        if fnmatch.fnmatchcase(rel, normalized) or any(fnmatch.fnmatchcase(part, normalized) for part in parts):
            return True
        if normalized.endswith("/"):
            directory_pattern = normalized.rstrip("/")
            directory_prefixes = ("/".join(parts[:index]) for index in range(1, len(parts)))
            if any(fnmatch.fnmatchcase(prefix, directory_pattern) for prefix in directory_prefixes):
                return True
    return False


def _append_inventory_finding(findings: list[Finding], finding: Finding) -> None:
    if len(findings) < MAX_FINDINGS:
        findings.append(finding)
    elif not findings or findings[-1].rule != "FP198":
        findings.append(Finding("FP198", "critical", ".", f"Report size limit of {MAX_FINDINGS:,} findings reached; additional findings were omitted."))


def _inventory(root: Path, patterns: tuple[str, ...]) -> tuple[list[Path], list[Finding], int]:
    found: list[Path] = []
    findings: list[Finding] = []
    symlinks = 0
    seen = 0
    def report_walk_error(error: OSError) -> None:
        filename = getattr(error, "filename", None)
        location = "."
        if filename:
            try:
                location = _relative(Path(filename), root)
            except ValueError:
                location = "."
        _append_inventory_finding(findings, Finding("FP103", "critical", location, "A folder could not be listed; the project inventory is incomplete, so bundling is blocked."))

    for current, dirs, filenames in os.walk(root, topdown=True, followlinks=False, onerror=report_walk_error):
        current_path = Path(current)
        kept_dirs: list[str] = []
        for dirname in sorted(dirs, key=lambda name: (name.casefold(), name)):
            candidate = current_path / dirname
            rel = _relative(candidate, root)
            if dirname.lower() in IGNORED_DIRS or _ignored(rel + "/placeholder", patterns):
                continue
            if _is_linked_directory(candidate):
                symlinks += 1
                _append_inventory_finding(findings, Finding("FP102", "info", rel, "Linked directory skipped; PushLens never follows directory links."))
                continue
            kept_dirs.append(dirname)
        dirs[:] = kept_dirs
        for filename in sorted(filenames, key=lambda name: (name.casefold(), name)):
            candidate = current_path / filename
            rel = _relative(candidate, root)
            if _ignored(rel, patterns):
                continue
            seen += 1
            if seen > MAX_FILE_COUNT:
                findings.append(Finding("FP199", "critical", ".", f"Project exceeds the {MAX_FILE_COUNT:,}-file safety limit."))
                return found, findings, symlinks
            try:
                if candidate.is_symlink():
                    symlinks += 1
                    _append_inventory_finding(findings, Finding("FP102", "info", rel, "Symbolic link skipped; PushLens never follows links."))
                    continue
                if not candidate.is_file():
                    continue
                found.append(candidate)
            except OSError:
                _append_inventory_finding(findings, Finding("FP103", "warning", rel, "File could not be inspected due to a filesystem error."))
    return found, findings, symlinks


def _scan_content(path: Path, root: Path) -> list[Finding]:
    rel = _relative(path, root)
    try:
        if path.is_symlink():
            raise OSError("file became a symbolic link after inventory")
        flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(path, flags)
        with os.fdopen(descriptor, "rb") as stream:
            source_info = os.fstat(stream.fileno())
            if not stat.S_ISREG(source_info.st_mode):
                raise OSError("path is no longer a regular file")
            size = source_info.st_size
            prefix = stream.read(8192)
            if b"\x00" in prefix:
                return []
            if size > MAX_TEXT_SCAN_BYTES:
                return [Finding("FP104", "warning", rel, "Large file was inventoried but not content-scanned (2 MiB scan cap). Review it before publishing.")]
            raw = prefix + stream.read(MAX_TEXT_SCAN_BYTES - len(prefix) + 1)
    except OSError:
        return [Finding("FP103", "critical", rel, "File could not be read; the project inventory is incomplete, so bundling is blocked.")]
    if len(raw) > MAX_TEXT_SCAN_BYTES:
        return [Finding("FP104", "warning", rel, "File grew beyond the 2 MiB scan cap while being read. Review it before publishing.")]
    if b"\x00" in raw[:8192]:
        return []
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        return []
    findings: list[Finding] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        for rule, pattern in SECRET_PATTERNS:
            match = pattern.search(line)
            if not match:
                continue
            if rule == "private-key" and not pattern.fullmatch(line.strip()):
                continue
            value = match.group(1) if match.lastindex else match.group(0)
            if rule in {"generic-secret-assignment", "aws-secret-key"} and any(marker in value.lower() for marker in PLACEHOLDER_MARKERS):
                continue
            findings.append(Finding("FP201", "critical", rel, f"Possible credential pattern ({rule}); matched text is hidden.", line_number))
            if sum(item.severity == "critical" for item in findings) >= MAX_FINDINGS_PER_FILE:
                findings.append(Finding("FP202", "critical", rel, f"Additional credential-like lines omitted after the per-file limit of {MAX_FINDINGS_PER_FILE}."))
                return findings
            break
    return findings


def scan_project(project: str | Path) -> ScanResult:
    """Inventory a project without changing files or contacting the network."""
    root = Path(project).expanduser().resolve(strict=True)
    if not root.is_dir():
        raise NotADirectoryError(f"Project path is not a directory: {root}")

    patterns = _read_ignore_patterns(root)
    files, findings, skipped_links = _inventory(root, patterns)
    files.sort(key=lambda item: (_relative(item, root).casefold(), _relative(item, root)))
    total_bytes = 0
    for path in files:
        rel = _relative(path, root)
        try:
            size = path.stat().st_size
        except OSError:
            size = 0
            findings.append(Finding("FP103", "critical", rel, "File metadata could not be read; upload-size checks are incomplete, so bundling is blocked."))
        total_bytes += size
        if _is_sensitive_filename(path):
            findings.append(Finding("FP200", "critical", rel, "Sensitive credential or private-key filename must be excluded before publishing."))
        if size > GITHUB_WEB_FILE_LIMIT:
            findings.append(Finding("FP301", "warning", rel, "File exceeds GitHub web upload's 25 MiB per-file limit."))
        findings.extend(_scan_content(path, root))
        if len(findings) > MAX_FINDINGS:
            if not any(item.rule == "FP198" for item in findings):
                findings.append(Finding("FP198", "critical", ".", f"Report size limit of {MAX_FINDINGS:,} findings reached; scan stopped before bundling."))
            break

    basenames = {path.name.lower() for path in files}
    if not any(name.startswith("readme") for name in basenames):
        findings.append(Finding("FP401", "warning", "README.md", "Add a README so visitors know what the project does and how to run it."))
    if "license" not in basenames and not any(name.startswith("license.") for name in basenames):
        findings.append(Finding("FP402", "info", "LICENSE", "No license file detected. Choose one before inviting others to reuse the code."))
    if ".gitignore" not in basenames:
        findings.append(Finding("FP403", "warning", ".gitignore", "Add a .gitignore to document standard Git exclusions and reduce future accidental staging."))
    if len(files) > GITHUB_WEB_BATCH_LIMIT:
        findings.append(Finding("FP302", "warning", ".", f"{len(files)} files exceed GitHub's 100-file browser-upload batch limit; upload in batches or use GitHub Desktop/Git."))
    if patterns:
        findings.append(Finding("FP105", "info", ".pushlensignore", f"Applied {len(patterns)} local ignore pattern(s); ignored content is omitted from the inventory and bundle."))
    if not files:
        findings.append(Finding("FP001", "critical", ".", "No files found. Check the selected folder and .pushlensignore rules."))

    order = {"critical": 0, "warning": 1, "info": 2}
    findings.sort(key=lambda item: (order.get(item.severity, 3), item.path.casefold(), item.path, item.line or 0, item.rule))
    return ScanResult(root, tuple(_relative(path, root) for path in files), total_bytes, tuple(findings), skipped_links)
