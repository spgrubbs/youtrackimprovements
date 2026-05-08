"""Entry point for the YouTrack–Slack bot.

Starts two concurrent background threads alongside the Slack Bolt Socket Mode app:
  1. A polling loop that checks YouTrack every 30 seconds for new issues and
     posts them to Slack — no YouTrack webhook configuration required.
  2. A Flask server kept available for future webhook use (e.g. Railway deployment).
"""

import logging
import os
import threading
import time

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

import handlers.commands as commands_module
import handlers.actions as actions_module

# ---------------------------------------------------------------------------
# Slack Bolt app
# ---------------------------------------------------------------------------

app = App(token=os.environ["SLACK_BOT_TOKEN"])

commands_module.register(app)
actions_module.register(app)

_channel = os.environ.get("SLACK_YOUTRACK_CHANNEL", "#youtrack-activity")
_poll_interval = int(os.environ.get("POLL_INTERVAL_SECONDS", 30))


# ---------------------------------------------------------------------------
# YouTrack polling thread
# ---------------------------------------------------------------------------

def _poll_new_issues():
    """Check YouTrack every POLL_INTERVAL_SECONDS for newly created issues."""
    from services.youtrack import get_recent_issues
    from utils.formatters import new_issue_blocks

    # Record startup time; only notify about issues created after this point.
    last_check_ms = int(time.time() * 1000)
    logger.info("YouTrack poller started — checking every %ds for new issues", _poll_interval)

    while True:
        time.sleep(_poll_interval)
        try:
            issues = get_recent_issues()
            new_issues = [i for i in issues if (i.get("created") or 0) > last_check_ms]
            for issue in reversed(new_issues):  # post oldest-first
                blocks = new_issue_blocks(issue)
                app.client.chat_postMessage(
                    channel=_channel,
                    blocks=blocks,
                    text=f"New issue: {issue.get('summary', '')}",
                )
                logger.info("Posted new issue %s to Slack", issue.get("id"))
            last_check_ms = int(time.time() * 1000)
        except Exception:
            logger.exception("Error polling YouTrack for new issues")


if __name__ == "__main__":
    poll_thread = threading.Thread(target=_poll_new_issues, daemon=True)
    poll_thread.start()

    logger.info("Starting Slack Bolt app in Socket Mode…")
    handler = SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
    handler.start()  # blocks until process is killed
