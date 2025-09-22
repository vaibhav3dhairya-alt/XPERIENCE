# This is the simplified, non-AI server code for your WhatsApp chatbot.
# This version features four distinct modes: Browse, Personalize, Surprise Me,
# and a rule-based Itinerary Builder.

import os
import random
import json
from flask import Flask, request
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from twilio.base.exceptions import TwilioRestException

# --- Configuration ---
account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
twilio_whatsapp_number = os.environ.get('TWILIO_WHATSAPP_NUMBER')
main_menu_sid = os.environ.get('TWILIO_MAIN_MENU_SID') # Corrected typo from TWilio
category_list_sid = os.environ.get('TWILIO_CATEGORY_LIST_SID')

# Initialize client
client = Client(account_sid, auth_token)
app = Flask(__name__)

# --- State Management ---
user_sessions = {}

# --- Comprehensive Jamshedpur Locations Database ---
PLACES = {
    'adventure': {
        'title': "*Adventure & Outdoors* 🌲",
        'locations': [
            {'name': 'Jubilee Park', 'desc': 'Central park with gardens, a zoo, and a laser show.', 'url': 'https://maps.google.com/?q=Jubilee+Park,Jamshedpur', 'budget': 'low', 'vibe': 'family', 'group': ['solo', 'friends', 'date'], 'type': 'activity'},
            {'name': 'Dalma Wildlife Sanctuary', 'desc': 'Known for elephants and scenic trekking routes.', 'url': 'https://maps.google.com/?q=Dalma+Wildlife+Sanctuary,Jamshedpur', 'budget': 'mid', 'vibe': 'adventure', 'group': ['friends', 'solo'], 'type': 'activity'}
        ]
    },
    'dining': {
        'title': "*Dining & Food* 🍔",
        'locations': [
            {'name': 'The Blue Diamond Restaurant', 'desc': 'Popular for its North Indian and Chinese cuisine.', 'url': 'https://maps.google.com/?q=The+Blue+Diamond+Restaurant,Jamshedpur', 'budget': 'high', 'vibe': 'family', 'group': ['date', 'friends'], 'type': 'dining'},
            {'name': 'Brubeck Bakery', 'desc': 'An upscale bakery & cafe with a quiet, chill ambiance.', 'url': 'https://maps.google.com/?q=Brubeck+Bakery,Jamshedpur', 'budget': 'high', 'vibe': 'chill', 'group': ['date', 'solo'], 'type': 'dining'},
            {'name': 'Dastarkhan', 'desc': 'A well-regarded spot for authentic Mughlai dishes.', 'url': 'https://maps.google.com/?q=Dastarkhan,Jamshedpur', 'budget': 'mid', 'vibe': 'social', 'group': ['friends', 'family'], 'type': 'dining'}
        ]
    },
    'getaways': {
        'title': "*Getaways & Nature* 🏞️",
        'locations': [
            {'name': 'Dimna Lake', 'desc': 'Beautiful artificial lake, perfect for picnics and boating.', 'url': 'https://maps.google.com/?q=Dimna+Lake,Jamshedpur', 'budget': 'low', 'vibe': 'chill', 'group': ['friends', 'family', 'date'], 'type': 'activity'},
            {'name': 'Hudco Lake', 'desc': 'Serene environment in the Telco Colony with boating facilities.', 'url': 'https://maps.google.com/?q=Hudco+Lake,Jamshedpur', 'budget': 'low', 'vibe': 'chill', 'group': ['solo', 'date'], 'type': 'activity'}
        ]
    },
    'cultural': {
        'title': "*Cultural & Shopping* 🛍️",
        'locations': [
            {'name': 'P&M Hi-Tech City Centre Mall', 'desc': 'The main mall for brands, food, and movies.', 'url': 'https://maps.google.com/?q=P%26M+Hi-Tech+City+Centre+Mall,Jamshedpur', 'budget': 'mid', 'vibe': 'social', 'group': ['friends', 'family'], 'type': 'activity'},
            {'name': 'Russy Modi Centre for Excellence', 'desc': 'An archive of Tata Steel\'s history with unique architecture.', 'url': 'https://maps.google.com/?q=Russy+Modi+Centre+for+Excellence,Jamshedpur', 'budget': 'low', 'vibe': 'cultural', 'group': ['solo', 'date'], 'type': 'activity'}
        ]
    },
    'leisure': {
        'title': "*Entertainment & Fun* 🎬",
        'locations': [
            {'name': 'PJP Cinema Hall', 'desc': 'A popular multiplex for watching the latest movies.', 'url': 'https://maps.google.com/?q=PJP+Cinema+Hall,Jamshedpur', 'budget': 'mid', 'vibe': 'social', 'group': ['friends', 'date'], 'type': 'activity'}
        ]
    },
    'sports': {
        'title': "*Sports & Fitness* 🏋️",
        'locations': [
            {'name': 'JRD Tata Sports Complex', 'desc': 'A large complex for various sports including football and swimming.', 'url': 'https://maps.google.com/?q=JRD+Tata+Sports+Complex,Jamshedpur', 'budget': 'low', 'vibe': 'adventure', 'group': ['solo', 'friends'], 'type': 'activity'}
        ]
    },
    'events': {
        'title': "*Events & Wellness* ✨",
        'locations': [
            {'name': 'Beldih Club', 'desc': 'Often hosts food festivals, concerts, and other lifestyle events.', 'url': 'https://maps.google.com/?q=Beldih+Club,Jamshedpur', 'budget': 'high', 'vibe': 'social', 'group': ['friends', 'family'], 'type': 'activity'}
        ]
    }
}

