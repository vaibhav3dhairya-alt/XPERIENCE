# This is the fully upgraded AI server code for your WhatsApp chatbot.
# It uses the Gemini model for advanced NLU, personalization, and state management.

import os
import random
import json
import google.generativeai as genai
from flask import Flask, request
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse

# --- Configuration ---
account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
gemini_api_key = os.environ.get('GEMINI_API_KEY')
twilio_whatsapp_number = os.environ.get('TWILIO_WHATSAPP_NUMBER') # Make sure this is set in Render

# Initialize clients
client = Client(account_sid, auth_token)
genai.configure(api_key=gemini_api_key)
model = genai.GenerativeModel('gemini-1.5-flash')

app = Flask(__name__)

# --- State Management ---
# A simple dictionary to hold conversation states for each user.
user_sessions = {}

# --- Expanded Jamshedpur Locations Database with Metadata ---
PLACES = {
    'adventure': {
        'title': "*Adventure & Outdoors* 🌲",
        'locations': [
            {'name': 'Jubilee Park', 'desc': 'Central park with gardens, a zoo, and a laser show.', 'url': 'https://maps.google.com/?q=Jubilee+Park,Jamshedpur', 'budget': 'low', 'vibe': 'family', 'group': ['solo', 'friends', 'date']},
            {'name': 'Dalma Wildlife Sanctuary', 'desc': 'Known for elephants and scenic trekking routes.', 'url': 'https://maps.google.com/?q=Dalma+Wildlife+Sanctuary,Jamshedpur', 'budget': 'mid', 'vibe': 'adventure', 'group': ['friends', 'solo']},
            {'name': 'Tata Steel Adventure Foundation (TSAF)', 'desc': 'Offers rock climbing, rappelling, and other adventure sports.', 'url': 'https://maps.google.com/?q=Tata+Steel+Adventure+Foundation,Jamshedpur', 'budget': 'mid', 'vibe': 'adventure', 'group': ['friends', 'solo']}
        ]
    },
    'dining': {
        'title': "*Dining & Food* 🍔",
        'locations': [
            {'name': 'The Blue Diamond Restaurant', 'desc': 'Popular for its North Indian and Chinese cuisine.', 'url': 'https://maps.google.com/?q=The+Blue+Diamond+Restaurant,Jamshedpur', 'budget': 'high', 'vibe': 'family', 'group': ['date', 'friends']},
            {'name': 'Dastarkhan', 'desc': 'A well-regarded spot for authentic Mughlai dishes.', 'url': 'https://maps.google.com/?q=Dastarkhan,Jamshedpur', 'budget': 'mid', 'vibe': 'social', 'group': ['friends', 'family']},
            {'name': 'Cafe Regal', 'desc': 'A cozy cafe perfect for conversations and snacks.', 'url': 'https://maps.google.com/?q=Cafe+Regal,Jamshedpur', 'budget': 'low', 'vibe': 'chill', 'group': ['date', 'solo', 'friends']},
            {'name': 'Novelty Restaurant', 'desc': 'An old classic known for its consistent quality and diverse menu.', 'url': 'https://maps.google.com/?q=Novelty+Restaurant,Jamshedpur', 'budget': 'mid', 'vibe': 'family', 'group': ['family', 'friends']}
        ]
    },
     'getaways': {
        'title': "*Getaways & Nature* 🏞️",
        'locations': [
            {'name': 'Dimna Lake', 'desc': 'Beautiful artificial lake, perfect for picnics and boating.', 'url': 'https://maps.google.com/?q=Dimna+Lake,Jamshedpur', 'budget': 'low', 'vibe': 'chill', 'group': ['friends', 'family', 'date']},
            {'name': 'Hudco Lake', 'desc': 'Serene environment in the Telco Colony with boating facilities.', 'url': 'https://maps.google.com/?q=Hudco+Lake,Jamshedpur', 'budget': 'low', 'vibe': 'chill', 'group': ['solo', 'date']}
        ]
    },
    'cultural': {
        'title': "*Cultural & Shopping* 🛍️",
        'locations': [
            {'name': 'P&M Hi-Tech City Centre Mall', 'desc': 'The main mall for brands, food, and movies.', 'url': 'https://maps.google.com/?q=P%26M+Hi-Tech+City+Centre+Mall,Jamshedpur', 'budget': 'mid', 'vibe': 'social', 'group': ['friends', 'family']},
            {'name': 'Sakchi Market', 'desc': 'A bustling local market for street shopping and food.', 'url': 'https://maps.google.com/?q=Sakchi+Market,Jamshedpur', 'budget': 'low', 'vibe': 'social', 'group': ['friends', 'solo']}
        ]
    },
    'leisure': {
        'title': "*Entertainment & Fun* 🎬",
        'locations': [
            {'name': 'PJP Cinema Hall', 'desc': 'A popular multiplex for watching the latest movies.', 'url': 'https://maps.google.com/?q=PJP+Cinema+Hall,Jamshedpur', 'budget': 'mid', 'vibe': 'social', 'group': ['friends', 'date']},
            {'name': 'Fun City', 'desc': 'An amusement park and gaming zone inside the P&M Mall.', 'url': 'https://maps.google.com/?q=Fun+City,P%26M+Mall,Jamshedpur', 'budget': 'low', 'vibe': 'family', 'group': ['family', 'friends']}
        ]
    },
    'sports': {
        'title': "*Sports & Fitness* 🏋️",
        'locations': [
            {'name': 'JRD Tata Sports Complex', 'desc': 'A large complex for various sports including football and swimming.', 'url': 'https://maps.google.com/?q=JRD+Tata+Sports+Complex,Jamshedpur', 'budget': 'low', 'vibe': 'adventure', 'group': ['solo', 'friends']},
            {'name': 'Keenan Stadium', 'desc': 'A famous cricket stadium that has hosted international matches.', 'url': 'https://maps.google.com/?q=Keenan+Stadium,Jamshedpur', 'budget': 'low', 'vibe': 'social', 'group': ['friends']}
        ]
    },
    'events': {
        'title': "*Events & Wellness* ✨",
        'locations': [
            {'name': 'Tata Auditorium', 'desc': 'A key venue for cultural events, shows, and concerts in the city.', 'url': 'https://maps.google.com/?q=Tata+Auditorium,XLRI,Jamshedpur', 'budget': 'mid', 'vibe': 'social', 'group': ['friends', 'date']},
            {'name': 'Beldih Club', 'desc': 'Often hosts food festivals, concerts, and other lifestyle events.', 'url': 'https://maps.google.com/?q=Beldih+Club,Jamshedpur', 'budget': 'high', 'vibe': 'social', 'group': ['friends', 'family']}
        ]
    }
}


