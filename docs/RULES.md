# Finding reference

PushLens findings are prompts for review, not proof that a project is unsafe or safe. File paths are relative to the selected project. Matched file-content values and code snippets are never included in a finding; inspect file names before sharing a report.

| Rule | Severity | Meaning | Suggested action |
|---|---|---|---|
| `FP001` | Critical | No files remain after exclusions. | Check the selected folder and `.pushlensignore`. |
| `FP102` | Info | A symbolic link or linked directory was skipped. | If that content belongs in the release, copy the intended files into the project. |
| `FP103` | Warning or critical | A file/folder or its metadata could not be inspected; a critical result means the inventory or size checks are incomplete. | Fix permissions or close the file, then scan again. |
| `FP104` | Warning | A text file is larger than 2 MiB or grew past the scan cap while being read. | Inspect it manually for sensitive content. |
| `FP105` | Info | Custom `.pushlensignore` patterns were applied. | Review the ignore file and the included-file list. |
| `FP198` | Critical | The finding/report safety cap was reached. | Reduce the number of findings and scan again. |
| `FP199` | Critical | The project exceeds the 100,000-file inventory limit. | Exclude generated or unrelated files and scan again. |
| `FP200` | Critical | A filename commonly used for credentials or private keys (such as `.env` or `credentials`) was found. | Remove it from the release or list its path in `.pushlensignore`. |
| `FP201` | Critical | A line resembles a known credential pattern, including common AWS, GitHub/GitLab, or Stripe tokens and long token/password assignments. The matched text is hidden. | Inspect that line locally and rotate any real exposed credential. |
| `FP202` | Critical | More than 50 credential-like matches were found in one file. | Review the whole file locally; additional match locations are omitted. |
| `FP301` | Warning | A file is over GitHub browser upload's 25 MiB per-file limit. | Reduce or exclude it, or use another upload method. |
| `FP302` | Warning | More than 100 files are in the project. | Upload in batches or use GitHub Desktop/Git. |
| `FP401` | Warning | No README was detected. | Add a short introduction and run instructions. |
| `FP402` | Info | No license was detected. | Choose a license before inviting others to reuse the code. |
| `FP403` | Warning | No `.gitignore` was detected. | Add common generated-file exclusions for future Git use. |

Secret checks are heuristic. They can miss credentials and can flag harmless examples. See [Security & privacy](SECURITY.md) for the limits and data-flow notes.
