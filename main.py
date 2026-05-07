"""Entry point for the YouTrack–Slack bot.

Starts two concurrent servers:
  1. Slack Bolt app in Socket Mode (no inbound port needed)
  2. Flask webhook listener for inbound YouTrack events (default port 5000)
"""

import logging
import os
import threading

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
from handlers.webhooks import webhook_app, init as init_webhook

# ---------------------------------------------------------------------------
# Slack Bolt app
# ---------------------------------------------------------------------------

app = App(token=os.environ["SLACK_BOT_TOKEN"])

commands_module.register(app)
actions_module.register(app)

# ---------------------------------------------------------------------------
# Wire webhook handler with the Slack client and target channel
# ---------------------------------------------------------------------------

_channel = os.environ.get("SLACK_YOUTRACK_CHANNEL", "#youtrack-activity")
init_webhook(slack_client=app.client, channel=_channel)


# ---------------------------------------------------------------------------
# Webhook server thread
# ---------------------------------------------------------------------------

def _run_webhook_server():
    port = int(os.environ.get("WEBHOOK_PORT", 5000))
    logger.info("Starting YouTrack webhook listener on port %d", port)
    # Use_reloader=False is required when Flask runs inside a thread
    webhook_app.run(host="0.0.0.0", port=port, use_reloader=False)


if __name__ == "__main__":
    webhook_thread = threading.Thread(target=_run_webhook_server, daemon=True)
    webhook_thread.start()

    logger.info("Starting Slack Bolt app in Socket Mode…")
    handler = SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
    handler.start()  # blocks until process is killed
