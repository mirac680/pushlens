# Contributing

Thanks for helping make a first GitHub upload less intimidating.

## Before opening an issue

- Include your operating system and, if available, Python version.
- Include the command or UI action that led to the issue.
- Use a tiny synthetic project to reproduce scanner behavior. Never attach a real `.env`, private key, customer export, or unredacted report.
- Use the bug report and feature request forms so the issue contains the details needed to review it.

## Development

PushLens targets Python 3.10+ and has no runtime dependencies. From the repository root:

```powershell
$env:PYTHONPATH = "$PWD\src"
python -m pushlens --help
python -m pushlens check .
```

Keep scanning offline and read-only. Never put matched values or source snippets in terminal output, JSON reports, error messages, screenshots, or documentation examples. Preserve safe ZIP behavior: exclude generated folders, do not follow symlinks, block critical findings, and write archives outside the scanned tree.

For changes to detection rules, document both the synthetic positive case and a likely false-positive case. Rules should make uncertainty visible rather than claiming a project is secure.
