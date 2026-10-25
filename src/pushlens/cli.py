"""Command-line interface for PushLens."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .models import ScanResult
from .packing import PackError, create_bundle
from .report import render_markdown, render_text
from .scanner import scan_project


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pushlens",
        description="Check a project before publishing it to GitHub — no Git or network required.",
        epilog="Examples: pushlens check ./my-project | pushlens pack ./my-project",
    )
    parser.add_argument("--version", action="version", version=f"PushLens {__version__}")
    commands = parser.add_subparsers(dest="command", required=True)

    check = commands.add_parser("check", help="scan project hygiene, upload limits, and likely secrets")
    check.add_argument("path", nargs="?", default=".", help="project folder (default: current folder)")
    check.add_argument("--format", choices=("text", "json", "markdown"), help="output format (default: Markdown for .md reports, otherwise text)")
    check.add_argument("--report", type=Path, help="write the report to a file (defaults to Markdown for .md, otherwise text)")
    check.add_argument("--list-files", action="store_true", help="print every included relative file path")
    check.add_argument("--strict", action="store_true", help="exit non-zero for warnings as well as critical findings")

    pack = commands.add_parser("pack", help="create a clean ZIP for review and browser upload")
    pack.add_argument("path", nargs="?", default=".", help="project folder (default: current folder)")
    pack.add_argument("-o", "--output", type=Path, help="output ZIP (default: sibling <folder>-github-upload.zip)")
    pack.add_argument("--overwrite", action="store_true", help="replace an existing output file")

    commands.add_parser("gui", help="open the optional graphical interface")
    return parser


def _render(result: ScanResult, output_format: str) -> str:
    if output_format == "json":
        return json.dumps(result.to_dict(), indent=2, ensure_ascii=False)
    if output_format == "markdown":
        return render_markdown(result)
    return render_text(result)


def _exit_code(result: ScanResult, strict: bool = False) -> int:
    if result.blocked:
        return 2
    if strict and any(f.severity == "warning" for f in result.findings):
        return 1
    return 0


def _write_report(text: str, path: Path, protected_root: Path) -> None:
    target = path.expanduser().resolve()
    if target.is_relative_to(protected_root):
        raise ValueError("Save reports outside the scanned project so a report cannot overwrite one of its source files.")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8", newline="\n")


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    if args.command == "gui":
        try:
            from .gui import launch
            launch()
            return 0
        except ImportError as exc:
            print(f"PushLens GUI could not start: {exc}. Install a Python build that includes tkinter.", file=sys.stderr)
            return 1
    try:
        if args.command == "check":
            result = scan_project(args.path)
            output_format = args.format or (
                "markdown" if args.report and args.report.suffix.lower() in {".md", ".markdown"} else "text"
            )
            output = _render(result, output_format)
            if args.list_files and output_format != "json":
                output += "\n\nFiles included in a clean ZIP:\n" + "\n".join(f"  {name}" for name in result.files)
            if args.report:
                _write_report(output, args.report, result.root)
                print(f"Report saved: {args.report.expanduser().resolve()}")
            else:
                print(output)
            return _exit_code(result, args.strict)
        if args.command == "pack":
            output, result = create_bundle(args.path, args.output, overwrite=args.overwrite)
            print(render_text(result))
            print(f"\nBundle created: {output}")
            print("Extract the ZIP, open its top-level project folder, then upload that folder's contents on GitHub.")
            print("Review the files manually before changing repository visibility to Public.")
            return 0
    except (OSError, ValueError, PackError) as exc:
        print(f"pushlens: {exc}", file=sys.stderr)
        return 2
    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
