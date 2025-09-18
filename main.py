# This is the fully upgraded AI server code for your WhatsApp chatbot.
# It uses the Gemini model for advanced NLU, personalization, and state management.
# This version includes fixes for the NLU loop and adds smart fallback logic.

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
twilio_whatsapp_number = os.environ.get('TWILIO_WHATSAPP_NUMBER')

# Initialize clients
client = Client(account_sid, auth_token)
genai.configure(api_key=gemini_api_key)
model = genai.GenerativeModel('gemini-1.5-flash')

app = Flask(__name__)

# --- State Management ---
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
            {'name': 'Novelty Restaurant', 'desc': 'An old classic known for its consistent quality and diverse menu.', 'url': 'https://maps.google.com/?q=Novelty+Restaurant,Jamshedpur', 'budget': 'mid', 'vibe': 'family', 'group': ['family', 'friends']},
            {'name': 'Brubeck Bakery', 'desc': 'An upscale bakery & cafe with a quiet, chill ambiance, perfect for a date.', 'url': 'https://maps.google.com/?q=Brubeck+Bakery,Jamshedpur', 'budget': 'high', 'vibe': 'chill', 'group': ['date', 'solo']}
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
    }
}


# --- AI Core Functions ---

def get_intent_and_preferences_from_ai(user_query, context=""):
    """
    Uses Gemini to perform advanced NLU. Extracts intent and any user preferences.
    Now includes context to better understand single-word answers.
    """
    system_prompt = f"""
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
    
    The current conversation context is: {context}
    Use this context to understand single-word answers. For example, if the context is 'awaiting_vibe' and the user says 'adventure', you must extract 'adventure' as the vibe.

    Example 1:
    User: "Hi there"
    Response: {{"intent": "greet", "preferences": {{"category": null, "budget": null, "vibe": null, "group": null}}}}

    Example 2:
    User: "Suggest a cheap place to eat"
    Response: {{"intent": "ask_for_recommendation", "preferences": {{"category": "dining", "budget": "low", "vibe": null, "group": null}}}}
    
    Example 3 (with context):
    Context: awaiting_vibe
    User: "adventure"
    Response: {{"intent": "provide_preference", "preferences": {{"category": null, "budget": null, "vibe": "adventure", "group": null}}}}
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
    incoming_msg = request.values.get('Body', '').strip()
    from_number = request.values.get('From')
    
    print(f"Received message: '{incoming_msg}' from {from_number}")

    session = user_sessions.get(from_number, {'state': 'start', 'preferences': {}})

    if session['state'] != 'start':
        handle_personalization_flow(from_number, incoming_msg, session)
        return str(MessagingResponse())

    ai_response = get_intent_and_preferences_from_ai(incoming_msg)
    intent = ai_response.get('intent')
    preferences = ai_response.get('preferences', {})

    print(f"AI Result: Intent='{intent}', Preferences='{preferences}'")
    
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
        send_recommendations(from_number, preferences)
    else:
        send_text_reply(from_number, "Sorry, I didn't quite get that. You can ask for recommendations or say 'personalize'.")

    return str(MessagingResponse())


def handle_personalization_flow(from_number, message, session):
    current_state = session.get('state')
    ai_response = get_intent_and_preferences_from_ai(message, context=current_state)
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
            send_recommendations(from_number, session['preferences'])
            user_sessions.pop(from_number, None)
        else:
             send_text_reply(from_number, "I didn't get that. Are you going solo, with friends, or on a date?")

    if from_number in user_sessions:
        user_sessions[from_number] = session


def filter_places(preferences, relax_criteria=None):
    """Filters the PLACES database. Can relax one criterion if needed."""
    filtered = []
    all_places = [loc for cat_data in PLACES.values() for loc in cat_data['locations']]
    
    for loc in all_places:
        match = True
        if preferences.get('budget') and relax_criteria != 'budget' and loc['budget'] != preferences['budget']:
            match = False
        if preferences.get('vibe') and relax_criteria != 'vibe' and loc['vibe'] != preferences['vibe']:
            match = False
        if preferences.get('group') and relax_criteria != 'group' and preferences['group'] not in loc['group']:
            match = False
        if preferences.get('category'):
            loc_category_key = next((key for key, val in PLACES.items() if loc in val['locations']), None)
            if loc_category_key != preferences['category']:
                match = False
        if match:
            filtered.append(loc)
    return filtered


def send_recommendations(from_number, preferences):
    """Formats and sends recommendations, with smart fallback logic."""
    # First, try a strict search
    recommendations = filter_places(preferences)
    fallback_message = ""

    # If no results, try relaxing criteria one by one
    if not recommendations:
        for criteria in ['budget', 'vibe', 'group']:
            relaxed_recs = filter_places(preferences, relax_criteria=criteria)
            if relaxed_recs:
                recommendations = relaxed_recs
                fallback_message = f"(I couldn't find a perfect match, so I relaxed the '{criteria}' filter for you.)\n\n"
                break

    if not recommendations:
        send_text_reply(from_number, "I couldn't find any spots that match your criteria, even with some flexibility. Try being a bit broader! Say 'Hi' to start over.")
        user_sessions.pop(from_number, None)
        return
    
    reply_text = fallback_message + "Here are a few recommendations for you:\n\n"
    for loc in recommendations[:3]:
        reply_text += f"*{loc['name']}*\n{loc['desc']}\nDirections: {loc['url']}\n\n"
    
    reply_text += "Say 'Hi' to start a new search."
    send_text_reply(from_number, reply_text.strip())
    user_sessions.pop(from_number, None)


def send_surprise_me(from_number):
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
    user_sessions.pop(from_number, None)


def send_text_reply(from_number, text):
    try:
        client.messages.create(
            from_=f'whatsapp:{twilio_whatsapp_number}', 
            to=from_number, 
            body=text
        )
    except Exception as e:
        print(f"Error sending Twilio message: {e}")


if __name__ == "__main__":
    port = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=port)

