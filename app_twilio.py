from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import os

# Import the chatbot logic from your existing file
from xperience_chatbot import chatbot_reply

app = Flask(__name__)

# This function creates the message with the three tappable buttons
def create_welcome_message():
    """Creates a TwiML response with the main menu as Quick Reply buttons."""
    resp = MessagingResponse()
    message_body = (
        "Welcome to Xperience, your exploration companion for Jamshedpur! 🧭\n\n"
        "Please choose an option:"
    )
    
    # The 'persistent_action' parameter is the modern way to create Quick Reply buttons
    # Note: WhatsApp limits you to a maximum of 3 reply buttons.
    resp.message(
        body=message_body,
        persistent_action=[
            'whatsapp:quick_reply:Personalize My Experience',
            'whatsapp:quick_reply:Browse Categories',
            'whatsapp:quick_reply:Surprise Me!'
        ]
    )
    return str(resp)

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handles incoming WhatsApp messages via Twilio."""
    incoming_msg = request.values.get('Body', '').strip()
    sender_id = request.values.get('From', '')

    print(f"Received message '{incoming_msg}' from {sender_id}")

    # --- Core Logic ---
    # Get the reply from your chatbot brain
    bot_response = chatbot_reply(sender_id, incoming_msg)

    # --- Twilio Response ---
    if bot_response == "SEND_WELCOME_WITH_BUTTONS":
        return create_welcome_message()
    else:
        # For all other text responses, send a simple message
        resp = MessagingResponse()
        resp.message(bot_response)
        return str(resp)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

