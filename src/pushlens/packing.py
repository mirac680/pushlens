"""Create a clean source archive without modifying the project being checked."""

from __future__ import annotations

import os
import shutil
import stat
import tempfile
import zipfile
from dataclasses import replace
from pathlib import Path

from .models import ScanResult
from .scanner import scan_project


class PackError(RuntimeError):
    """The requested source bundle could not be safely created."""


def create_bundle(
    project: str | Path,
    destination: str | Path | None = None,
    *,
    overwrite: bool = False,
) -> tuple[Path, ScanResult]:
    """Write a ZIP with one project-root folder and return it with its scan."""
    result = scan_project(project)
    if result.blocked:
        raise PackError("Bundle stopped: critical findings must be resolved before creating a shareable ZIP.")

    target = Path(destination).expanduser() if destination else result.root.parent / f"{result.root.name}-github-upload.zip"
    target = target.resolve()
    try:
        target.relative_to(result.root)
    except ValueError:
        pass
    else:
        raise PackError("Choose an output path outside the project folder to avoid bundling the archive into itself.")
    if target.exists() and not overwrite:
        raise PackError(f"Output already exists: {target} (use --overwrite to replace it).")
    target.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Build and inspect a snapshot. This closes the gap where a file could
        # change after the first scan but before it is added to the ZIP.
        with tempfile.TemporaryDirectory(prefix=f".{target.name}.stage-", dir=target.parent) as work_dir:
            work = Path(work_dir)
            snapshot_root = work / result.root.name
            snapshot_root.mkdir()
            for relative in result.files:
                source = result.root / relative
                destination = snapshot_root / relative
                try:
                    if source.is_symlink():
                        raise PackError(f"Project changed during packaging: {relative} is now a symbolic link. Run the check again.")
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
                    descriptor = os.open(source, flags)
                    with os.fdopen(descriptor, "rb") as source_stream:
                        source_info = os.fstat(source_stream.fileno())
                        if not stat.S_ISREG(source_info.st_mode):
                            raise PackError(f"Project changed during packaging: {relative} is no longer a regular file. Run the check again.")
                        with destination.open("xb") as destination_stream:
                            shutil.copyfileobj(source_stream, destination_stream)
                    destination.chmod(stat.S_IMODE(source_info.st_mode) & 0o777)
                except PackError:
                    raise
                except OSError as exc:
                    raise PackError(f"Could not snapshot {relative}; the project may have changed. Run the check again. ({exc})") from exc

            snapshot = scan_project(snapshot_root)
            if snapshot.blocked:
                raise PackError("Bundle stopped: the staged snapshot contains a critical finding. Review the current project and scan again.")

            # Catch files added or removed while the snapshot was being copied.
            current = scan_project(result.root)
            if current.files != result.files:
                raise PackError("Project files changed during packaging. Run a fresh check, review the file list, and create the ZIP again.")

            temporary_archive = work / "bundle.tmp"
            with zipfile.ZipFile(temporary_archive, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
                for relative in snapshot.files:
                    archive.write(snapshot_root / relative, arcname=f"{result.root.name}/{relative}")
            if overwrite:
                os.replace(temporary_archive, target)
            elif os.name == "nt":
                try:
                    os.rename(temporary_archive, target)
                except FileExistsError as exc:
                    raise PackError(f"Output already exists: {target} (choose another path or enable overwrite).") from exc
            else:
                try:
                    os.link(temporary_archive, target)
                except FileExistsError as exc:
                    raise PackError(f"Output already exists: {target} (choose another path or enable overwrite).") from exc
                temporary_archive.unlink()
            final_result = replace(snapshot, root=result.root)
    except OSError as exc:
        raise PackError(f"Could not create bundle: {exc}") from exc
    return target, final_result
