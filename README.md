# YouTrack–Slack Bot — Setup Guide

This bot connects your YouTrack project tracker to Slack so your team can:
- Get an automatic Slack message whenever a new YouTrack task is created
- Create YouTrack tasks directly from Slack with `/create-task`
- Attach meeting notes from Otter.ai to a YouTrack ticket with `/append-notes`

---

## What you'll need before starting

- A computer that stays on (the bot runs on it)
- Python installed (see Step 1)
- Access to your team's Slack workspace as an admin (or ask your Slack admin)
- Your YouTrack login info

---

## Step 1 — Install Python

1. Go to **https://www.python.org/downloads/**
2. Click the big yellow "Download Python" button
3. Run the installer — on the first screen, **check the box that says "Add Python to PATH"** before clicking Install
4. When it finishes, open a Terminal (Mac) or Command Prompt (Windows) and type:
   ```
   python --version
   ```
   You should see something like `Python 3.12.0`. If you do, Python is installed correctly.

> **How to open a Terminal / Command Prompt**
> - **Mac:** Press `Command + Space`, type `Terminal`, press Enter
> - **Windows:** Press the Windows key, type `cmd`, press Enter

---

## Step 2 — Download the bot files

1. Download this project as a ZIP file (there's a button on the GitHub page)
2. Unzip it somewhere easy to find, like your Desktop
3. In your Terminal / Command Prompt, navigate into that folder by typing:
   ```
   cd Desktop/youtrack-slack-bot
   ```
   *(Adjust the path if you unzipped it somewhere else)*

---

## Step 3 — Install the bot's dependencies

Think of this like installing apps the bot needs to run. In your Terminal, type:

```
pip install -r requirements.txt
```

Wait for it to finish. You'll see a lot of text scroll by — that's normal.

---

## Step 4 — Create your Slack App

This is the part that takes the most steps, but just follow along one click at a time.

1. Go to **https://api.slack.com/apps** and sign in with your Slack account
2. Click **"Create New App"**
3. Choose **"From scratch"**
4. Give it a name (e.g. `YouTrack Bot`) and pick your workspace, then click **Create App**

### Turn on Socket Mode
5. In the left sidebar, click **"Socket Mode"**
6. Toggle it **On**
7. It will ask you to name a token — type `youtrack-bot-token` and click **Generate**
8. **Copy the token that appears** — it starts with `xapp-`. Save it somewhere (a notes app is fine). This is your `SLACK_APP_TOKEN`.

### Give the bot permissions
9. In the left sidebar, click **"OAuth & Permissions"**
10. Scroll down to **"Bot Token Scopes"** and click **"Add an OAuth Scope"**
11. Add these three scopes one at a time:
    - `chat:write`
    - `commands`
    - `im:write`
12. Scroll back to the top and click **"Install to Workspace"**, then click **Allow**
13. **Copy the "Bot User OAuth Token"** — it starts with `xoxb-`. This is your `SLACK_BOT_TOKEN`.

### Add slash commands
14. In the left sidebar, click **"Slash Commands"**
15. Click **"Create New Command"** and fill in:
    - Command: `/create-task`
    - Request URL: `https://placeholder.example.com` *(doesn't matter, Socket Mode ignores this)*
    - Short description: `Create a YouTrack task`
    - Click Save
16. Click **"Create New Command"** again:
    - Command: `/append-notes`
    - Request URL: `https://placeholder.example.com`
    - Short description: `Append Otter.ai notes to a ticket`
    - Click Save

### Reinstall the app
17. Go back to **"OAuth & Permissions"** and click **"Reinstall to Workspace"** → Allow
    *(Adding slash commands requires a reinstall)*

---

## Step 5 — Get your YouTrack token

1. Log in to YouTrack at **https://www.youtrackradteam.com:8443**
2. Click your profile picture in the top-right corner
3. Click **"Profile"**
4. Click the **"Authentication"** tab (sometimes called "Account Security")
5. Under **"Permanent Tokens"**, click **"New token"**
6. Give it a name like `slack-bot` and click **Create**
7. **Copy the token immediately** — you won't be able to see it again

---

## Step 6 — Create your settings file

In the bot folder, you'll see a file called `.env.example`. Make a copy of it and name the copy `.env` (just `.env`, no "example").

> **On Mac/Windows:** You may need to show hidden files to see `.env` files. Alternatively, just open the `.env.example` file in a text editor (Notepad on Windows, TextEdit on Mac), edit it, and save it as `.env`.

Open `.env` in a text editor and fill in your values. It looks like this:

```
SLACK_BOT_TOKEN=xoxb-...put your Bot Token here...
SLACK_APP_TOKEN=xapp-...put your App Token here...

YOUTRACK_URL=https://www.youtrackradteam.com:8443
YOUTRACK_TOKEN=perm:...put your YouTrack token here...

SLACK_YOUTRACK_CHANNEL=#youtrack-activity

OTTER_API_KEY=otterai_d9ANdECFNmcv2xQ-OzpKspS8tbw-Dzw5Tf7C3JYAvl4

WEBHOOK_PORT=5000
```

Replace the placeholder text with your actual tokens. Save the file.

> **Important:** Never share this file or upload it anywhere. It contains passwords.

---

## Step 7 — Create the Slack channel

In Slack, create a channel called `#youtrack-activity` (or whatever you put in `SLACK_YOUTRACK_CHANNEL`). Then **invite the bot to that channel**:

1. Open the channel in Slack
2. Type `/invite @YouTrack Bot` and press Enter

---

## Step 8 — Run the bot

In your Terminal (make sure you're still in the bot folder), type:

```
python main.py
```

You should see something like:
```
Starting YouTrack webhook listener on port 5000
Starting Slack Bolt app in Socket Mode…
⚡️ Bolt app is running!
```

The bot is now running. **Leave this Terminal window open** — closing it stops the bot.

---

## Step 9 — Automatic Slack notifications for new issues

**No YouTrack configuration needed.** The bot automatically checks YouTrack every 30 seconds for new issues. When it finds one, it posts a message to `#youtrack-activity` in Slack.

To test it, just create a new issue in YouTrack. Within 30 seconds you should see it appear in Slack.

That's it for this step — nothing to set up.

---

## Daily use

- **To start the bot:** Open Terminal, go to the bot folder, run `python main.py`
- **To stop the bot:** Click the Terminal window and press `Control + C`
- **To create a task from Slack:** Type `/create-task` in any Slack channel
- **To attach meeting notes:** Type `/append-notes` in any Slack channel

---

## Something went wrong?

| Problem | Try this |
|---------|----------|
| `python: command not found` | Python isn't installed or wasn't added to PATH — redo Step 1 |
| `No module named slack_bolt` | Run `pip install -r requirements.txt` again |
| Bot doesn't respond in Slack | Make sure the Terminal with `python main.py` is still open |
| Slack notifications not appearing | Wait up to 30 seconds — the bot polls on a timer. If still nothing, check the Terminal for error messages. |
| `SLACK_BOT_TOKEN` error on startup | Double-check your `.env` file — no spaces around the `=` sign |