# --- Main Application Logic ---

@app.route('/whatsapp', methods=['POST'])
def whatsapp_reply():
    incoming_msg = request.values.get('Body', '').strip()
    from_number = request.values.get('From')
    
    session = user_sessions.get(from_number, {'state': 'start'})
    
    interactive_reply_id = request.values.get('ButtonPayload')
    if interactive_reply_id:
        handle_interactive_reply(from_number, interactive_reply_id, session)
        return str(MessagingResponse())
    
    if session['state'] != 'start':
        handle_ongoing_conversation(from_number, incoming_msg, session)
        return str(MessagingResponse())

    if incoming_msg.lower() in ['hi', 'hello', 'menu']:
        send_main_menu(from_number)
    else:
        send_text_reply(from_number, "Sorry, I didn't understand that. Please say 'Hi' to see the main menu.")

    return str(MessagingResponse())

def handle_interactive_reply(from_number, reply_id, session):
    """Handles selections from the main menu or category list."""
    if reply_id == 'browse_categories':
        send_category_list_message(from_number)
    elif reply_id == 'plan_itinerary':
        session['state'] = 'awaiting_itinerary_occasion'
        user_sessions[from_number] = session
        send_text_reply(from_number, "I can plan something for you! What's the occasion? (e.g., an evening out, a day trip)")
    elif reply_id == 'personalize':
        session['state'] = 'awaiting_budget'
        user_sessions[from_number] = session
        send_text_reply(from_number, "Great! Let's find a single perfect spot. What's your budget? (e.g., low, mid, or high)")
    elif reply_id == 'surprise_me':
        send_surprise_me(from_number)
    elif reply_id in PLACES:
        # Handles a selection from the category list
        send_recommendations(from_number, {'category': reply_id})

def handle_ongoing_conversation(from_number, message, session):
    """Routes ongoing conversations to the correct flow handler."""
    if 'itinerary' in session.get('state', ''):
        handle_itinerary_flow(from_number, message, session)
    else:
        handle_personalization_flow(from_number, message, session)

def handle_itinerary_flow(from_number, message, session):
    """Manages the multi-turn conversation for building an itinerary."""
    current_state = session.get('state')
    message_lower = message.lower()
    
    if current_state == 'awaiting_itinerary_occasion':
        session['preferences'] = {'occasion': message_lower}
        session['state'] = 'awaiting_itinerary_budget'
        user_sessions[from_number] = session
        send_text_reply(from_number, "Sounds like fun! What's the budget for this plan? (e.g., low, mid, or high)")

    elif current_state == 'awaiting_itinerary_budget':
        budget = None
        if any(keyword in message_lower for keyword in ['low', 'cheap']): budget = 'low'
        elif 'mid' in message_lower: budget = 'mid'
        elif any(keyword in message_lower for keyword in ['high', 'fancy']): budget = 'high'
        
        if budget:
            session['preferences']['budget'] = budget
            itinerary = generate_simple_itinerary(session['preferences'])
            send_text_reply(from_number, itinerary)
            user_sessions.pop(from_number, None) # End session
        else:
            send_text_reply(from_number, "I didn't catch that. Is the budget low, mid, or high?")


def handle_personalization_flow(from_number, message, session):
    """Manages the multi-turn conversation for finding a single place."""
    current_state = session.get('state')
    message_lower = message.lower()

    if current_state == 'awaiting_budget':
        budget = None
        if any(keyword in message_lower for keyword in ['low', 'cheap']): budget = 'low'
        elif 'mid' in message_lower: budget = 'mid'
        elif any(keyword in message_lower for keyword in ['high', 'fancy']): budget = 'high'
        
        if budget:
            session['preferences'] = {'budget': budget}
            session['state'] = 'awaiting_vibe'
            user_sessions[from_number] = session
            send_text_reply(from_number, "Got it. What kind of vibe are you looking for? (e.g., chill, adventure, social, family)")
        else:
            send_text_reply(from_number, "I didn't catch that. Is the budget low, mid, or high?")

    elif current_state == 'awaiting_vibe':
        vibe_map = {'chill': 'chill', 'adventure': 'adventure', 'social': 'social', 'family': 'family'}
        found_vibe = next((vibe for keyword, vibe in vibe_map.items() if keyword in message_lower), None)
        
        if found_vibe:
            session['preferences']['vibe'] = found_vibe
            session['state'] = 'awaiting_group'
            user_sessions[from_number] = session
            send_text_reply(from_number, "Perfect. And who are you going with? (e.g., solo, friends, or a date)")
        else:
            send_text_reply(from_number, "I didn't understand the vibe. Is it chill, adventure, social, or family?")

    elif current_state == 'awaiting_group':
        group_map = {'solo': 'solo', 'friends': 'friends', 'date': 'date'}
        found_group = next((group for keyword, group in group_map.items() if keyword in message_lower), None)
        
        if found_group:
            session['preferences']['group'] = found_group
            send_recommendations(from_number, session['preferences'])
        else:
            send_text_reply(from_number, "I didn't get that. Are you going solo, with friends, or on a date?")