# --- AI Core Functions ---

def get_intent_and_preferences_from_ai(user_query):
    """
    Uses Gemini to perform advanced NLU. Extracts intent and any user preferences.
    """
    system_prompt = """
    You are a sophisticated NLU engine for a Jamshedpur city guide chatbot.
    Your task is to analyze the user's message and extract their intent and preferences.
    Respond in JSON format only.

    Intents: 'greet', 'ask_for_recommendation', 'start_personalization', 'provide_preference', 'ask_for_surprise'.

    Preferences:
    - category: ['adventure', 'dining', 'getaways', 'cultural', 'leisure', 'sports', 'events']
    - budget: ['low', 'mid', 'high']
    - vibe: ['chill', 'adventure', 'social', 'family']
    - group: ['solo', 'friends', 'date']

    Analyze the user query and extract all available information.
    If a preference is not mentioned, its value should be null.
    'cheap' or 'inexpensive' maps to 'low' budget. 'moderate' or 'not too expensive' maps to 'mid'. 'expensive' or 'fancy' maps to 'high'.

    Example 1:
    User: "Hi there"
    Response: {"intent": "greet", "preferences": {"category": null, "budget": null, "vibe": null, "group": null}}

    Example 2:
    User: "Suggest a cheap place to eat"
    Response: {"intent": "ask_for_recommendation", "preferences": {"category": "dining", "budget": "low", "vibe": null, "group": null}}
    
    Example 3:
    User: "Help me find something"
    Response: {"intent": "start_personalization", "preferences": {"category": null, "budget": null, "vibe": null, "group": null}}

    Example 4:
    User: "I'm bored"
    Response: {"intent": "ask_for_surprise", "preferences": {"category": null, "budget": null, "vibe": null, "group": null}}
    
    Example 5 (inside a conversation):
    User: "not too expensive"
    Response: {"intent": "provide_preference", "preferences": {"category": null, "budget": "mid", "vibe": null, "group": null}}
    """
    try:
        response = model.generate_content(f"{system_prompt}\nUser: \"{user_query}\"\nResponse:")
        cleaned_response = response.text.strip().replace('```json', '').replace('```', '')
        return json.loads(cleaned_response)
    except Exception as e:
        print(f"AI NLU Error: {e}")
        return {"intent": "greet", "preferences": {}}

