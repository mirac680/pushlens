# Security & privacy model

PushLens is a local pre-publish checklist. It is not a security scanner, malware detector, or guarantee that a project is safe to publish.

## Data flow

- The scanner reads the selected directory and a bounded `.pushlensignore` file; it does not make network requests.
- It does not execute project files, Git hooks, build scripts, or package managers.
- It never follows symbolic links or Windows directory junctions.
- It reads text files up to 2 MiB for heuristic pattern checks. Files beyond that limit are inventoried and warned about but not content-scanned.
- Findings contain a rule identifier, relative file path, severity, optional line number, and a generic explanation. Matched file-content text is never stored in a finding or printed. Review file names before sharing a report.
- `pack` creates and scans a temporary project snapshot before writing a new ZIP outside the source directory by default. It never edits or deletes project files. Existing output is not replaced unless `--overwrite` is given.

## Important limits

Pattern-based secret checks can miss credentials, encoded or split secrets, unrecognized providers, binary content, large files, and secrets in Git history. False positives are possible. The path ignore file can hide a sensitive file from the inventory, so inspect `.pushlensignore` and the resulting ZIP.

The built-in skip list is a convenience, not a universal Git ignore implementation. PushLens does not interpret `.gitignore` yet, and GitHub's browser uploader does not apply it when selecting files. Use `.pushlensignore` for explicit exclusions, then inspect the final package and GitHub's upload list before committing, especially before making a repository public.

## Reporting a vulnerability

Please report security concerns privately to the repository owner through GitHub's **Report a vulnerability** feature. Include a minimal synthetic reproduction. Do not publish real credentials, personal data, or sensitive project files in an issue.
