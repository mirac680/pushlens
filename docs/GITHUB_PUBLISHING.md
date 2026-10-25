# Publish PushLens on GitHub

Suggested repository metadata:

- **Repository name:** `pushlens`
- **Description:** `Check what goes into your GitHub upload before you publish. Offline, local, and Git-free.`
- **Topics:** `github`, `github-upload`, `beginner-friendly`, `python`, `privacy-first`, `offline-first`, `secret-scanning`, `open-source`
- **License:** MIT (`LICENSE` is included)
- **README:** `README.md` (English), with a Turkish version at `README_TR.md`

## Browser upload

1. Create an empty repository. Do not generate a second README, `.gitignore`, or license on GitHub; these files are already here.
2. Use **Add file → Upload files** and drag in the contents of the extracted `pushlens` project folder.
3. Leave `.github`, `.gitignore`, `.pushlensignore`, `docs`, `src`, and the launcher in place. Never upload a real `.env`, API key, or private key.
4. Use a clear commit message such as `Initial release: PushLens 1.0.0`.
5. If you want anyone to discover and star the project, choose **Public**; anyone can view a public repository, while private repositories are visible only to people you grant access. Review the file list and README one final time before making it public.

GitHub currently limits browser uploads to 100 files per batch and 25 MiB per file. GitHub's web uploader does not apply `.gitignore` rules; PushLens's own ZIP excludes the generated directories it knows about and files listed in `.pushlensignore`. Always inspect the archive before uploading it.

For Turkish instructions, see [PushLens'i GitHub'a yükleme](GITHUB_YAYINLAMA.md).

For exact, current GitHub steps, see [Adding a file to a repository](https://docs.github.com/en/repositories/working-with-files/managing-files/adding-a-file-to-a-repository).

For repository visibility details, see [About repositories](https://docs.github.com/en/repositories/creating-and-managing-repositories/about-repositories#about-repository-visibility).
