"""Inbound YouTrack webhook listener (Flask).

YouTrack is configured to POST to http://<your-machine>:<WEBHOOK_PORT>/youtrack/webhook
whenever a new issue is created. This module parses that payload and forwards
a formatted message to the configured Slack channel.

This Flask app runs in a background thread alongside the Bolt Socket Mode app.
"""

import logging
import os

from flask import Flask, Response, request, jsonify

logger = logging.getLogger(__name__)

# Populated by main.py after the Bolt app is initialised
_slack_client = None
_channel = None


def init(slack_client, channel: str) -> None:
    """Inject the Slack WebClient and target channel. Called from main.py."""
    global _slack_client, _channel
    _slack_client = slack_client
    _channel = channel


webhook_app = Flask(__name__)


@webhook_app.post("/youtrack/webhook")
def youtrack_webhook() -> Response:
    """Receive a YouTrack webhook POST and publish to Slack."""
    # Lazy import to avoid circular dependency at module load time
    from utils.formatters import new_issue_blocks

    payload = request.get_json(force=True, silent=True) or {}
    logger.debug("Received YouTrack webhook: %s", payload)

    # YouTrack wraps the issue under different keys depending on version/event type
    issue = (
        payload.get("issue")
        or payload.get("data", {}).get("issue")
        or payload  # some configurations send the issue object directly
    )

    event_type = payload.get("eventType") or payload.get("event", "")
    # Only act on new-issue events; ignore updates/deletes if mixed into same endpoint
    if event_type and "created" not in event_type.lower() and "new" not in event_type.lower():
        return jsonify({"status": "ignored", "eventType": event_type}), 200

    if not _slack_client or not _channel:
        logger.error("Slack client not initialised in webhook handler")
        return jsonify({"error": "bot not ready"}), 503

    try:
        blocks = new_issue_blocks(issue)
        _slack_client.chat_postMessage(channel=_channel, blocks=blocks, text=f"New issue: {issue.get('summary', '')}")
    except Exception:
        logger.exception("Failed to post YouTrack webhook notification to Slack")
        return jsonify({"error": "slack post failed"}), 500

    return jsonify({"status": "ok"}), 200
