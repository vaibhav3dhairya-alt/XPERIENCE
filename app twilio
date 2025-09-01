from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import os

# Import the chatbot logic from your existing file
from xperience_chatbot import chatbot_reply

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    """
    Handles incoming WhatsApp messages via Twilio.
    """
    # Get the message from the user
    incoming_msg = request.values.get('Body', '').lower()
    # Get the user's phone number to maintain conversation state
    sender_id = request.values.get('From', '')

    print(f"Received message '{incoming_msg}' from {sender_id}")

    # --- Core Logic ---
    # Get the reply from your chatbot brain (xperience_chatbot.py)
    bot_response_text = chatbot_reply(sender_id, incoming_msg)

    # --- Twilio Response ---
    # Create a TwiML response object to build our reply
    resp = MessagingResponse()
    
    # Add the chatbot's message to the response
    resp.message(bot_response_text)

    return str(resp)

if __name__ == '__main__':
    # This setup allows the app to be run by a hosting service like Render.
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

