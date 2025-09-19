# This is the final, polished AI server code for your WhatsApp chatbot.
# This version includes a special 'debug' command to definitively test
# the Twilio messaging connection and diagnose silent failures.

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
gemini_api_key = os.environ.get('GEMINI_API_KEY')
twilio_whatsapp_number = os.environ.get('TWILIO_WHATSAPP_NUMBER')
main_menu_sid = os.environ.get('TWILIO_MAIN_MENU_SID')
category_list_sid = os.environ.get('TWILIO_CATEGORY_LIST_SID')

# Initialize clients
client = Client(account_sid, auth_token)
genai.configure(api_key=gemini_api_key)
model = genai.GenerativeModel('gemini-1.5-flash')

app = Flask(__name__)

# --- State Management & Database (Unchanged) ---
user_sessions = {}
PLACES = {
    'adventure': {
        'title': "*Adventure & Outdoors* 🌲",
        'locations': [
            {'name': 'Jubilee Park', 'desc': 'Central park with gardens, a zoo, and a laser show.', 'url': 'https://maps.google.com/?q=Jubilee+Park,Jamshedpur', 'budget': 'low', 'vibe': 'family', 'group': ['solo', 'friends', 'date'], 'opens': 6, 'closes': 21},
            {'name': 'Dalma Wildlife Sanctuary', 'desc': 'Known for elephants and scenic trekking routes.', 'url': 'https://maps.google.com/?q=Dalma+Wildlife+Sanctuary,Jamshedpur', 'budget': 'mid', 'vibe': 'adventure', 'group': ['friends', 'solo'], 'opens': 8, 'closes': 17}
        ]
    },
    'dining': {
        'title': "*Dining & Food* 🍔",
        'locations': [
            {'name': 'The Blue Diamond Restaurant', 'desc': 'Popular for its North Indian and Chinese cuisine.', 'url': 'https://maps.google.com/?q=The+Blue+Diamond+Restaurant,Jamshedpur', 'budget': 'high', 'vibe': 'family', 'group': ['date', 'friends'], 'opens': 12, 'closes': 23},
            {'name': 'Brubeck Bakery', 'desc': 'An upscale bakery & cafe with a quiet, chill ambiance, perfect for a date.', 'url': 'https://maps.google.com/?q=Brubeck+Bakery,Jamshedpur', 'budget': 'high', 'vibe': 'chill', 'group': ['date', 'solo'], 'opens': 9, 'closes': 21}
        ]
    },
    'cultural': {
        'title': "*Cultural & Shopping* 🛍️",
        'locations': [
            {'name': 'P&M Hi-Tech City Centre Mall', 'desc': 'The main mall for brands, food, and movies.', 'url': 'https://maps.google.com/?q=P%26M+Hi-Tech+City+Centre+Mall,Jamshedpur', 'budget': 'mid', 'vibe': 'social', 'group': ['friends', 'family'], 'opens': 11, 'closes': 22}
        ]
    }
}

# --- AI Core Functions (Unchanged) ---
def get_intent_from_ai(user_query):
    system_prompt = "..."
    try:
        # (code unchanged)
        response = model.generate_content(f"{system_prompt}\nUser: \"{user_query}\"\nResponse:")
        cleaned_response = response.text.strip().replace('```json', '').replace('```', '')
        return json.loads(cleaned_response)
    except Exception as e:
        print(f"AI NLU Error: {e}")
        return {"intent": "greet", "preferences": {}}

def generate_itinerary_from_ai(preferences):
    system_prompt = "..."
    try:
        # (code unchanged)
        response = model.generate_content(system_prompt)
        return response.text
    except Exception as e:
        print(f"AI Itinerary Generation Error: {e}")
        return "I had trouble creating a plan right now."


# --- Main Application Logic ---

@app.route('/whatsapp', methods=['POST'])
def whatsapp_reply():
    incoming_msg = request.values.get('Body', '').strip()
    from_number = request.values.get('From')
    
    # --- ADDED DEBUG ROUTE ---
    if incoming_msg.lower() == 'debug':
        send_debug_message(from_number)
        return str(MessagingResponse())

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
        session['state'] = 'awaiting_freeform_query'
        user_sessions[from_number] = session
        handle_ongoing_conversation(from_number, incoming_msg, session)

    return str(MessagingResponse())

def handle_interactive_reply(from_number, reply_id, session):
    # (code unchanged)
    if reply_id == 'ai_search':
        session['state'] = 'awaiting_freeform_query'
        user_sessions[from_number] = session
        send_text_reply(from_number, "Of course! What are you looking for?")
    # ... etc
    elif reply_id == 'browse_categories':
        send_category_list_message(from_number)
    elif reply_id == 'plan_itinerary':
        session['state'] = 'awaiting_itinerary_occasion'
        user_sessions[from_number] = session
        send_text_reply(from_number, "I can plan something for you! What's the occasion?")
    elif reply_id == 'surprise_me':
        send_surprise_me(from_number)
    elif reply_id in PLACES:
        send_recommendations(from_number, {'category': reply_id})

