import os
from flask import Flask, request
from slackeventsapi import SlackEventAdapter
from slack import WebClient
from dotenv import load_dotenv
from lib.model import prompt_model
from lib.vectorize import download_pdf_from_url
import json

# Load the Token from .env file
load_dotenv()

# Initialize Flask app and Slack Event Adapter
app = Flask(__name__)
slack_events_adapter = SlackEventAdapter(
    os.environ["SLACK_SIGNING_SECRET"], "/slack/events", app
)

# Initialize Slack API client
slack_token = os.environ["SLACK_API_TOKEN"]  # Replace with your Slack API token
client = WebClient(token=slack_token)
BOT_ID = client.api_call("auth.test")['user_id']

prev_msg_id = None

# Event callback
@slack_events_adapter.on("app_mention")
def handle_message(payload):
    global prev_msg_id
    
    event = payload.get("event", {})
    channel_id = event.get("channel")
    user_id = event.get("user")
    message_text = event.get("text")
    
    user_info = client.users_info(user=user_id)
    username = user_info["user"]["real_name"]
    
    new_message = message_text.replace("<@U05FQLC7DMH> ", "").strip()
    
    print(event)
    
    current_msg_id = event.get("client_msg_id")
    
    if prev_msg_id == current_msg_id:
        prev_msg_id = current_msg_id
        return
    
    prev_msg_id = current_msg_id
    
    if username != "Donna" and user_id != None and BOT_ID != user_id:
        llm_response = prompt_model(username, new_message)
        client.chat_postMessage(channel=channel_id, text=llm_response, blocks=[{"type": "section", "text": {"type": "mrkdwn", "text": llm_response}}])



# Event handler for file shared events
@slack_events_adapter.on("file_shared")
def handle_file_shared(event_data):
    file_id = event_data["event"]["file_id"]
    
    # Retrieve file information using the API client
    file_info = client.files_info(file=file_id)
    file_url = file_info["file"]["url_private"]
    
    channel_id = event_data["event"]["channel_id"]

    # Send a custom message with buttons
    client.chat_postMessage(
        channel=channel_id,
        text="Looks like you shared a file. Would you like me to store it on my desk?",
        attachments=[
            {
                "fallback": "You are unable to confirm the file.",
                "callback_id": "file_confirmation",
                "actions": [
                    {
                        "name": "confirm",
                        "text": "Confirm",
                        "type": "button",
                        "value": file_url
                    },
                    {
                        "name": "cancel",
                        "text": "Cancel",
                        "type": "button",
                        "value": "cancel"
                    }
                ]
            }
        ]
    )
        
        
@app.route("/slack/actions", methods=["POST"])
def slack_actions():
    serialized = request.form.get("payload")
    payload = json.loads(serialized)

    action = payload["actions"][0]
    user_id = payload["user"]["id"]
    

    if action["name"] == "confirm" and action["value"] != "cancel":
        file_url = action["value"]
        print(f"Confirmed file URL: {file_url}")

        # Send a message to the user confirming the file
        client.chat_postEphemeral(
            channel=payload["channel"]["id"],
            user=user_id,
            text=f"You confirmed the file. URL: {file_url}"
        )
        
    elif action["name"] == "cancel":
        #Send a message to the user indicating cancellation
        client.chat_postEphemeral(
            channel=payload["channel"]["id"],
            user=user_id,
            text="You canceled the file confirmation."
        )
        
    return "", 200


# Start the Flask server
if __name__ == "__main__":
    app.run(port=3000, debug=True)