# gitbot-hackclub-slack-slackbot-github-ollama-llms
A slackbot that can chat with you, give your slack info(public or private), and give your github info


GitBot is a Slack bot that can:
- 🔍 Fetch a user's top GitHub repositories
- 🤖 Chat with a local Ollama-powered LLM (like LLaMA3)
- 👤 Display Slack user info via a `/slack-me` slash command

Built with Python, Slack Bolt, Flask, and Ollama.

---

## 📦 Features

- `/slack-me`: Get detailed info about yourself on Slack.
- `my repos`: Ask the bot to show your top GitHub repos.
- `--chat [prompt]`: Have a conversation with a local Ollama LLM.

---

## 🧠 Requirements

- Python 3.9+
- [Ollama](https://ollama.com/) installed and running locally
- A Slack App with:
  - Socket Mode enabled
  - `chat:write`, `commands`, `users:read`, `app_mentions:read` scopes
- GitHub access (public API)

---

## ⚙️ Setup

### 1. Clone the repo

```bash
git clone https://github.com/yourusername/gitbot.git
cd gitbot
```

### 2. Create .env from template

```bash
cp .env.example .env
```

### 3. Fill in your .env

```bash
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
SLACK_APP_TOKEN=xapp-your-slack-app-level-token
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Run your bot

```bash
python main.py
```

### 6. For Flask-based endpoints, run
 ```bash
 python server.py
 ```

 ### LLM via Ollama

 Make sure to run the desired model before using chat:

 ```bash
 ollama run llama3.2
 ```

 ### Test chat functionality

 ```bash
 python test_llm.py
 ```

 