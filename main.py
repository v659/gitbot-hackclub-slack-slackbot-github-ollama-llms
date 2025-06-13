from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import requests
import os, certifi
import re
import ollama
from dotenv import load_dotenv
load_dotenv()  # This loads environment variables from .env

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN")

os.environ['SSL_CERT_FILE'] = certifi.where()

# Initialize the Slack app
app = App(token=SLACK_BOT_TOKEN)

# In-memory user session (you can use a DB instead)
user_sessions = {}


# Trigger command
@app.message("my repos")
def ask_for_github_username(message, say):
    user_id = message['user']
    user_sessions[user_id] = {"awaiting_username": True}
    say(f"<@{user_id}>, what's your GitHub username?")


@app.message(re.compile(".*"))
def handle_message(message, say):
    user_id = message['user']
    text = message['text'].strip().lower()  # Lowercase for consistent comparison

    # --- GITHUB TRIGGER ---
    if text == "my repos":
        user_sessions[user_id] = {"awaiting_username": True}
        say(f"<@{user_id}>, what's your GitHub username?")
        return

    # --- GITHUB FLOW ---
    if user_id in user_sessions and user_sessions[user_id].get("awaiting_username"):
        github_username = text
        user_sessions[user_id]["awaiting_username"] = False

        say(f"Looking up GitHub repos for *{github_username}*...")
        url = f"https://api.github.com/users/{github_username}/repos"
        response = requests.get(url)

        if response.status_code != 200:
            say("Couldn't fetch repositories. Are you sure the username is correct?")
            return

        repos = response.json()
        if not repos:
            say(f"No public repositories found for {github_username}.")
            return

        repos.sort(key=lambda r: r.get("stargazers_count", 0), reverse=True)
        top_repos = repos[:5]
        result = f"*Top repositories for `{github_username}`:*"
        for repo in top_repos:
            result += f"\n• *{repo['name']}* – ⭐ {repo['stargazers_count']} | 🍴 {repo['forks_count']} | {repo['html_url']}"
        say(result)
        return

@app.command("/slack-me")
def handle_whoami_command(ack, body, client, respond):
    ack()  # Acknowledge the slash command immediately

    user_id = body["user_id"]
    team_id = body["team_id"]

    try:
        user_info = client.users_info(user=user_id)
        profile = user_info["user"]["profile"]

        real_name = profile.get("real_name", "N/A")
        email = profile.get("email", "N/A")
        timezone = user_info["user"].get("tz", "N/A")

        respond(f"""👤 *Slack User Info*:
        • User ID: `{user_id}`
        • Team ID: `{team_id}`
        • Username: <@{user_id}>
        • Real Name: `{real_name}`
        • Email: `{email}`
        • Timezone: `{timezone}`
        """)

    except Exception as e:
        respond(f"⚠️ Error retrieving user info: `{e}`")


@app.command("/slack-me-public")
def handle_public_whoami(ack, body, client, respond):
    ack()  # Acknowledge the slash command immediately

    user_id = body["user_id"]
    team_id = body["team_id"]
    channel_id = body["channel_id"]

    try:
        user_info = client.users_info(user=user_id)
        profile = user_info["user"]["profile"]

        real_name = profile.get("real_name", "N/A")
        email = profile.get("email", "N/A")
        timezone = user_info["user"].get("tz", "N/A")

        client.chat_postMessage(
            channel=channel_id,
            text=f"""👤 *Slack User Info*:
• User ID: `{user_id}`
• Team ID: `{team_id}`
• Username: <@{user_id}>
• Real Name: `{real_name}`
• Email: `{email}`
• Timezone: `{timezone}`
"""
        )

    except Exception as e:
        respond(f"⚠️ Error retrieving user info: `{e}`")




@app.event("app_mention")
def handle_app_mention(body, say):
    user = body["event"]["user"]
    text = body["event"]["text"]

    # Strip the bot mention to get clean prompt
    cleaned_text = re.sub(r"<@[^>]+>\s*", "", text).strip()

    say(f"🧠 LLaMA3 is thinking...\n> `{cleaned_text}`")
    try:
        response = ollama.chat(model='llama3.2', messages=[
            {'role': 'user', 'content': cleaned_text}
        ])
        say(response['message']['content'])
    except Exception as e:
        say(f"⚠️ Error: `{e}`")

# Start the bot
if __name__ == "__main__":
    handler = SocketModeHandler(app, SLACK_APP_TOKEN)
    handler.start()
