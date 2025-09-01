from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
import os

# Import the chatbot logic from your existing file
from xperience_chatbot import chatbot_reply, CATEGORIES_MAP

app = Flask(__name__)

# It's better to get Twilio credentials from environment variables for security
# For Render, you can set these in the "Environment" tab for your service
ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
TWILIO_NUMBER = os.environ.get('TWILIO_NUMBER') # e.g., 'whatsapp:+14155238886'

client = Client(ACCOUNT_SID, AUTH_TOKEN)

def send_welcome_message(to_number):
    """Sends the main menu with Reply Buttons."""
    message_body = "Welcome to Xperience, your exploration companion for Jamshedpur! 🧭\n\nHow can I help you today?"
    
    # Using the Twilio REST Client to send a message with interactive buttons
    client.messages.create(
        from_=TWILIO_NUMBER,
        to=to_number,
        body=message_body,
        actions=[
            {'type': 'QUICK_REPLY', 'reply': {'id': 'personalize_1', 'title': 'Personalize My Experience'}},
            {'type': 'QUICK_REPLY', 'reply': {'id': 'browse_1', 'title': 'Browse Categories'}},
            {'type': 'QUICK_REPLY', 'reply': {'id': 'surprise_1', 'title': 'Surprise Me!'}}
        ]
    )

def send_category_list(to_number):
    """Sends the category options as a List Message."""
    # The sections structure is required by the API
    sections = [{
        "title": "Experience Types",
        "rows": [{"id": f"cat_{i+1}", "title": cat.title(), "description": ""} for i, cat in enumerate(CATEGORIES_MAP.keys())]
    }]

    client.messages.create(
        from_=TWILIO_NUMBER,
        to=to_number,
        body="Please choose a category from the list below.",
        action="LIST",
        action_button_title="View Categories",
        action_sections=sections
    )

def send_final_response(to_number, body_text):
    """Sends the final result with a thank you and a Main Menu button."""
    # Append the concluding message to the list of places
    final_message = body_text + "\nThank you for using Xperience! ✨"

    client.messages.create(
        from_=TWILIO_NUMBER,
        to=to_number,
        body=final_message,
        actions=[
            {'type': 'QUICK_REPLY', 'reply': {'id': 'main_menu_1', 'title': 'Main Menu'}}
        ]
    )


@app.route('/webhook', methods=['POST'])
def webhook():
    """Handles incoming WhatsApp messages via Twilio."""
    incoming_msg = request.values.get('Body', '').lower()
    sender_id = request.values.get('From', '')

    print(f"Received message '{incoming_msg}' from {sender_id}")

    # --- Core Logic ---
    bot_response = chatbot_reply(sender_id, incoming_msg)
    
    # --- Twilio Response ---
    # Using an empty TwiML response as we are sending replies via the REST API now
    resp = MessagingResponse()

    # Check for special commands returned from the logic file
    if isinstance(bot_response, tuple) and bot_response[0] == "SEND_FINAL_RESPONSE":
        send_final_response(sender_id, bot_response[1])
    elif bot_response == "SEND_WELCOME":
        send_welcome_message(sender_id)
    elif bot_response == "SEND_CATEGORY_LIST":
        send_category_list(sender_id)
    else:
        # For standard text replies, we can use the simple TwiML response
        resp.message(bot_response)

    return str(resp)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

