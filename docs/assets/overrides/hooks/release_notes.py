"""
Populate the Release Notes page from the GitHub Releases of this repository.

The page content in docs/home/release-notes.md is only a fallback shown if the
GitHub API cannot be reached at build time (e.g. no network, rate limit).
"""

from __future__ import annotations

import logging
import os
import re
from datetime import datetime
from typing import TYPE_CHECKING

import requests

if TYPE_CHECKING:
    from mkdocs.config.defaults import MkDocsConfig
    from mkdocs.structure.files import Files
    from mkdocs.structure.pages import Page

log = logging.getLogger("mkdocs.hooks.release_notes")

REPO = "open-energy-transition/technology-data"
RELEASE_NOTES_PAGE = "home/release-notes.md"


def on_page_markdown(markdown: str, *, page: Page, config: MkDocsConfig, files: Files) -> str:
    if page.file.src_uri != RELEASE_NOTES_PAGE:
        return markdown

    try:
        releases = _fetch_releases()
    except Exception as exc:
        log.warning(f"Could not fetch GitHub releases for {RELEASE_NOTES_PAGE}: {exc}")
        return markdown

    return "\n\n".join(["# Release Notes", *(_format_release(r) for r in releases)])


def _fetch_releases() -> list[dict]:
    headers = {"Accept": "application/vnd.github+json"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    response = requests.get(
        f"https://api.github.com/repos/{REPO}/releases",
        headers=headers,
        params={"per_page": 100},
        timeout=10,
    )
    response.raise_for_status()
    return [release for release in response.json() if not release["draft"]]


def _format_release(release: dict) -> str:
    title = release["name"] or release["tag_name"]
    published = datetime.fromisoformat(release["published_at"].replace("Z", "+00:00"))
    body = _demote_headings(release["body"] or "_No description provided._")

    lines = [f"## {title}", "", f"*Released {published:%Y-%m-%d}.*"]
    if release.get("prerelease"):
        lines += ["", '!!! warning "Pre-release"']
    lines += ["", body, "", f"[View on GitHub]({release['html_url']})"]
    return "\n".join(lines)


def _demote_headings(body: str) -> str:
    return re.sub(r"^#{1,5} ", lambda match: "#" + match.group(0), body, flags=re.M)
