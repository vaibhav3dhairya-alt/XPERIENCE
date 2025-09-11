# This is the core server code for your WhatsApp chatbot, written in Python using Flask.
# It now uses the Twilio REST API to send interactive messages with buttons and lists.

import os
from flask import Flask, request
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse

# --- Twilio Configuration ---
# Your Account SID and Auth Token are read from environment variables
# IMPORTANT: You must set these in your Render dashboard for the bot to work.
account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
client = Client(account_sid, auth_token)

app = Flask(__name__)

@app.route('/whatsapp', methods=['POST'])
def whatsapp_reply():
    """
    Handles incoming WhatsApp messages. It sends interactive messages using the
    Twilio REST API and returns an empty TwiML response to acknowledge the webhook.
    """
    incoming_msg = request.values.get('Body', '').strip()
    from_number = request.values.get('From')
    to_number = request.values.get('To')
    
    print(f"Received message: '{incoming_msg}' from {from_number}")

    # --- Chatbot Logic ---

    # Initial greeting or main menu request
    if 'hi' in incoming_msg.lower() or 'hello' in incoming_msg.lower():
        # This sends a message with three Quick Reply buttons.
        client.messages.create(
            from_=to_number,
            to=from_number,
            body="Hi there! Welcome to Xperience, your exploration companion for Jamshedpur. 🧭\n\nChoose a path:",
            # The 'actions' parameter is used to define the buttons.
            # WhatsApp only supports up to 3 reply buttons.
            actions=[
                {"type": "reply", "reply": {"id": "browse_cat", "title": "Browse 7 categories"}},
                {"type": "reply", "reply": {"id": "surprise_me", "title": "Surprise Me"}},
                {"type": "reply", "reply": {"id": "personalize", "title": "Personalize"}}
            ]
        )

    # User clicked "Browse 7 categories" button
    elif incoming_msg == 'Browse 7 categories':
         # This sends a "List Message" with all 7 categories.
        client.messages.create(
            from_=to_number,
            to=from_number,
            body="Great! Here are the 7 categories:",
            # The 'actions' parameter for a list is more complex.
            actions=[{
                "button": "Choose a Category",
                "sections": [{
                    "title": "Experience Buckets",
                    "rows": [
                        {"id": "cat_adventure", "title": "Adventure & Outdoors 🌲"},
                        {"id": "cat_dining", "title": "Dining & Food 🍔"},
                        {"id": "cat_getaways", "title": "Getaways & Nature 🏞️"},
                        {"id": "cat_cultural", "title": "Cultural & Shopping 🛍️"},
                        {"id": "cat_leisure", "title": "Entertainment & Leisure 🎬"},
                        {"id": "cat_sports", "title": "Sports & Fitness 🏋️"},
                        {"id": "cat_events", "title": "Events & Wellness ✨"},
                    ]
                }]
            }]
        )
    
    # User selected a category from the list
    elif incoming_msg == 'Adventure & Outdoors 🌲':
        reply_text = (
            "*Adventure & Outdoors* 🌲:\n\n"
            "*Jubilee Park*\n"
            "A central park with gardens, a zoo, and a laser show.\n"
            "Directions: https://maps.google.com/?q=Jubilee+Park,Jamshedpur\n\n"
            "*Dalma Wildlife Sanctuary*\n"
            "Known for its elephants and scenic trekking routes.\n"
            "Directions: https://maps.google.com/?q=Dalma+Wildlife+Sanctuary,Jamshedpur"
        )
        client.messages.create(from_=to_number, to=from_number, body=reply_text)

    elif incoming_msg == 'Dining & Food 🍔':
        reply_text = (
            "*Dining & Food* 🍔:\n\n"
            "*The Blue Diamond Restaurant*\n"
            "Popular for its North Indian and Chinese cuisine.\n"
            "Directions: https://maps.google.com/?q=The+Blue+Diamond+Restaurant,Jamshedpur\n\n"
            "*Dastarkhan*\n"
            "A well-regarded spot for authentic Mughlai dishes.\n"
            "Directions: https://maps.google.com/?q=Dastarkhan,Jamshedpur"
        )
        client.messages.create(from_=to_number, to=from_number, body=reply_text)
        
    elif incoming_msg == 'Getaways & Nature 🏞️':
        reply_text = (
            "*Getaways & Nature* 🏞️:\n\n"
            "*Dimna Lake*\n"
            "A beautiful artificial lake at the foothills of the Dalma hills, perfect for picnics and boating.\n"
            "Directions: https://maps.google.com/?q=Dimna+Lake,Jamshedpur\n\n"
            "*Hudco Lake*\n"
            "Located in the Telco Colony, it offers a serene environment and boating facilities.\n"
            "Directions: https://maps.google.com/?q=Hudco+Lake,Jamshedpur"
        )
        client.messages.create(from_=to_number, to=from_number, body=reply_text)
        
    # --- Placeholder responses for other options ---
    elif incoming_msg in ['Surprise Me', 'Personalize', 'Cultural & Shopping 🛍️', 'Entertainment & Leisure 🎬', 'Sports & Fitness 🏋️', 'Events & Wellness ✨']:
        client.messages.create(from_=to_number, to=from_number, body="This feature is coming soon! Reply 'Hi' to go back to the main menu.")

    # Fallback message
    else:
        # We only send a fallback if it's not the initial 'hi' message
        if 'hi' not in incoming_msg.lower():
            client.messages.create(from_=to_number, to=from_number, body="Sorry, I didn't get that. Say 'Hi' to see the main menu.")

    # Return an empty response to Twilio to acknowledge receipt of the message
    resp = MessagingResponse()
    return str(resp)

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=port)

