# This is the corrected server code for your WhatsApp chatbot.
# It uses the correct 'persistent_action' parameter for interactive Quick Reply buttons
# and implements a multi-step menu to display all 7 categories.

import os
from flask import Flask, request
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse

# --- Twilio Configuration ---
# Your credentials are read from the environment variables you set in Render.
account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
client = Client(account_sid, auth_token)

app = Flask(__name__)

@app.route('/whatsapp', methods=['POST'])
def whatsapp_reply():
    """
    Handles incoming WhatsApp messages, routing them to the correct reply function.
    """
    incoming_msg = request.values.get('Body', '').strip()
    from_number = request.values.get('From')
    to_number = request.values.get('To')
    
    print(f"Received message: '{incoming_msg}' from {from_number}")

    body_lower = incoming_msg.lower()

    # --- Chatbot Logic Router ---

    # Main menu options
    if 'hi' in body_lower or 'hello' in body_lower or incoming_msg == 'Back to Start':
        send_main_menu(from_number, to_number)

    # Browse categories menu
    elif incoming_msg == 'Browse 7 categories':
        send_categories_menu_page_1(from_number, to_number)
    elif incoming_msg == 'More categories (1/2)':
        send_categories_menu_page_2(from_number, to_number)
    elif incoming_msg == 'More categories (2/2)':
        send_categories_menu_page_3(from_number, to_number)

    # Category selection actions
    elif 'Adventure & Outdoors' in incoming_msg:
        send_location_details(from_number, to_number, 'adventure')
    elif 'Dining & Food' in incoming_msg:
        send_location_details(from_number, to_number, 'dining')
    elif 'Getaways & Nature' in incoming_msg:
        send_location_details(from_number, to_number, 'getaways')
    elif 'Cultural & Shopping' in incoming_msg:
        send_location_details(from_number, to_number, 'cultural')
    elif 'Entertainment & Leisure' in incoming_msg:
        send_location_details(from_number, to_number, 'leisure')
    elif 'Sports & Fitness' in incoming_msg:
        send_location_details(from_number, to_number, 'sports')
    elif 'Events & Wellness' in incoming_msg:
        send_location_details(from_number, to_number, 'events')

    # Other main menu options
    elif incoming_msg in ['Surprise Me', 'Personalize']:
        send_text_reply(from_number, to_number, "This feature is coming soon! Reply 'Hi' to go back to the main menu.")
    
    # Fallback for unknown messages
    else:
        send_text_reply(from_number, to_number, "Sorry, I didn't get that. Say 'Hi' to see the main menu.")

    # Return an empty response to Twilio to acknowledge the message
    return str(MessagingResponse())


def send_main_menu(to_number, from_number):
    """Sends the initial greeting with 3 Quick Reply buttons."""
    client.messages.create(
        from_=from_number,
        to=to_number,
        body="Hi there! Welcome to Xperience, your exploration companion for Jamshedpur. 🧭\n\nChoose a path:",
        persistent_action=['Browse 7 categories', 'Surprise Me', 'Personalize']
    )

def send_categories_menu_page_1(to_number, from_number):
    """Sends the first page of category buttons."""
    client.messages.create(
        from_=from_number,
        to=to_number,
        body="Let's start exploring! Pick one or see more options:",
        persistent_action=['Adventure & Outdoors 🌲', 'Dining & Food 🍔', 'More categories (1/2)']
    )

def send_categories_menu_page_2(to_number, from_number):
    """Sends the second page of category buttons."""
    client.messages.create(
        from_=from_number,
        to=to_number,
        body="Here are more categories:",
        persistent_action=['Getaways & Nature 🏞️', 'Cultural & Shopping 🛍️', 'More categories (2/2)']
    )

def send_categories_menu_page_3(to_number, from_number):
    """Sends the final page of category buttons."""
    client.messages.create(
        from_=from_number,
        to=to_number,
        body="And the final options:",
        persistent_action=['Entertainment & Leisure 🎬', 'Sports & Fitness 🏋️', 'Events & Wellness ✨']
    )

def send_location_details(to_number, from_number, category):
    """Sends a formatted string with location details based on the category."""
    replies = {
        'adventure': (
            "*Adventure & Outdoors* 🌲:\n\n"
            "*Jubilee Park*\nA central park with gardens, a zoo, and a laser show.\n"
            "Directions: https://maps.google.com/?q=Jubilee+Park,Jamshedpur\n\n"
            "*Dalma Wildlife Sanctuary*\nKnown for its elephants and scenic trekking routes.\n"
            "Directions: https://maps.google.com/?q=Dalma+Wildlife+Sanctuary,Jamshedpur"
        ),
        'dining': (
            "*Dining & Food* 🍔:\n\n"
            "*The Blue Diamond Restaurant*\nPopular for its North Indian and Chinese cuisine.\n"
            "Directions: https://maps.google.com/?q=The+Blue+Diamond+Restaurant,Jamshedpur\n\n"
            "*Dastarkhan*\nA well-regarded spot for authentic Mughlai dishes.\n"
            "Directions: https://maps.google.com/?q=Dastarkhan,Jamshedpur"
        ),
        'getaways': (
            "*Getaways & Nature* 🏞️:\n\n"
            "*Dimna Lake*\nA beautiful artificial lake at the foothills of the Dalma hills, perfect for picnics and boating.\n"
            "Directions: https://maps.google.com/?q=Dimna+Lake,Jamshedpur\n\n"
            "*Hudco Lake*\nLocated in the Telco Colony, it offers a serene environment and boating facilities.\n"
            "Directions: https://maps.google.com/?q=Hudco+Lake,Jamshedpur"
        ),
        # You can add the other categories here
        'cultural': "Coming soon: Cultural & Shopping locations!",
        'leisure': "Coming soon: Entertainment & Leisure locations!",
        'sports': "Coming soon: Sports & Fitness locations!",
        'events': "Coming soon: Events & Wellness locations!",
    }
    reply_text = replies.get(category, "Sorry, something went wrong.")
    send_text_reply(to_number, from_number, reply_text)

def send_text_reply(to_number, from_number, text):
    """A simple helper function to send a standard text message."""
    client.messages.create(from_=from_number, to=to_number, body=text)


if __name__ == "__main__":
    port = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=port)

