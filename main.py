from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import requests
import os, certifi
import re
import ollama
from dotenv import load_dotenv
from deep_translator import GoogleTranslator
from personalities import personalities

user_personalities = {}

load_dotenv()  # This loads environment variables from .env

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN")

os.environ['SSL_CERT_FILE'] = certifi.where()

# Initialize the Slack app
app = App(token=SLACK_BOT_TOKEN)

# In-memory user session (you can use a DB instead)
user_sessions = {}

@app.command("/change-personality")
def change_personality(ack, respond, body):
    ack()
    user_id = body["user_id"]
    text = body.get("text", "").strip().lower()

    if text not in personalities:
        available = ", ".join(personalities.keys())
        respond(f"⚠️ Unknown personality. Try one of: `{available}`")
        return

    user_personalities[user_id] = text
    respond(f"🎭 Personality changed to *{text}* for <@{user_id}>.")


def translate_text(text, target='en'):
    try:
        translated = GoogleTranslator(source='auto', target=target).translate(text)
        return translated
    except Exception as e:
        return f"⚠️ Translation error: {e}"

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



@app.command("/translate")
def handle_translate_command(ack, respond, command):
    ack()

    text = command.get("text", "")
    if not text:
        respond("❗ Please provide text to translate. Example: `/translate Bonjour le monde`")
        return

    try:
        translated = GoogleTranslator(source='auto', target='en').translate(text)
        respond(f"🌍 *Translation:*\n> `{translated}`")
    except Exception as e:
        respond(f"⚠️ Error translating: `{e}`")



@app.command("/trans-public")
def handle_trans_public(ack, body, client, respond):
    ack()

    user_id = body["user_id"]
    channel_id = body["channel_id"]
    text = body.get("text", "").strip()

    if not text:
        respond("❌ Usage: `/trans-public [language_code] [text]` (e.g., `/trans-public en Bonjour le monde`)")
        return

    try:
        parts = text.split(" ", 1)
        if len(parts) != 2:
            respond("❌ Please provide a language code and the text to translate.")
            return

        lang, to_translate = parts
        translated = GoogleTranslator(source="auto", target=lang).translate(to_translate)

        client.chat_postMessage(
            channel=channel_id,
            text=(
                f"🌍 <@{user_id}> said:\n> `{to_translate}`\n"
                f"🔁 Translated to *{lang}*:\n> `{translated}`"
            )
        )
    except Exception as e:
        respond(f"⚠️ Translation error: `{e}`")


@app.event("app_mention")
def handle_app_mention(body, say, logger):
    user = body["event"]["user"]
    text = body["event"]["text"]

    # Strip the bot mention to extract clean prompt
    cleaned_text = translate_text(re.sub(r"<@[^>]+>\s*", "", text).strip())
    logger.info(f"[MENTION] From user {user}: '{cleaned_text}'")

    # Handle 'my repos' directly
    if cleaned_text.lower() == 'my repos':
        return  # Handled elsewhere

    # Determine personality
    personality = user_personalities.get(user, "default")
    system_prompt_text = personalities.get(personality, personalities["default"])["system_prompt"]

    say(f"🤖 (*{personality}*) Thinking...")

    try:
        response = ollama.chat(
            model='teen-bot',
            messages=[
                {'role': 'system', 'content': system_prompt_text},
                {'role': 'user', 'content': cleaned_text}
            ]
        )
        content = response.get("message", {}).get("content", None)
        if content:
            say(content)
        else:
            logger.warning("Ollama response missing 'message.content'")
            say("⚠️ LLaMA didn’t reply as expected.")

    except Exception as e:
        logger.error(f"Ollama call failed: {e}")
        say(f"⚠️ Error talking to LLaMA: `{e}`")



# Start the bot
if __name__ == "__main__":
    handler = SocketModeHandler(app, SLACK_APP_TOKEN)
    handler.start()