# --- Main Application Logic ---

@app.route('/whatsapp', methods=['POST'])
def whatsapp_reply():
    """Handles incoming messages, manages session state, and routes to AI."""
    incoming_msg = request.values.get('Body', '').strip()
    from_number = request.values.get('From')
    
    print(f"Received message: '{incoming_msg}' from {from_number}")

    # Get or create a session for the user
    session = user_sessions.get(from_number, {'state': 'start', 'preferences': {}})

    # --- Personalization Flow State Machine ---
    if session['state'] != 'start':
        handle_personalization_flow(from_number, incoming_msg, session)
        return str(MessagingResponse())

    # --- AI-Powered Router for New Conversations ---
    ai_response = get_intent_and_preferences_from_ai(incoming_msg)
    intent = ai_response.get('intent')
    preferences = ai_response.get('preferences', {})

    print(f"AI Result: Intent='{intent}', Preferences='{preferences}'")
    
    # Handle the 'personalize' keyword specifically to start the flow
    if 'personalize' in incoming_msg.lower():
        intent = 'start_personalization'

    if intent == 'greet':
        send_text_reply(from_number, "Hi! I'm Xperience, your AI guide to Jamshedpur. You can ask me for recommendations (e.g., 'find a chill cafe') or say 'personalize' for a guided search.")
    elif intent == 'start_personalization':
        session['state'] = 'awaiting_budget'
        user_sessions[from_number] = session
        send_text_reply(from_number, "Great! Let's find the perfect spot. What's your budget? (e.g., cheap, moderate, or expensive)")
    elif intent == 'ask_for_surprise':
        send_surprise_me(from_number)
    elif intent == 'ask_for_recommendation':
        recommendations = filter_places(preferences)
        send_recommendations(from_number, recommendations)
    else:
        send_text_reply(from_number, "Sorry, I didn't quite get that. You can ask for recommendations or say 'personalize'.")

    return str(MessagingResponse())


