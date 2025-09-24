# This is the final, AI-powered server code for your WhatsApp chatbot.
# This version features a hybrid model with four distinct user modes:
# AI Search, Browse Categories, an AI Itinerary Planner, and Surprise Me.

import os
import random
import json
import google.generativeai as genai
from flask import Flask, request
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from twilio.base.exceptions import TwilioRestException

# --- Configuration ---
account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
twilio_whatsapp_number = os.environ.get('TWILIO_WHATSAPP_NUMBER')
main_menu_sid = os.environ.get('TWILIO_MAIN_MENU_SID')
category_list_sid = os.environ.get('TWILIO_CATEGORY_LIST_SID')
gemini_api_key = os.environ.get('GEMINI_API_KEY') # AI key is required again

# Initialize clients
client = Client(account_sid, auth_token)
genai.configure(api_key=gemini_api_key)
model = genai.GenerativeModel('gemini-1.5-flash')
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
            {'name': 'Dimna Lake', 'desc': 'Beautiful artificial lake, perfect for picnics and boating.', 'url': 'https://maps.google.com/?q=Dimna+Lake,Jamshedpur', 'budget': 'low', 'vibe': 'chill', 'group': ['friends', 'family', 'date'], 'type': 'activity'}
        ]
    },
    'cultural': {
        'title': "*Cultural & Shopping* 🛍️",
        'locations': [
            {'name': 'P&M Hi-Tech City Centre Mall', 'desc': 'The main mall for brands, food, and movies.', 'url': 'https://maps.google.com/?q=P%26M+Hi-Tech+City+Centre+Mall,Jamshedpur', 'budget': 'mid', 'vibe': 'social', 'group': ['friends', 'family'], 'type': 'activity'}
        ]
    },
    'leisure': { 'title': "*Entertainment & Fun* 🎬", 'locations': [ {'name': 'PJP Cinema Hall', 'desc': 'A popular multiplex for watching the latest movies.', 'url': 'https://maps.google.com/?q=PJP+Cinema+Hall,Jamshedpur', 'budget': 'mid', 'vibe': 'social', 'group': ['friends', 'date'], 'type': 'activity'} ] },
    'sports': { 'title': "*Sports & Fitness* 🏋️", 'locations': [ {'name': 'JRD Tata Sports Complex', 'desc': 'A large complex for various sports including football and swimming.', 'url': 'https://maps.google.com/?q=JRD+Tata+Sports+Complex,Jamshedpur', 'budget': 'low', 'vibe': 'adventure', 'group': ['solo', 'friends'], 'type': 'activity'} ] },
    'events': { 'title': "*Events & Wellness* ✨", 'locations': [ {'name': 'Beldih Club', 'desc': 'Often hosts food festivals, concerts, and other lifestyle events.', 'url': 'https://maps.google.com/?q=Beldih+Club,Jamshedpur', 'budget': 'high', 'vibe': 'social', 'group': ['friends', 'family'], 'type': 'activity'} ] }
}

# --- AI Core Functions ---

def get_intent_and_preferences_from_ai(user_query):
    """Uses Gemini to perform NLU, extracting intent and preferences."""
    system_prompt = """
    You are an NLU engine for a city guide chatbot. Analyze the user's message to extract their intent and any preferences.
    Respond in JSON format only.
    Intents: 'ask_for_recommendation', 'start_itinerary', 'ask_for_surprise'.
    Preferences: 'category', 'budget', 'vibe', 'group'.
    Map words like 'cheap' to 'low' budget, 'plan my evening' to 'start_itinerary'.
    If the query is too vague (e.g., "suggest something"), the intent should be 'start_itinerary'.
    """
    try:
        response = model.generate_content(f"{system_prompt}\nUser: \"{user_query}\"\nResponse:")
        cleaned_response = response.text.strip().replace('```json', '').replace('```', '')
        return json.loads(cleaned_response)
    except Exception as e:
        print(f"AI NLU Error: {e}")
        return {"intent": "greet", "preferences": {}}

