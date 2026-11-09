# Security Policy — FKRA Depth Studio

## Reporting a vulnerability

**Please do not open a public issue for security problems.**

Report privately through GitHub: **Security → Report a vulnerability** on this repository
(GitHub private vulnerability reporting). You will get a reply within 7 days, and a fix or a
plan within 30 days. Please give us that time before talking about it publicly.

Useful to include: what you found, the steps to reproduce it, the version/commit, and the impact.

## Supported versions

| Version | Supported |
|---|---|
| latest `main` | ✅ |
| older commits / forks | ❌ — update to `main` |

## How the code protects you

- **Runs 100% locally.** Your videos never leave your machine. Nothing is uploaded, and there
  is no telemetry or analytics.
- **Pinned and verified downloads.** The only network access is the first-run download of 3
  MediaPipe models and 3 Google Fonts. Each URL is pinned to a fixed version and checked against
  a SHA-256 hash in `fx_core.py`. A file that doesn't match is deleted and refused, not loaded.
- **No secrets.** The project needs no API keys or tokens. Never add one to a plan file, an
  issue or a pull request.
- **No shell injection.** ffmpeg is called with argument lists (`subprocess` without `shell=True`).
  File paths from plan files are passed as arguments, never put into a shell command.
- **Plan files are data.** `plan.json` is parsed as JSON only; it cannot run code.

## Safe use

1. Install dependencies from PyPI only:
   `pip install numpy pillow opencv-python-headless mediapipe`
2. Only run plan files and videos you trust, and keep them in their own folder.
3. Don't run the scripts as root/admin unless you need to.
4. If a checksum error appears, **don't** bypass it. Report it (see above).

## Out of scope

Bugs in ffmpeg, MediaPipe, OpenCV or Pillow themselves. Report those to their projects.
Licence violations (copies re-published without permission) are not security issues: open an
issue titled "License violation", or file a DMCA takedown with GitHub.
