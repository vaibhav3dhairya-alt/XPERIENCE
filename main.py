# This is the fully upgraded server code for your WhatsApp chatbot.
# This version uses the Twilio Content API for ALL interactive messages
# for maximum reliability. It requires two Content SIDs to be configured.

import os
import random
import json
from flask import Flask, request
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse

# --- Twilio Configuration ---
account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
# SID for the Main Menu (Reply Buttons) template
main_menu_sid = os.environ.get('TWILIO_MAIN_MENU_SID')
# SID for the Category Menu (List Picker) template
category_list_sid = os.environ.get('TWILIO_CONTENT_SID')
client = Client(account_sid, auth_token)

app = Flask(__name__)

# --- Jamshedpur Locations Database ---
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
        'title': "*Entertainment & Fun* 🎬",
        'locations': [
            {'name': 'PJP Cinema Hall', 'desc': 'A popular multiplex for watching the latest movies.', 'url': 'https://maps.google.com/?q=PJP+Cinema+Hall,Jamshedpur'},
            {'name': 'Fun City', 'desc': 'An amusement park and gaming zone inside the P&M Mall.', 'url': 'https://maps.google.com/?q=Fun+City,P%26M+Mall,Jamshedpur'}
        ]
    },
    'sports': {
        'title': "*Sports & Fitness* 🏋️",
        'locations': [
            {'name': 'JRD Tata Sports Complex', 'desc': 'A large complex for various sports including football and swimming.', 'url': 'https://maps.google.com/?q=JRD+Tata+Sports+Complex,Jamshedpur'},
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
    Handles incoming WhatsApp messages, routing them based on interactive replies or keywords.
    """
    incoming_msg = request.values.get('Body', '').strip()
    from_number = request.values.get('From')
    to_number = request.values.get('To')
    
    print(f"Received message: '{incoming_msg}' from {from_number}")
    
    # Check for interactive replies from a List Picker or Reply Button
    interactive_reply_id = request.values.get('ButtonPayload')
    if not interactive_reply_id: # Fallback for some message types
        interactive_reply_id = incoming_msg

    # --- Router Logic ---
    if interactive_reply_id.lower() in ['hi', 'hello', 'back to start']:
        send_main_menu(from_number, to_number)
    elif interactive_reply_id == 'Browse Categories':
        send_category_list_message(from_number, to_number)
    elif interactive_reply_id == 'Surprise Me 🎲':
        send_surprise_me(from_number, to_number)
    elif interactive_reply_id in PLACES:
        send_location_details(from_number, to_number, interactive_reply_id)
    else:
        # Fallback for when the bot doesn't understand
        send_text_reply(from_number, to_number, "Sorry, I didn't get that. Say 'Hi' to see the main menu.")

    return str(MessagingResponse())

def send_main_menu(to_number, from_number):
    """Sends the initial greeting using a Reply Button Content Template."""
    if not main_menu_sid:
        send_text_reply(to_number, from_number, "The main menu is not configured. Please contact the administrator.")
        return

    client.messages.create(
        from_=from_number,
        to=to_number,
        content_sid=main_menu_sid,
        content_variables=json.dumps({
            '1': "Hi there! Welcome to Xperience, your exploration companion for Jamshedpur. 🧭\n\nHow would you like to start?"
        })
    )

def send_category_list_message(to_number, from_number):
    """Sends an interactive List Picker message using the Content API."""
    if not category_list_sid:
        send_text_reply(to_number, from_number, "The category menu is not configured. Please contact the administrator.")
        return

    client.messages.create(
        from_=from_number,
        to=to_number,
        content_sid=category_list_sid,
        content_variables=json.dumps({
            '1': 'Xperience Categories',
            '2': 'Please select a category to explore.',
            '3': 'Categories'
        })
    )

def send_location_details(to_number, from_number, category):
    """Formats and sends location details based on the selected category."""
    category_info = PLACES.get(category)
    if not category_info:
        send_text_reply(to_number, from_number, "Sorry, something went wrong.")
        return

    reply_text = category_info['title'] + "\n\n"
    for loc in category_info['locations']:
        reply_text += f"*{loc['name']}*\n{loc['desc']}\nDirections: {loc['url']}\n\n"
    
    reply_text += "Reply 'Hi' to return to the main menu."
    
    send_text_reply(to_number, from_number, reply_text.strip())

def send_surprise_me(to_number, from_number):
    """Selects a random place and sends its details."""
    all_locations = [loc for cat_data in PLACES.values() for loc in cat_data['locations']]
    
    if not all_locations:
        send_text_reply(to_number, from_number, "I couldn't find a surprise right now.")
        return
        
    random_place = random.choice(all_locations)
    
    reply_text = (
        "🎲 Surprise! Here's a random suggestion for you:\n\n"
        f"*{random_place['name']}*\n{random_place['desc']}\n"
        f"Directions: {random_place['url']}\n\n"
        "Reply 'Hi' to return to the main menu."
    )
    
    send_text_reply(to_number, from_number, reply_text)

def send_text_reply(to_number, from_number, text):
    """A simple helper function to send a standard text message."""
    client.messages.create(from_=from_number, to=to_number, body=text)

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=port)

