import json
import re
from urllib.request import Request, urlopen


GITHUB_API_BASE = "https://api.github.com"


class ReleaseLookupError(RuntimeError):
    pass


def normalize_version(value: str) -> str:
    value = (value or "").strip()
    return value[1:] if value.lower().startswith("v") else value


def version_key(value: str):
    normalized = normalize_version(value)
    parts = []

    for chunk in re.split(r"[^0-9]+", normalized):
        if chunk:
            parts.append(int(chunk))

    return tuple(parts or [0])


def is_newer_version(remote_version: str, local_version: str) -> bool:
    remote_key = list(version_key(remote_version))
    local_key = list(version_key(local_version))

    size = max(len(remote_key), len(local_key))
    remote_key.extend([0] * (size - len(remote_key)))
    local_key.extend([0] * (size - len(local_key)))

    return tuple(remote_key) > tuple(local_key)


def get_latest_release(repo: str) -> dict:
    repo = (repo or "").strip().strip("/")
    if not repo or "/" not in repo:
        raise ReleaseLookupError("Invalid GitHub repository name.")

    url = f"{GITHUB_API_BASE}/repos/{repo}/releases/latest"
    request = Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "TuxPulse",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )

    try:
        with urlopen(request, timeout=8) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        raise ReleaseLookupError(f"GitHub request failed: {exc}") from exc

    tag_name = payload.get("tag_name") or payload.get("name") or ""
    if not tag_name:
        raise ReleaseLookupError("No published release was returned by GitHub.")

    return {
        "tag_name": str(payload.get("tag_name") or "").strip(),
        "name": str(payload.get("name") or "").strip(),
        "html_url": str(
            payload.get("html_url") or f"https://github.com/{repo}/releases/latest"
        ).strip(),
        "published_at": str(payload.get("published_at") or "").strip(),
    }