"""
Slack bot that connect chat room with slack channel

Setup:
    In this file you need to setup:
        PORT = 5555             - slack server will run on this port
        CHAT_CHANNEL = "chat"   - slack channel name

    Provide correct SLACK_TOKEN and SLACK_SIGNING_SECRET in bots/.slack_env

    Need to add this bot to chat room in common.py file:
        Bot("http://127.0.0.1:5555/messages"),   # slack bot
        (already added, just change port if you change it in this file)

    Bot permissions in slack:
        - chat:write
        - im:read
        - im:write
        - users:read

Bot requirements:
    Bot should provide url that support GET and POST requests.
    GET - return list of new messages in format:
        {
            "messages": [list_of_messages]
        }
    POST - receive message in string format that should be sent to slack channel

"""

import os
from typing import List

import slack
from dotenv import load_dotenv
from flask import Flask, request
from slack.errors import SlackApiError
from slackeventsapi import SlackEventAdapter

# Bot settings
PORT = 5555
CHAT_CHANNEL = "chat"
# End bot settings

messages_in: List[str] = []  # messages from slack to chat

load_dotenv(os.path.dirname(os.path.abspath(__file__)) + "/.slack_env")
SLACK_TOKEN = os.environ.get("SLACK_TOKEN")
SLACK_SIGNING_SECRET = os.environ.get("SLACK_SIGNING_SECRET")

app = Flask(__name__)
slack_event_adapter = SlackEventAdapter(SLACK_SIGNING_SECRET, '/slack/events', app)


@app.route('/messages', methods=['GET'])
def get_messages():
    """
    Return new messages
    """
    response = {"messages": messages_in.copy()}
    messages_in.clear()
    return response


@app.route('/messages', methods=['POST'])
def send_message():
    """
    Receive message
    """
    send_public_message_to_slack(request.data.decode())
    return "The message was successfully received"


def set_public_chat_id(client):
    """
    Returns id for CHAT_CHANNEL channel
    """
    response = client.conversations_list()
    channels = response["channels"]
    for channel in channels:
        if channel["name"] == CHAT_CHANNEL:
            return channel["id"]
    raise ValueError(f"Channel with name '{CHAT_CHANNEL}' was not found!")


def get_user_name(user_id):
    """
    Returns username by user_id
    Requires users:read permission for that
    """
    try:
        username = "[{}] ".format(slack_client.users_info(user=user_id).get("user").get("real_name"))
    except SlackApiError:
        username = ""
    return username


def is_public_channel(event):
    """
    Check that it is public channel (not private message)
    """
    channel_type = event.get('channel_type')
    if channel_type == "channel":
        return True
    return False


def send_message_to_slack(channel_id, text):
    """
    Send message to slack channel or private message
    """
    slack_client.chat_postMessage(channel=channel_id, text=text)


def send_public_message_to_slack(text):
    """
    Send message to slack channel
    """
    send_message_to_slack(public_chat_id, text)


def answer_on_private_msg(channel_id, text):
    """
    Simple AI to answer on private messages
    """
    greetings = ["hi", "hello", "привет"]
    goodbyes = ["bye", "see you", "пока", "до свидания"]
    if any(map(lambda msg: msg.lower() in text.lower(), greetings)):
        send_message_to_slack(channel_id, "Hi!")
    elif "?" in text:
        send_message_to_slack(channel_id, "Answer to the Ultimate Question of Life, the Universe, and Everything is 42")
    elif any(map(lambda msg: msg.lower() in text.lower(), goodbyes)):
        send_message_to_slack(channel_id, "Bye!")
    else:
        send_message_to_slack(channel_id, "I'm sorry, but I don't know what to say...")


@slack_event_adapter.on('message')
def message(payload):
    """
    Event Subscriptions Listener
    """
    event = payload.get('event', {})
    user_id = event.get('user')
    if bot_id == user_id:
        return

    text = event.get('text')
    if is_public_channel(event):
        messages_in.append(get_user_name(user_id) + text)
    else:
        channel_id = event.get('channel')
        answer_on_private_msg(channel_id, text)


if __name__ == '__main__':
    slack_client = slack.WebClient(token=SLACK_TOKEN)
    bot_id = slack_client.api_call("auth.test")["user_id"]
    public_chat_id = set_public_chat_id(slack_client)
    app.run(debug=True, port=PORT)