def filter_places(preferences):
    """Filters the PLACES database based on user preferences."""
    filtered = []
    all_places = [loc for cat_data in PLACES.values() for loc in cat_data['locations']]
    
    for loc in all_places:
        match = True
        if preferences.get('budget') and loc['budget'] != preferences['budget']: match = False
        if preferences.get('vibe') and loc['vibe'] != preferences['vibe']: match = False
        if preferences.get('group') and preferences.get('group') not in loc['group']: match = False
        if preferences.get('category'):
            loc_cat_key = next((key for key, val in PLACES.items() if loc in val['locations']), None)
            if loc_cat_key != preferences['category']: match = False
        if match: filtered.append(loc)
            
    return filtered

def send_recommendations(from_number, preferences):
    """Formats and sends a list of recommendations for a single place search."""
    recommendations = filter_places(preferences)
    
    if not recommendations:
        send_text_reply(from_number, "I couldn't find any spots that match all your criteria. Say 'Hi' to start over with a broader search!")
    else:
        reply_text = "Here are a few recommendations for you:\n\n"
        for loc in recommendations[:3]:
            reply_text += f"*{loc['name']}*\n{loc['desc']}\nDirections: {loc['url']}\n\n"
        reply_text += "Say 'Hi' to return to the main menu."
        send_text_reply(from_number, reply_text.strip())
    
    user_sessions.pop(from_number, None)


def send_surprise_me(from_number):
    """Selects a random place and sends its details."""
    all_locations = [loc for cat_data in PLACES.values() for loc in cat_data['locations']]
    random_place = random.choice(all_locations)
    reply_text = (
        f"🎲 Surprise! Here's a random suggestion:\n\n"
        f"*{random_place['name']}*\n{random_place['desc']}\n"
        f"Directions: {random_place['url']}\n\n"
        "Say 'Hi' to return to the main menu."
    )
    send_text_reply(from_number, reply_text)
    user_sessions.pop(from_number, None)


def generate_simple_itinerary(preferences):
    """Creates a rule-based 2-stop itinerary."""
    budget = preferences.get('budget')
    
    possible_activities = [loc for cat in PLACES.values() for loc in cat['locations'] if loc['type'] == 'activity' and loc['budget'] == budget]
    possible_dining = [loc for cat in PLACES.values() for loc in cat['locations'] if loc['type'] == 'dining' and loc['budget'] == budget]

    if not possible_activities or not possible_dining:
        return "I couldn't create a full plan with that budget, but you could try the 'Personalize' option to find a single spot! Say 'Hi' to start over."
    
    activity = random.choice(possible_activities)
    dining = random.choice(possible_dining)

    itinerary = (
        f"🗺️ *Here's a plan for your {preferences.get('occasion', 'outing')}!*\n\n"
        f"1️⃣ *First, an activity:*\n"
        f"*{activity['name']}*\n{activity['desc']}\nDirections: {activity['url']}\n\n"
        f"2️⃣ *Afterwards, grab a bite at:*\n"
        f"*{dining['name']}*\n{dining['desc']}\nDirections: {dining['url']}\n\n"
        "Enjoy your time in Jamshedpur! Say 'Hi' to start a new search."
    )
    return itinerary


# --- Twilio Messaging Helpers ---
def send_text_reply(from_number, text):
    try:
        client.messages.create(from_=f'whatsapp:{twilio_whatsapp_number}', to=from_number, body=text)
    except TwilioRestException as e:
        print(f"Error sending Twilio message: {e}")

def send_main_menu(from_number):
    try:
        client.messages.create(
            from_=f'whatsapp:{twilio_whatsapp_number}', 
            to=from_number, 
            content_sid=main_menu_sid,
            content_variables=json.dumps({
                'body_text': "Hi! I'm Xperience, your guide to Jamshedpur. Please choose an option to start:", 
                'button_text': "Main Menu"
            })
        )
    except TwilioRestException as e:
        print(f"ERROR: Could not send main menu. Details: {e}")
        send_text_reply(from_number, "Sorry, my main menu is having a problem right now.")

def send_category_list_message(from_number):
    try:
        client.messages.create(
            from_=f'whatsapp:{twilio_whatsapp_number}', 
            to=from_number, 
            content_sid=category_list_sid,
            content_variables=json.dumps({
                'body_text': "Please select a category to explore.", 
                'button_text': "Categories"
            })
        )
    except TwilioRestException as e:
        print(f"ERROR: Could not send category list. Details: {e}")
        send_text_reply(from_number, "Sorry, my category list is having a problem right now.")

# --- Flask App Runner ---
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=port)

