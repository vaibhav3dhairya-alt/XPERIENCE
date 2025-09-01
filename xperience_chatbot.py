import random
from urllib.parse import quote_plus

# --- Helper function to create Google Maps links ---
def create_maps_link(location_query):
    """Creates a Google Maps search URL from a location string."""
    encoded_query = quote_plus(location_query)
    return f"https://www.google.com/maps/search/?api=1&query={encoded_query}"

# --- Mock Database for Jamshedpur Locations (with location_query) ---
Jamshedpur_DATABASE = {
    'dining': [
        {'name': 'The Blue Diamond', 'vibe': 'family', 'budget': 3, 'type': 'restaurant', 'audience': ['professional', 'family'], 'description': 'A classic spot in Bistupur for North Indian cuisine.', 'location_query': 'The Blue Diamond Restaurant, Bistupur, Jamshedpur'},
        {'name': 'Novelty Restaurant', 'vibe': 'family', 'budget': 2, 'type': 'restaurant', 'audience': ['student', 'family'], 'description': 'Famous for its South Indian dishes and family-friendly atmosphere.', 'location_query': 'Novelty Restaurant, Bistupur, Jamshedpur'},
        {'name': 'Brubeck Bakery', 'vibe': 'cozy', 'budget': 1, 'type': 'cafe', 'audience': ['student'], 'description': 'A popular cafe in Sakchi known for its pastries and coffee.', 'location_query': 'Brubeck Bakery, Sakchi, Jamshedpur'},
        {'name': 'Mocha Jamshedpur', 'vibe': 'trendy', 'budget': 2, 'type': 'cafe', 'audience': ['student', 'professional'], 'description': 'A stylish cafe perfect for hanging out with friends.', 'location_query': 'Mocha Jamshedpur, Bistupur'}
    ],
    'outdoors': [
        {'name': 'Jubilee Park', 'vibe': 'relaxing', 'budget': 1, 'type': 'park', 'audience': ['student', 'family', 'professional'], 'description': 'The green heart of Jamshedpur, perfect for morning walks and evening strolls.', 'location_query': 'Jubilee Park, Jamshedpur'},
        {'name': 'Dimna Lake', 'vibe': 'scenic', 'budget': 1, 'type': 'lake', 'audience': ['student', 'family'], 'description': 'A beautiful artificial lake at the foothills of Dalma range, offering boating.', 'location_query': 'Dimna Lake, Jamshedpur'},
        {'name': 'Dalma Wildlife Sanctuary', 'vibe': 'adventurous', 'budget': 2, 'type': 'trek', 'audience': ['student', 'professional'], 'description': 'Ideal for a day trip involving trekking and nature watching.', 'location_query': 'Dalma Wildlife Sanctuary, Jharkhand'}
    ],
    'entertainment': [
        {'name': 'P&M Hi-Tech City Centre Mall', 'vibe': 'modern', 'budget': 2, 'type': 'mall', 'audience': ['student', 'family', 'professional'], 'description': 'Your one-stop destination for movies, shopping, and a food court.', 'location_query': 'P&M Hi-Tech City Centre Mall, Jamshedpur'},
        {'name': 'Eylex Multiplex', 'vibe': 'modern', 'budget': 2, 'type': 'cinema', 'audience': ['student', 'family'], 'description': 'A popular multiplex for watching the latest movies.', 'location_query': 'Eylex Cinema, Pardih, Jamshedpur'}
    ],
    'shopping': [
        {'name': 'Bistupur Market', 'vibe': 'bustling', 'budget': 2, 'type': 'market', 'audience': ['family', 'professional'], 'description': 'A major shopping hub with branded stores and local shops.', 'location_query': 'Bistupur Market, Jamshedpur'},
        {'name': 'Sakchi Market', 'vibe': 'bustling', 'budget': 1, 'type': 'market', 'audience': ['student', 'family'], 'description': 'A vibrant and crowded market, great for budget shopping and street food.', 'location_query': 'Sakchi Market, Jamshedpur'}
    ]
}

CATEGORIES_MAP = {
    # The key is now what the user sees and sends back
    "adventure & outdoors": "outdoors",
    "dining & food": "dining",
    "entertainment & leisure": "entertainment",
    "shopping": "shopping" # Simplified for list message
}

