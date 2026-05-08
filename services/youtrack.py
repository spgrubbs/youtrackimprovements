"""YouTrack REST API client.

All requests disable SSL verification because the server uses a self-signed
certificate. This is acceptable for internal-only traffic; add a CA bundle
path to YOUTRACK_CA_BUNDLE in .env if you want strict verification instead.
"""

import os
import httpx

_BASE = os.environ.get("YOUTRACK_URL", "").rstrip("/")
_TOKEN = os.environ.get("YOUTRACK_TOKEN", "")
_CA = os.environ.get("YOUTRACK_CA_BUNDLE", False)  # False == skip verification

_HEADERS = {
    "Authorization": f"Bearer {_TOKEN}",
    "Accept": "application/json",
    "Content-Type": "application/json",
}

# Fields requested from YouTrack for every issue query
_ISSUE_FIELDS = "id,summary,description,project(id,name,shortName),assignee(login,fullName),priority(name),reporter(login,fullName),created,updated,numberInProject"


def _client() -> httpx.Client:
    return httpx.Client(headers=_HEADERS, verify=_CA, timeout=15)


def get_projects() -> list[dict]:
    """Return all accessible projects."""
    with _client() as c:
        r = c.get(f"{_BASE}/api/admin/projects", params={"fields": "id,name,shortName"})
        r.raise_for_status()
        return r.json()


def get_users() -> list[dict]:
    """Return users visible to the current token (used to populate assignee list)."""
    with _client() as c:
        r = c.get(f"{_BASE}/api/users", params={"fields": "id,login,fullName", "$top": 100})
        r.raise_for_status()
        return r.json()


def create_issue(project_id: str, summary: str, description: str = "",
                 assignee_login: str | None = None, priority: str | None = None) -> dict:
    """Create a new issue and return the created issue object."""
    body: dict = {
        "summary": summary,
        "description": description,
        "project": {"id": project_id},
    }
    if assignee_login:
        body["assignee"] = {"login": assignee_login}
    # Priority is a custom field in YouTrack; we set it via customFields
    if priority:
        body["customFields"] = [
            {
                "$type": "EnumIssueCustomField",
                "name": "Priority",
                "value": {"name": priority},
            }
        ]

    with _client() as c:
        r = c.post(
            f"{_BASE}/api/issues",
            json=body,
            params={"fields": _ISSUE_FIELDS},
        )
        r.raise_for_status()
        return r.json()


def append_comment(issue_id: str, text: str) -> dict:
    """Append a comment to an existing issue."""
    with _client() as c:
        r = c.post(
            f"{_BASE}/api/issues/{issue_id}/comments",
            json={"text": text},
            params={"fields": "id,text,created,author(login,fullName)"},
        )
        r.raise_for_status()
        return r.json()


def get_recent_issues(top: int = 20) -> list[dict]:
    """Return the most recently created issues, newest first."""
    with _client() as c:
        r = c.get(
            f"{_BASE}/api/issues",
            params={
                "fields": _ISSUE_FIELDS,
                "$top": top,
                "query": "sort by: created desc",
            },
        )
        r.raise_for_status()
        return r.json()


def issue_url(issue_id: str) -> str:
    return f"{_BASE}/issue/{issue_id}"
