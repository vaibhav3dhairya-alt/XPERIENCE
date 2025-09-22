# This is the final, polished AI server code for your WhatsApp chatbot.
# This version implements an asynchronous architecture with background threading
# to handle slow AI API calls and prevent Twilio webhook timeouts.

import os
import random
import json
import threading
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
    'adventure': { 'title': "*Adventure & Outdoors* 🌲", 'locations': [ {'name': 'Jubilee Park', 'desc': 'Central park with gardens, a zoo, and a laser show.', 'url': 'https://maps.google.com/?q=Jubilee+Park,Jamshedpur', 'budget': 'low', 'vibe': 'family', 'group': ['solo', 'friends', 'date'], 'opens': 6, 'closes': 21}, {'name': 'Dalma Wildlife Sanctuary', 'desc': 'Known for elephants and scenic trekking routes.', 'url': 'https://maps.google.com/?q=Dalma+Wildlife+Sanctuary,Jamshedpur', 'budget': 'mid', 'vibe': 'adventure', 'group': ['friends', 'solo'], 'opens': 8, 'closes': 17} ] },
    'dining': { 'title': "*Dining & Food* 🍔", 'locations': [ {'name': 'The Blue Diamond Restaurant', 'desc': 'Popular for its North Indian and Chinese cuisine.', 'url': 'https://maps.google.com/?q=The+Blue+Diamond+Restaurant,Jamshedpur', 'budget': 'high', 'vibe': 'family', 'group': ['date', 'friends'], 'opens': 12, 'closes': 23}, {'name': 'Brubeck Bakery', 'desc': 'An upscale bakery & cafe with a quiet, chill ambiance.', 'url': 'https://maps.google.com/?q=Brubeck+Bakery,Jamshedpur', 'budget': 'high', 'vibe': 'chill', 'group': ['date', 'solo'], 'opens': 9, 'closes': 21} ] },
    'cultural': { 'title': "*Cultural & Shopping* 🛍️", 'locations': [ {'name': 'P&M Hi-Tech City Centre Mall', 'desc': 'The main mall for brands, food, and movies.', 'url': 'https://maps.google.com/?q=P%26M+Hi-Tech+City+Centre+Mall,Jamshedpur', 'budget': 'mid', 'vibe': 'social', 'group': ['friends', 'family'], 'opens': 11, 'closes': 22} ] }
}

# --- AI Core Functions (Unchanged) ---
def get_intent_from_ai(user_query):
    system_prompt = "..." # (Full prompt omitted for brevity)
    try:
        response = model.generate_content(f"{system_prompt}\nUser: \"{user_query}\"\nResponse:")
        cleaned_response = response.text.strip().replace('```json', '').replace('```', '')
        return json.loads(cleaned_response)
    except Exception as e:
        print(f"AI NLU Error: {e}")
        return {"intent": "greet", "preferences": {}}

def generate_itinerary_from_ai(preferences):
    system_prompt = f"..." # (Full prompt omitted for brevity)
    try:
        response = model.generate_content(system_prompt)
        return response.text
    except Exception as e:
        print(f"AI Itinerary Generation Error: {e}")
        return "I had trouble creating a plan right now, but how about Jubilee Park?"

# --- Main Application Logic ---

@app.route('/whatsapp', methods=['POST'])
def whatsapp_reply():
    """
    Handles incoming messages. For slow AI tasks, it responds immediately
    and starts a background thread to do the real work.
    """
    incoming_msg = request.values.get('Body', '').strip()
    from_number = request.values.get('From')
    
    session = user_sessions.get(from_number, {'state': 'start'})
    
    interactive_reply_id = request.values.get('ButtonPayload')
    if interactive_reply_id:
        handle_interactive_reply(from_number, interactive_reply_id, session)
        return str(MessagingResponse()) # Respond immediately
    
    if session['state'] != 'start':
        # Start background thread for ongoing conversations (personalization/itinerary)
        thread = threading.Thread(target=process_ongoing_conversation_async, args=(from_number, incoming_msg, session))
        thread.start()
        # Immediately acknowledge to prevent timeout
        return str(MessagingResponse())

    if incoming_msg.lower() in ['hi', 'hello', 'menu']:
        send_main_menu(from_number)
    else:
        # Start background thread for a new freeform AI query
        send_text_reply(from_number, "Thinking... 🧠")
        thread = threading.Thread(target=process_ai_request_async, args=(from_number, incoming_msg))
        thread.start()

    return str(MessagingResponse()) # Respond immediately

# --- Asynchronous Processing Functions ---

def process_ai_request_async(from_number, message):
    """Runs in a background thread to handle a freeform AI query."""
    print(f"BACKGROUND: Processing freeform query: '{message}'")
    ai_response = get_intent_from_ai(message)
    send_recommendations(from_number, ai_response.get('preferences', {}))

def process_ongoing_conversation_async(from_number, message, session):
    """Runs in a background thread to handle multi-turn conversations."""
    current_state = session.get('state')
    print(f"BACKGROUND: Processing ongoing conversation. State: {current_state}")

    if 'awaiting_itinerary' in current_state:
        handle_itinerary_flow(from_number, message, session)
    # Add other state handlers here if needed in the future

# --- Synchronous Handlers (Called from main thread or background thread) ---

def handle_interactive_reply(from_number, reply_id, session):
    if reply_id == 'ai_search':
        session['state'] = 'awaiting_freeform_query'
        user_sessions[from_number] = session
        send_text_reply(from_number, "Of course! What are you looking for? (e.g., 'a cheap cafe' or 'something fun for a date')")
    elif reply_id == 'browse_categories':
        send_category_list_message(from_number)
    elif reply_id == 'plan_itinerary':
        session['state'] = 'awaiting_itinerary_occasion'
        user_sessions[from_number] = session
        send_text_reply(from_number, "I can definitely plan something for you! What's the occasion? (e.g., a chill evening, a full day trip, etc.)")
    elif reply_id == 'surprise_me':
        send_surprise_me(from_number) # This is fast, so no need for async
    elif reply_id in PLACES:
        send_recommendations(from_number, {'category': reply_id})

def handle_itinerary_flow(from_number, message, session):
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
        session['preferences']['budget'] = message
        user_sessions[from_number] = session
        send_text_reply(from_number, "Awesome! I'm creating a custom plan for you now, please give me a moment...")
        itinerary = generate_itinerary_from_ai(session['preferences'])
        send_text_reply(from_number, itinerary)
        user_sessions.pop(from_number, None)

# --- Filtering and Response Functions (Unchanged) ---
def filter_places(preferences):
    # ... (code is unchanged)
    return [] 

def send_recommendations(from_number, preferences):
    # ... (code is unchanged)
    user_sessions.pop(from_number, None)

def send_surprise_me(from_number):
    # ... (code is unchanged)
    user_sessions.pop(from_number, None)

# --- Twilio Messaging Helpers (Unchanged) ---
def send_text_reply(from_number, text):
    # ... (code is unchanged)
    pass

def send_main_menu(from_number):
    # ... (code is unchanged)
    pass

def send_category_list_message(from_number):
    # ... (code is unchanged)
    pass

# --- Flask App Runner (Unchanged) ---
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=port)