# Session management remains the same
user_sessions = {}

def generate_places_response(places_list, intro_text):
    """Generates a formatted string with place details and map links."""
    if not places_list:
        return "Sorry, I couldn't find anything matching your criteria. Let's try again?"
    
    response = intro_text + "\n\n"
    for place in places_list:
        location_query = place.get('location_query', place['name'])
        maps_link = create_maps_link(location_query)
        response += (
            f"📍 *{place['name']}*\n"
            f"_{place['description']}_\n"
            f"🗺️ Directions: {maps_link}\n\n"
        )
    # The thank you message is now added in the web server file along with the button
    return response

def handle_category_selection(user_id, message):
    """Handles the selection from the category list."""
    category_key = CATEGORIES_MAP.get(message.lower())
    if category_key:
        results = Jamshedpur_DATABASE.get(category_key, [])
        intro = f"Here are some options for *{message}*:"
        response_text = generate_places_response(results, intro)
        user_sessions.pop(user_id, None)
        # Return a tuple to signal a final response
        return ("SEND_FINAL_RESPONSE", response_text)
    else:
        # Fallback if something unexpected is received
        return "Sorry, I didn't recognize that category. Please try again."

def handle_personalize(user_id, message):
    """Manages the multi-step personalization flow."""
    state = user_sessions.get(user_id, {'flow': 'personalize', 'step': 'ask_role', 'filters': {}})

    if state['step'] == 'ask_role':
        state['step'] = 'ask_budget'
        user_sessions[user_id] = state
        return "Let's find the perfect spot! First, who are you?\n(e.g., *student*, *professional*, *family*)"

    elif state['step'] == 'ask_budget':
        state['filters']['role'] = message.lower()
        state['step'] = 'get_results'
        user_sessions[user_id] = state
        return "Got it. And what's your budget?\n(e.g., *cheap*, *mid-range*, *any*)"

    elif state['step'] == 'get_results':
        budget_map = {'cheap': 1, 'mid-range': 2, 'any': 99}
        state['filters']['budget'] = budget_map.get(message.lower(), 99)
        
        role_filter = state['filters']['role']
        budget_filter = state['filters']['budget']
        
        results = []
        for category in Jamshedpur_DATABASE.values():
            for place in category:
                if place['budget'] <= budget_filter and role_filter in place.get('audience', []):
                    results.append(place)
        
        intro = "Here are your personalized suggestions:"
        response_text = generate_places_response(results, intro)
        user_sessions.pop(user_id, None)
        # Return a tuple to signal a final response
        return ("SEND_FINAL_RESPONSE", response_text)
    return "Something went wrong. Let's start over."

def chatbot_reply(user_id, message):
    """Main function to route user messages."""
    msg_clean = message.strip().lower()

    # Handle the new "Main Menu" button press
    if msg_clean == "main menu":
        return "SEND_WELCOME"

    # Check for session-based flows first
    if user_id in user_sessions:
        session = user_sessions[user_id]
        if session.get('flow') == 'browse_category':
            return handle_category_selection(user_id, msg_clean)
        if session.get('flow') == 'personalize':
            return handle_personalize(user_id, msg_clean)
    
    # Simple keyword matching for main menu actions
    if msg_clean == "personalize my experience":
        user_sessions[user_id] = {'flow': 'personalize', 'step': 'ask_role'}
        return handle_personalize(user_id, None) # Start the flow
    
    if msg_clean == "browse categories":
        user_sessions[user_id] = {'flow': 'browse_category'}
        # The web server will now send the list message
        return "SEND_CATEGORY_LIST"

    if msg_clean == "surprise me!":
        all_places = [p for sublist in Jamshedpur_DATABASE.values() for p in sublist]
        random_place = random.choice(all_places)
        response_text = generate_places_response([random_place], "🎉 Surprise! How about this? 🎉")
        # Return a tuple to signal a final response
        return ("SEND_FINAL_RESPONSE", response_text)

    # Default welcome message for "Hi", "Hello", etc.
    return "SEND_WELCOME"

