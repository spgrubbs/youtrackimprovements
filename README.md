# YouTrack–Slack Bot

A Python Slack bot that connects a self-hosted YouTrack instance with Slack. Built with `slack_bolt` in Socket Mode — no public URL or open inbound port is required for the Slack connection itself.

## Features

| Feature | How to trigger |
|---------|---------------|
| **YouTrack → Slack notifications** | YouTrack POSTs a webhook to the bot; a formatted message appears in `#youtrack-activity` |
| **Slack → YouTrack task creation** | `/create-task` slash command opens a modal |
| **Otter.ai → YouTrack notes** | `/append-notes` lets you pick a meeting and attach its AI summary to a ticket |

---

## Prerequisites

- Python 3.11+
- A Slack app with Bot Token Scopes: `chat:write`, `commands`, `im:write`
- Slack app with Socket Mode enabled (generates an App-Level Token with `connections:write`)
- Slash commands `/create-task` and `/append-notes` configured in the Slack app settings
- A YouTrack permanent token with issue read/write access
- (Optional) An Otter.ai enterprise API key for the notes feature

---

## Setup

### 1. Clone and install dependencies

```bash
git clone <repo-url>
cd youtrack-slack-bot
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env`:

```
SLACK_BOT_TOKEN=xoxb-...          # Bot User OAuth Token
SLACK_APP_TOKEN=xapp-...          # App-Level Token (Socket Mode)
YOUTRACK_URL=https://www.youtrackradteam.com:8443
YOUTRACK_TOKEN=perm:...           # YouTrack permanent token
SLACK_YOUTRACK_CHANNEL=#youtrack-activity
OTTER_API_KEY=otterai_...
WEBHOOK_PORT=5000
```

> **SSL note:** The YouTrack client sends `verify=False` by default because the server uses a self-signed certificate. To use a CA bundle instead, set `YOUTRACK_CA_BUNDLE=/path/to/ca.pem`.

### 3. Run the bot

```bash
python main.py
```

You should see:
```
Starting YouTrack webhook listener on port 5000
Starting Slack Bolt app in Socket Mode…
⚡️ Bolt app is running!
```

---

## Configuring the YouTrack Webhook

YouTrack needs to be able to reach `http://<your-machine>:5000/youtrack/webhook`.

### During local development — use ngrok

```bash
# In a separate terminal
ngrok http 5000
```

Copy the `https://xxxx.ngrok.io` URL and in YouTrack:

1. Go to **Administration → Notifications → Webhooks**
2. Click **New webhook**
3. Set URL to `https://xxxx.ngrok.io/youtrack/webhook`
4. Event: **Issue created**
5. Save and click **Test**

The bot will post a formatted message to `#youtrack-activity` in Slack.

### In production / always-on deployment

Point the YouTrack webhook directly at your machine's IP/hostname on port 5000 (or whatever `WEBHOOK_PORT` is set to). Make sure the port is reachable from the YouTrack server.

---

## Slack App Configuration

### Required OAuth scopes (Bot Token)

- `chat:write`
- `commands`
- `im:write`

### Slash commands to register in Slack App settings

| Command | Description |
|---------|-------------|
| `/create-task` | Create a YouTrack issue via a modal |
| `/append-notes` | Append an Otter.ai meeting summary to a YouTrack ticket |

Set the **Request URL** for slash commands to any placeholder — Socket Mode intercepts them before they hit HTTP.

### Event subscriptions

Not required for this MVP (Socket Mode handles everything).

---

## Project Structure

```
youtrack-slack-bot/
├── .env                   # Credentials (never commit)
├── .env.example           # Template
├── requirements.txt
├── main.py                # Entry point
├── handlers/
│   ├── commands.py        # /create-task, /append-notes
│   ├── actions.py         # Modal submission callbacks
│   └── webhooks.py        # Flask endpoint for YouTrack → Slack
├── services/
│   ├── youtrack.py        # YouTrack REST API client
│   └── otter.py           # Otter.ai API client
└── utils/
    └── formatters.py      # Slack Block Kit message builders
```

---

## Error Handling Notes

This is an MVP focused on the happy path. The following areas should have
more robust error handling before production use:

- YouTrack API errors (rate limits, auth failures) in `services/youtrack.py`
- Otter.ai API pagination and auth expiry in `services/otter.py`
- Slack API retries in `handlers/webhooks.py`
- Webhook signature verification (add a secret token to confirm requests are from YouTrack)
- Input validation on modal fields before hitting the YouTrack API
