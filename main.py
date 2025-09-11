# This is the corrected server code for your WhatsApp chatbot.
# This version is designed for a BUTTON-ONLY experience.
# It uses the correct 'persistent_action' parameter for interactive Quick Reply buttons
# and relies on exact matches from the button text for navigation.

import os
import random
from flask import Flask, request
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse

# --- Twilio Configuration ---
# Your credentials are read from the environment variables you set in Render.
account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
client = Client(account_sid, auth_token)

app = Flask(__name__)

# --- Jamshedpur Locations Database ---
# A structured dictionary to hold all the curated places.
PLACES = {
    'adventure': {
        'title': "*Adventure & Outdoors* 🌲",
        'locations': [
            {'name': 'Jubilee Park', 'desc': 'A central park with gardens, a zoo, and a laser show.', 'url': 'https://maps.google.com/?q=Jubilee+Park,Jamshedpur'},
            {'name': 'Dalma Wildlife Sanctuary', 'desc': 'Known for its elephants and scenic trekking routes.', 'url': 'https://maps.google.com/?q=Dalma+Wildlife+Sanctuary,Jamshedpur'}
        ]
    },
    'dining': {
        'title': "*Dining & Food* 🍔",
        'locations': [
            {'name': 'The Blue Diamond Restaurant', 'desc': 'Popular for its North Indian and Chinese cuisine.', 'url': 'https://maps.google.com/?q=The+Blue+Diamond+Restaurant,Jamshedpur'},
            {'name': 'Dastarkhan', 'desc': 'A well-regarded spot for authentic Mughlai dishes.', 'url': 'https://maps.google.com/?q=Dastarkhan,Jamshedpur'}
        ]
    },
    'getaways': {
        'title': "*Getaways & Nature* 🏞️",
        'locations': [
            {'name': 'Dimna Lake', 'desc': 'A beautiful artificial lake at the foothills of the Dalma hills, perfect for picnics and boating.', 'url': 'https://maps.google.com/?q=Dimna+Lake,Jamshedpur'},
            {'name': 'Hudco Lake', 'desc': 'Located in the Telco Colony, it offers a serene environment and boating facilities.', 'url': 'https://maps.google.com/?q=Hudco+Lake,Jamshedpur'}
        ]
    },
    'cultural': {
        'title': "*Cultural & Shopping* 🛍️",
        'locations': [
            {'name': 'Sir Dorabji Tata Park', 'desc': 'A park dedicated to the founder, known for its annual flower show.', 'url': 'https://maps.google.com/?q=Sir+Dorabji+Tata+Park,Jamshedpur'},
            {'name': 'P&M Hi-Tech City Centre Mall', 'desc': 'The main shopping mall for brands, food, and movies.', 'url': 'https://maps.google.com/?q=P%26M+Hi-Tech+City+Centre+Mall,Jamshedpur'}
        ]
    },
    'leisure': {
        'title': "*Entertainment & Leisure* 🎬",
        'locations': [
            {'name': 'PJP Cinema Hall', 'desc': 'A popular multiplex for watching the latest movies.', 'url': 'https://maps.google.com/?q=PJP+Cinema+Hall,Jamshedpur'},
            {'name': 'Fun City', 'desc': 'An amusement park and gaming zone inside the P&M Mall.', 'url': 'https://maps.google.com/?q=Fun+City,P%26M+Mall,Jamshedpur'}
        ]
    },
    'sports': {
        'title': "*Sports & Fitness* 🏋️",
        'locations': [
            {'name': 'JRD Tata Sports Complex', 'desc': 'A large complex with facilities for various sports including football, athletics, and swimming.', 'url': 'https://maps.google.com/?q=JRD+Tata+Sports+Complex,Jamshedpur'},
            {'name': 'Keenan Stadium', 'desc': 'A famous cricket stadium that has hosted international matches.', 'url': 'https://maps.google.com/?q=Keenan+Stadium,Jamshedpur'}
        ]
    },
    'events': {
        'title': "*Events & Wellness* ✨",
        'locations': [
            {'name': 'Tata Auditorium', 'desc': 'A key venue for cultural events, shows, and concerts in the city.', 'url': 'https://maps.google.com/?q=Tata+Auditorium,XLRI,Jamshedpur'},
            {'name': 'Beldih Club', 'desc': 'Often hosts food festivals, concerts, and other lifestyle events.', 'url': 'https://maps.google.com/?q=Beldih+Club,Jamshedpur'}
        ]
    }
}


