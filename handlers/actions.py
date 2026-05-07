"""Block Kit modal submission handlers (view_submission callbacks)."""

import logging

from slack_bolt import App

logger = logging.getLogger(__name__)


def register(app: App) -> None:
    app.view("create_task_submit")(handle_create_task)
    app.view("append_notes_submit")(handle_append_notes)


def handle_create_task(ack, body, client, logger=logger):
    ack()

    from services.youtrack import create_issue
    from utils.formatters import issue_created_confirmation

    values = body["view"]["state"]["values"]
    user_id = body["user"]["id"]

    title = values["title_block"]["title"]["value"]
    description = (values.get("description_block", {}).get("description", {}) or {}).get("value") or ""
    project_id = values["project_block"]["project"]["selected_option"]["value"]
    priority = values["priority_block"]["priority"]["selected_option"]["value"]

    assignee_block = values.get("assignee_block", {})
    assignee_opt = (assignee_block.get("assignee") or {}).get("selected_option")
    assignee_login = assignee_opt["value"] if assignee_opt else None

    try:
        issue = create_issue(
            project_id=project_id,
            summary=title,
            description=description,
            assignee_login=assignee_login,
            priority=priority,
        )
    except Exception:
        logger.exception("Failed to create YouTrack issue")
        client.chat_postMessage(
            channel=user_id,
            text=":x: Failed to create YouTrack issue. Check the bot logs for details.",
        )
        return

    blocks = issue_created_confirmation(issue)
    client.chat_postMessage(channel=user_id, blocks=blocks, text="Issue created.")


def handle_append_notes(ack, body, client, logger=logger):
    ack()

    from services.otter import get_speech_summary
    from services.youtrack import append_comment

    values = body["view"]["state"]["values"]
    user_id = body["user"]["id"]

    # The meeting selector is an accessory action, not an input block — read from state
    meeting_block = values.get("meeting_block") or {}
    meeting_action = (meeting_block.get("select_meeting") or {})
    selected_opt = meeting_action.get("selected_option")
    otid = selected_opt["value"] if selected_opt else None

    ticket_id = values["ticket_block"]["ticket_id"]["value"].strip()

    if not otid:
        client.chat_postMessage(channel=user_id, text=":warning: Please select a meeting.")
        return

    try:
        summary = get_speech_summary(otid)
    except Exception:
        logger.exception("Failed to fetch Otter.ai summary for %s", otid)
        client.chat_postMessage(channel=user_id, text=":x: Could not fetch the Otter.ai summary.")
        return

    comment_text = f"## Meeting Notes (via Otter.ai)\n\n{summary}"

    try:
        append_comment(issue_id=ticket_id, text=comment_text)
    except Exception:
        logger.exception("Failed to append comment to %s", ticket_id)
        client.chat_postMessage(
            channel=user_id,
            text=f":x: Could not append notes to `{ticket_id}`. Verify the ticket ID exists.",
        )
        return

    client.chat_postMessage(
        channel=user_id,
        text=f":white_check_mark: Meeting notes appended to *{ticket_id}* successfully.",
    )