def handle_personalization_flow(from_number, message, session):
    """Manages the multi-turn conversation for gathering preferences."""
    current_state = session.get('state')
    ai_response = get_intent_and_preferences_from_ai(message)
    new_preferences = ai_response.get('preferences', {})

    if current_state == 'awaiting_budget':
        budget = new_preferences.get('budget')
        if budget:
            session['preferences']['budget'] = budget
            session['state'] = 'awaiting_vibe'
            send_text_reply(from_number, "Got it. What kind of vibe are you looking for? (e.g., chill, adventure, social, or family)")
        else:
            send_text_reply(from_number, "I didn't catch a budget. Could you say cheap, moderate, or expensive?")
    
    elif current_state == 'awaiting_vibe':
        vibe = new_preferences.get('vibe')
        if vibe:
            session['preferences']['vibe'] = vibe
            session['state'] = 'awaiting_group'
            send_text_reply(from_number, "Perfect. And who are you going with? (e.g., solo, with friends, or on a date)")
        else:
            send_text_reply(from_number, "I didn't understand the vibe. Is it chill, adventure, social, or family?")

    elif current_state == 'awaiting_group':
        group = new_preferences.get('group')
        if group:
            session['preferences']['group'] = group
            # All preferences gathered, now filter and respond
            recommendations = filter_places(session['preferences'])
            send_recommendations(from_number, recommendations)
            # Reset session for the next query
            user_sessions.pop(from_number, None)
        else:
             send_text_reply(from_number, "I didn't get that. Are you going solo, with friends, or on a date?")

    # Save the updated session if it hasn't been reset
    if from_number in user_sessions:
        user_sessions[from_number] = session


def filter_places(preferences):
    """Filters the PLACES database based on user preferences."""
    filtered = []
    all_places = [loc for cat_data in PLACES.values() for loc in cat_data['locations']]
    
    for loc in all_places:
        match = True
        # Check each preference. If it's set in the user's request, it must match the location's data.
        if preferences.get('budget') and preferences['budget'] and loc['budget'] != preferences['budget']:
            match = False
        if preferences.get('vibe') and preferences['vibe'] and loc['vibe'] != preferences['vibe']:
            match = False
        if preferences.get('group') and preferences['group'] and preferences['group'] not in loc['group']:
            match = False
        
        # This is a simple category filter based on the 'dining' keyword etc.
        if preferences.get('category') and preferences['category']:
            # Find which main category key this location belongs to
            loc_category_key = None
            for key, val in PLACES.items():
                if loc in val['locations']:
                    loc_category_key = key
                    break
            if loc_category_key != preferences['category']:
                match = False
        
        if match:
            filtered.append(loc)
    return filtered


def send_recommendations(from_number, recommendations):
    """Formats and sends a list of recommendations."""
    if not recommendations:
        send_text_reply(from_number, "I couldn't find any spots that match your criteria. Try being a bit broader! Say 'Hi' to start over.")
        # Reset session if the search fails
        user_sessions.pop(from_number, None)
        return
    
    reply_text = "Here are a few recommendations for you:\n\n"
    # Limit to max 3 recommendations to avoid spam
    for loc in recommendations[:3]:
        reply_text += f"*{loc['name']}*\n{loc['desc']}\nDirections: {loc['url']}\n\n"
    
    reply_text += "Say 'Hi' to start a new search."
    send_text_reply(from_number, reply_text.strip())
    # Reset session after a successful recommendation
    user_sessions.pop(from_number, None)


def send_surprise_me(from_number):
    """Selects a random place and sends its details."""
    all_locations = [loc for cat_data in PLACES.values() for loc in cat_data['locations']]
    if not all_locations:
        send_text_reply(from_number, "I couldn't find a surprise right now.")
        return
    
    random_place = random.choice(all_locations)
    reply_text = (
        f"🎲 Surprise! Here's a random suggestion:\n\n"
        f"*{random_place['name']}*\n{random_place['desc']}\n"
        f"Directions: {random_place['url']}\n\n"
        "Say 'Hi' to start over."
    )
    send_text_reply(from_number, reply_text)
    # Reset session after a surprise
    user_sessions.pop(from_number, None)


def send_text_reply(from_number, text):
    """Helper function to send a simple text message via Twilio."""
    # This function now correctly constructs the 'from' and 'to' numbers for Twilio
    client.messages.create(
        from_=f'whatsapp:{twilio_whatsapp_number}', 
        to=from_number, 
        body=text
    )


if __name__ == "__main__":
    port = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=port)