def generate_itinerary_from_ai(preferences):
    """Uses Gemini to generate a creative itinerary from the PLACES data."""
    system_prompt = f"""
    You are an expert Jamshedpur tour guide. Your task is to create a logical and engaging itinerary based on the user's preferences.
    The user wants a plan for an '{preferences.get('occasion', 'evening')}' with a '{preferences.get('vibe', 'any')}' vibe and a '{preferences.get('budget', 'any')}' budget.
    
    Here is a list of available places in JSON format: {json.dumps(PLACES)}
    
    Create a short, creative itinerary with 2-3 stops.
    Structure the output as a step-by-step plan with timings.
    Make it sound like a friendly, expert recommendation. Do not output JSON.
    Start with a catchy title for the plan.
    """
    try:
        response = model.generate_content(system_prompt)
        return response.text
    except Exception as e:
        print(f"AI Itinerary Generation Error: {e}")
        return "I had trouble creating a plan right now, but how about a visit to Jubilee Park? It's lovely in the evening!"


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
        # Assume any other text is a direct AI query and start that flow
        session['state'] = 'awaiting_freeform_query'
        user_sessions[from_number] = session
        handle_ongoing_conversation(from_number, incoming_msg, session)

    return str(MessagingResponse())

def handle_interactive_reply(from_number, reply_id, session):
    """Handles selections from the main menu or category list."""
    if reply_id == 'ai_search':
        session['state'] = 'awaiting_freeform_query'
        user_sessions[from_number] = session
        send_text_reply(from_number, "Of course! What are you looking for? (e.g., 'a cheap cafe' or 'something fun for a date')")
    elif reply_id == 'browse_categories':
        send_category_list_message(from_number)
    elif reply_id == 'plan_itinerary':
        session['state'] = 'awaiting_itinerary_occasion'
        user_sessions[from_number] = session
        send_text_reply(from_number, "I can plan something for you! What's the occasion? (e.g., a chill evening, a full day trip, etc.)")
    elif reply_id == 'surprise_me':
        send_surprise_me(from_number)
    elif reply_id in PLACES:
        # Handles a selection from the category list
        send_recommendations(from_number, {'category': reply_id})

def handle_ongoing_conversation(from_number, message, session):
    """Routes ongoing conversations to the correct flow handler."""
    current_state = session.get('state')

    if current_state == 'awaiting_freeform_query':
        ai_response = get_intent_and_preferences_from_ai(message)
        send_recommendations(from_number, ai_response.get('preferences', {}))
    
    elif 'awaiting_itinerary' in current_state:
        handle_itinerary_flow(from_number, message, session)

def handle_itinerary_flow(from_number, message, session):
    """Manages the multi-turn conversation for building an itinerary with AI."""
    current_state = session.get('state')
    
    if current_state == 'awaiting_itinerary_occasion':
        session['preferences'] = {'occasion': message}
        session['state'] = 'awaiting_itinerary_vibe'
        user_sessions[from_number] = session
        send_text_reply(from_number, f"A {message} sounds great! What kind of vibe are you looking for? (e.g., adventurous, relaxing, social)")
    
    elif current_state == 'awaiting_itinerary_vibe':
        session['preferences']['vibe'] = message
        session['state'] = 'awaiting_itinerary_budget'
        user_sessions[from_number] = session
        send_text_reply(from_number, f"Perfect. And what's the budget for this plan? (e.g., low, mid, or high)")

    elif current_state == 'awaiting_itinerary_budget':
        session['preferences']['budget'] = message.lower()
        send_text_reply(from_number, "Awesome! I'm creating a custom plan for you now, please give me a moment...")
        itinerary = generate_itinerary_from_ai(session['preferences'])
        send_text_reply(from_number, itinerary)
        user_sessions.pop(from_number, None) # End session

# --- Filtering and Response Functions ---

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
    """Formats and sends a list of recommendations from a direct AI query."""
    if not preferences or not any(preferences.values()):
        # If AI returns nothing, pivot to the itinerary builder
        session = user_sessions.get(from_number, {})
        session['state'] = 'awaiting_itinerary_occasion'
        user_sessions[from_number] = session
        send_text_reply(from_number, "I can help with that, but it sounds like you're looking for a plan. What's the occasion? (e.g., a chill evening)")
        return

    recommendations = filter_places(preferences)
    
    if not recommendations:
        send_text_reply(from_number, "I couldn't find any spots that match your criteria. Say 'Hi' to try again with broader search terms!")
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
                'body_text': "Hi! I'm Xperience, your AI guide to Jamshedpur. Please choose an option to start:", 
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

