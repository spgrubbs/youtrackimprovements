"""Slack slash command handlers.

Registered commands:
  /create-task  — opens a modal to create a YouTrack issue
  /append-notes — lists recent Otter.ai meetings; user picks one to append to a ticket
"""

import logging

from slack_bolt import App

logger = logging.getLogger(__name__)


def register(app: App) -> None:
    app.command("/create-task")(create_task)
    app.command("/append-notes")(append_notes)


def create_task(ack, client, body, logger=logger):
    ack()

    from services.youtrack import get_projects, get_users

    try:
        projects = get_projects()
    except Exception:
        logger.exception("Failed to fetch YouTrack projects")
        projects = []

    try:
        users = get_users()
    except Exception:
        logger.exception("Failed to fetch YouTrack users")
        users = []

    project_options = [
        {
            "text": {"type": "plain_text", "text": p.get("name", p.get("shortName", "?"))},
            "value": p["id"],
        }
        for p in projects
        if p.get("id")
    ] or [{"text": {"type": "plain_text", "text": "Default"}, "value": "default"}]

    user_options = [
        {
            "text": {"type": "plain_text", "text": u.get("fullName") or u.get("login", "?")},
            "value": u.get("login", u.get("id", "")),
        }
        for u in users
        if u.get("login") or u.get("id")
    ][:25]  # Slack modals cap options at 100 but keep it manageable

    priority_options = [
        {"text": {"type": "plain_text", "text": p}, "value": p}
        for p in ["Critical", "Major", "Normal", "Minor"]
    ]

    modal: dict = {
        "type": "modal",
        "callback_id": "create_task_submit",
        "title": {"type": "plain_text", "text": "Create YouTrack Task"},
        "submit": {"type": "plain_text", "text": "Create"},
        "close": {"type": "plain_text", "text": "Cancel"},
        "blocks": [
            {
                "type": "input",
                "block_id": "title_block",
                "label": {"type": "plain_text", "text": "Title"},
                "element": {
                    "type": "plain_text_input",
                    "action_id": "title",
                    "placeholder": {"type": "plain_text", "text": "Short, descriptive title"},
                },
            },
            {
                "type": "input",
                "block_id": "description_block",
                "label": {"type": "plain_text", "text": "Description"},
                "optional": True,
                "element": {
                    "type": "plain_text_input",
                    "action_id": "description",
                    "multiline": True,
                    "placeholder": {"type": "plain_text", "text": "Detailed description (optional)"},
                },
            },
            {
                "type": "input",
                "block_id": "project_block",
                "label": {"type": "plain_text", "text": "Project"},
                "element": {
                    "type": "static_select",
                    "action_id": "project",
                    "options": project_options,
                },
            },
            {
                "type": "input",
                "block_id": "priority_block",
                "label": {"type": "plain_text", "text": "Priority"},
                "element": {
                    "type": "static_select",
                    "action_id": "priority",
                    "initial_option": {"text": {"type": "plain_text", "text": "Normal"}, "value": "Normal"},
                    "options": priority_options,
                },
            },
            *(
                [
                    {
                        "type": "input",
                        "block_id": "assignee_block",
                        "label": {"type": "plain_text", "text": "Assignee"},
                        "optional": True,
                        "element": {
                            "type": "static_select",
                            "action_id": "assignee",
                            "placeholder": {"type": "plain_text", "text": "Unassigned"},
                            "options": user_options,
                        },
                    }
                ]
                if user_options
                else []
            ),
        ],
    }

    client.views_open(trigger_id=body["trigger_id"], view=modal)


def append_notes(ack, client, body, logger=logger):
    ack()

    from services.otter import list_speeches
    from utils.formatters import meeting_select_blocks

    try:
        speeches = list_speeches(limit=10)
    except Exception:
        logger.exception("Failed to fetch Otter.ai speeches")
        speeches = []

    blocks = meeting_select_blocks(speeches)

    # Add a text input for the YouTrack ticket ID
    blocks += [
        {
            "type": "input",
            "block_id": "ticket_block",
            "dispatch_action": False,
            "label": {"type": "plain_text", "text": "YouTrack Ticket ID"},
            "element": {
                "type": "plain_text_input",
                "action_id": "ticket_id",
                "placeholder": {"type": "plain_text", "text": "e.g. RAD-42"},
            },
        }
    ]

    modal: dict = {
        "type": "modal",
        "callback_id": "append_notes_submit",
        "title": {"type": "plain_text", "text": "Append Otter Notes"},
        "submit": {"type": "plain_text", "text": "Append"},
        "close": {"type": "plain_text", "text": "Cancel"},
        "blocks": blocks,
    }

    client.views_open(trigger_id=body["trigger_id"], view=modal)