def handle_ongoing_conversation(from_number, message, session):
    # (code unchanged)
    current_state = session.get('state')
    if current_state == 'awaiting_freeform_query':
        ai_response = get_intent_from_ai(message)
        send_recommendations(from_number, ai_response.get('preferences', {}))
    elif 'awaiting_itinerary' in current_state:
        handle_itinerary_flow(from_number, message, session)

def handle_itinerary_flow(from_number, message, session):
    # (code unchanged)
    current_state = session.get('state')
    if current_state == 'awaiting_itinerary_occasion':
        session['preferences'] = {'occasion': message}
        session['state'] = 'awaiting_itinerary_vibe'
        send_text_reply(from_number, "Sounds great! What kind of vibe?")
    # ... etc
    elif current_state == 'awaiting_itinerary_vibe':
        session['preferences']['vibe'] = message
        session['state'] = 'awaiting_itinerary_budget'
        send_text_reply(from_number, "Perfect. And the budget?")
    elif current_state == 'awaiting_itinerary_budget':
        session['preferences']['budget'] = message
        send_text_reply(from_number, "Awesome! Creating a plan for you now...")
        itinerary = generate_itinerary_from_ai(session['preferences'])
        send_text_reply(from_number, itinerary)
        user_sessions.pop(from_number, None)
    if from_number in user_sessions:
        user_sessions[from_number] = session

def filter_places(preferences):
    # (code unchanged)
    filtered = []
    all_places = [loc for cat_data in PLACES.values() for loc in cat_data['locations']]
    for loc in all_places:
        match = True
        # ... etc
        if preferences.get('budget') and loc['budget'] != preferences['budget']: match = False
        if preferences.get('vibe') and loc['vibe'] != preferences['vibe']: match = False
        if preferences.get('group') and preferences.get('group') not in loc['group']: match = False
        if preferences.get('category'):
            loc_cat_key = next((key for key, val in PLACES.items() if loc in val['locations']), None)
            if loc_cat_key != preferences['category']: match = False
        if match: filtered.append(loc)
    return filtered

def send_recommendations(from_number, preferences):
    # (code unchanged)
    if not preferences or not any(preferences.values()):
        # ... etc
        session = user_sessions.get(from_number, {})
        session['state'] = 'awaiting_itinerary_occasion'
        user_sessions[from_number] = session
        send_text_reply(from_number, "I can help with that, but it sounds like you're looking for a plan. What's the occasion?")
        return
    # ... etc
    recommendations = filter_places(preferences)
    if not recommendations:
        send_text_reply(from_number, "I couldn't find any spots that match your criteria.")
        user_sessions.pop(from_number, None)
        return
    reply_text = "Here are a few recommendations:\n\n"
    for loc in recommendations[:3]:
        reply_text += f"*{loc['name']}*\n{loc['desc']}\nDirections: {loc['url']}\n\n"
    reply_text += "Say 'Hi' to return to the main menu."
    send_text_reply(from_number, reply_text.strip())
    user_sessions.pop(from_number, None)

def send_surprise_me(from_number):
    # (code unchanged)
    all_locations = [loc for cat_data in PLACES.values() for loc in cat_data['locations']]
    if not all_locations:
        send_text_reply(from_number, "I couldn't find a surprise right now.")
        return
    random_place = random.choice(all_locations)
    reply_text = (f"🎲 Surprise!\n\n*{random_place['name']}*\n{random_place['desc']}\nDirections: {random_place['url']}\n\nSay 'Hi' to return.")
    send_text_reply(from_number, reply_text)
    user_sessions.pop(from_number, None)

# --- Twilio Messaging Helpers ---

def send_text_reply(from_number, text):
    try:
        client.messages.create(from_=f'whatsapp:{twilio_whatsapp_number}', to=from_number, body=text)
    except TwilioRestException as e:
        print(f"ERROR sending text reply: {e}")

def send_main_menu(from_number):
    # (code unchanged)
    if not main_menu_sid:
        send_text_reply(from_number, "The main menu is not configured.")
        return
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
    # (code unchanged)
    if not category_list_sid:
        send_text_reply(from_number, "The category menu is not configured.")
        return
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

# --- ADDED DEBUG FUNCTION ---
def send_debug_message(from_number):
    """A simple function to test the core Twilio messaging functionality."""
    try:
        message = client.messages.create(
            from_=f'whatsapp:{twilio_whatsapp_number}',
            to=from_number,
            body="This is a direct test message. If you see this, the connection is working."
        )
        print(f"DEBUG: Successfully sent message. SID: {message.sid}")
    except TwilioRestException as e:
        print(f"DEBUG: FAILED to send message. Error Code: {e.code}, Message: {e.msg}")


# --- Flask App Runner (Unchanged) ---
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=port)