@app.route('/whatsapp', methods=['POST'])
def whatsapp_reply():
    """
    Handles incoming WhatsApp messages, routing them to the correct reply function
    based on keywords or the exact text of the button pressed.
    """
    incoming_msg = request.values.get('Body', '').strip()
    from_number = request.values.get('From')
    to_number = request.values.get('To')
    
    print(f"Received message: '{incoming_msg}' from {from_number}")

    body_lower = incoming_msg.lower()

    # --- NLU & Chatbot Logic Router ---

    # Handle greetings and main menu navigation
    if body_lower in ['hi', 'hello'] or incoming_msg == 'Back to Start':
        send_main_menu(from_number, to_number)

    # Handle main menu button presses
    elif incoming_msg == 'Browse 7 categories':
        send_categories_menu_page_1(from_number, to_number)
    elif incoming_msg == 'Surprise Me':
        send_surprise_me(from_number, to_number)
    elif incoming_msg == 'Personalize':
        send_text_reply(from_number, to_number, "This feature is coming soon! Reply 'Hi' to go back to the main menu.")

    # Handle category page 1 button presses
    elif incoming_msg == '1. Adventure & Outdoors 🌲':
         send_location_details(from_number, to_number, 'adventure')
    elif incoming_msg == '2. Dining & Food 🍔':
         send_location_details(from_number, to_number, 'dining')
    elif incoming_msg == '3. More categories (1/2)':
         send_categories_menu_page_2(from_number, to_number)

    # Handle category page 2 button presses
    elif incoming_msg == '1. Getaways & Nature 🏞️':
        send_location_details(from_number, to_number, 'getaways')
    elif incoming_msg == '2. Cultural & Shopping 🛍️':
        send_location_details(from_number, to_number, 'cultural')
    elif incoming_msg == '3. More categories (2/2)':
        send_categories_menu_page_3(from_number, to_number)

    # Handle category page 3 button presses
    elif incoming_msg == '1. Entertainment & Leisure 🎬':
        send_location_details(from_number, to_number, 'leisure')
    elif incoming_msg == '2. Sports & Fitness 🏋️':
        send_location_details(from_number, to_number, 'sports')
    elif incoming_msg == '3. Events & Wellness ✨':
        send_location_details(from_number, to_number, 'events')

    # Handle simple free-form queries (basic NLU)
    elif any(keyword in body_lower for keyword in ['food', 'eat', 'restaurant', 'cafe']):
        send_location_details(from_number, to_number, 'dining')
    elif any(keyword in body_lower for keyword in ['park', 'trek', 'outdoors']):
        send_location_details(from_number, to_number, 'adventure')
    elif any(keyword in body_lower for keyword in ['movie', 'fun', 'cinema']):
        send_location_details(from_number, to_number, 'leisure')
    elif any(keyword in body_lower for keyword in ['shop', 'market', 'mall']):
        send_location_details(from_number, to_number, 'cultural')

    # Fallback for unknown messages
    else:
        send_text_reply(from_number, to_number, "Sorry, I didn't get that. Say 'Hi' to see the main menu.")

    return str(MessagingResponse())


def send_main_menu(to_number, from_number):
    """Sends the initial greeting with 3 Quick Reply buttons."""
    body_text = (
        "Hi there! Welcome to Xperience, your exploration companion for Jamshedpur. 🧭\n\n"
        "Choose a path:"
    )
    client.messages.create(
        from_=from_number,
        to=to_number,
        body=body_text,
        persistent_action=['Browse 7 categories', 'Surprise Me', 'Personalize']
    )

def send_categories_menu_page_1(to_number, from_number):
    """Sends the first page of category buttons."""
    body_text = "Let's start exploring! Pick one or see more options:"
    client.messages.create(
        from_=from_number,
        to=to_number,
        body=body_text,
        persistent_action=['1. Adventure & Outdoors 🌲', '2. Dining & Food 🍔', '3. More categories (1/2)']
    )

def send_categories_menu_page_2(to_number, from_number):
    """Sends the second page of category buttons."""
    body_text = "Here are more categories:"
    client.messages.create(
        from_=from_number,
        to=to_number,
        body=body_text,
        persistent_action=['1. Getaways & Nature 🏞️', '2. Cultural & Shopping 🛍️', '3. More categories (2/2)']
    )

def send_categories_menu_page_3(to_number, from_number):
    """Sends the final page of category buttons."""
    body_text = "And the final options:"
    client.messages.create(
        from_=from_number,
        to=to_number,
        body=body_text,
        persistent_action=['1. Entertainment & Leisure 🎬', '2. Sports & Fitness 🏋️', '3. Events & Wellness ✨']
    )

def send_location_details(to_number, from_number, category):
    """Formats and sends location details based on the category."""
    category_info = PLACES.get(category)
    if not category_info:
        send_text_reply(to_number, from_number, "Sorry, something went wrong.")
        return

    reply_text = category_info['title'] + "\n\n"
    for loc in category_info['locations']:
        reply_text += f"*{loc['name']}*\n{loc['desc']}\nDirections: {loc['url']}\n\n"
    
    client.messages.create(
        from_=from_number,
        to=to_number,
        body=reply_text.strip(),
        persistent_action=['Back to Start'] # Add a button for easy navigation
    )

def send_surprise_me(to_number, from_number):
    """Selects a random place from all categories and sends its details."""
    all_locations = []
    for category_data in PLACES.values():
        all_locations.extend(category_data['locations'])
    
    if not all_locations:
        send_text_reply(to_number, from_number, "I couldn't find a surprise right now. Please try browsing categories!")
        return
        
    random_place = random.choice(all_locations)
    
    reply_text = (
        "🎲 Surprise! Here's a random suggestion for you:\n\n"
        f"*{random_place['name']}*\n{random_place['desc']}\n"
        f"Directions: {random_place['url']}"
    )
    
    client.messages.create(
        from_=from_number,
        to=to_number,
        body=reply_text,
        persistent_action=['Back to Start', 'Surprise Me']
    )

def send_text_reply(to_number, from_number, text):
    """A simple helper function to send a standard text message."""
    client.messages.create(from_=from_number, to=to_number, body=text)


if __name__ == "__main__":
    port = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=port)

