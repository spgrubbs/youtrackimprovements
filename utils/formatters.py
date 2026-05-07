"""Slack Block Kit message builders for YouTrack events."""

from services.youtrack import issue_url


_PRIORITY_EMOJI = {
    "critical": ":red_circle:",
    "major": ":large_orange_circle:",
    "normal": ":large_yellow_circle:",
    "minor": ":white_circle:",
    "show-stopper": ":rotating_light:",
}


def _priority_emoji(priority: str) -> str:
    return _PRIORITY_EMOJI.get(priority.lower(), ":large_yellow_circle:")


def new_issue_blocks(issue: dict) -> list[dict]:
    """Build Block Kit blocks for a newly created YouTrack issue.

    Accepts either a raw YouTrack API issue object or the parsed webhook payload.
    """
    issue_id = issue.get("id") or issue.get("idReadable", "?")
    summary = issue.get("summary", "(no title)")
    description = (issue.get("description") or "").strip()[:300]

    assignee_obj = issue.get("assignee") or {}
    assignee = assignee_obj.get("fullName") or assignee_obj.get("login") or "Unassigned"

    priority_obj = issue.get("priority") or {}
    priority = priority_obj.get("name", "Normal")
    emoji = _priority_emoji(priority)

    project_obj = issue.get("project") or {}
    project = project_obj.get("name", "")

    reporter_obj = issue.get("reporter") or {}
    reporter = reporter_obj.get("fullName") or reporter_obj.get("login") or "Unknown"

    url = issue_url(issue_id)

    blocks: list[dict] = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": f"New YouTrack Issue: {issue_id}"},
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*<{url}|{summary}>*"},
            "fields": [
                {"type": "mrkdwn", "text": f"*Project*\n{project}"},
                {"type": "mrkdwn", "text": f"*Priority*\n{emoji} {priority}"},
                {"type": "mrkdwn", "text": f"*Assignee*\n{assignee}"},
                {"type": "mrkdwn", "text": f"*Reporter*\n{reporter}"},
            ],
        },
    ]

    if description:
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*Description*\n{description}"},
        })

    blocks.append({"type": "divider"})
    return blocks


def issue_created_confirmation(issue: dict) -> list[dict]:
    """Confirmation blocks sent back to the user after /create-task succeeds."""
    issue_id = issue.get("id") or issue.get("idReadable", "?")
    summary = issue.get("summary", "")
    url = issue_url(issue_id)

    return [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f":white_check_mark: Issue created: *<{url}|{issue_id} — {summary}>*",
            },
        }
    ]


def meeting_select_blocks(speeches: list[dict]) -> list[dict]:
    """Build a static_select block letting the user pick a meeting."""
    options = [
        {
            "text": {"type": "plain_text", "text": s.get("title") or s.get("otid", "Untitled")[:75]},
            "value": s.get("otid", s.get("id", "")),
        }
        for s in speeches
        if s.get("otid") or s.get("id")
    ]

    if not options:
        return [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": ":warning: No recent meetings found in Otter.ai."},
            }
        ]

    return [
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": "Select a meeting to append to YouTrack:"},
            "accessory": {
                "type": "static_select",
                "action_id": "select_meeting",
                "placeholder": {"type": "plain_text", "text": "Choose a meeting…"},
                "options": options,
            },
        }
    ]
