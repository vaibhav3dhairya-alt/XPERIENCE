import random
from urllib.parse import quote_plus

# --- Helper function to create Google Maps links ---
def create_maps_link(location_query):
    """Creates a Google Maps search URL from a location string."""
    encoded_query = quote_plus(location_query)
    return f"https://www.google.com/maps/search/?api=1&query={encoded_query}"

# --- Mock Database for Jamshedpur Locations ---
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
    "1": ("Adventure & Outdoors", "outdoors"),
    "2": ("Dining & Food", "dining"),
    "3": ("Entertainment & Leisure", "entertainment"),
    "4": ("Cultural & Shopping", "shopping")
}

user_sessions = {}

def generate_places_response(places_list, intro_text):
    """Generates a formatted string with place details and map links."""
    if not places_list:
        return "Sorry, I couldn't find anything matching your criteria."
    
    response = intro_text + "\n\n"
    for place in places_list:
        location_query = place.get('location_query', place['name'])
        maps_link = create_maps_link(location_query)
        response += (
            f"📍 *{place['name']}*\n"
            f"_{place['description']}_\n"
            f"🗺️ Directions: {maps_link}\n\n"
        )
    
    response += "Thank you for using Xperience! ✨\n\nType 'Hi' to return to the main menu."
    return response

def handle_browse_category(user_id, message):
    """Handles the category browsing flow."""
    state = user_sessions.get(user_id, {})
    if state.get('step') == 'select_category':
        category_info = CATEGORIES_MAP.get(message)
        if category_info:
            category_name, category_key = category_info
            results = Jamshedpur_DATABASE.get(category_key, [])
            intro = f"Here are some options for *{category_name}*:"
            response = generate_places_response(results, intro)
            user_sessions.pop(user_id, None)
            return response
        else:
            return "Invalid selection. Please choose a number from the list."

    # This part starts the flow
    user_sessions[user_id] = {'flow': 'browse', 'step': 'select_category'}
    response = "Great! Here are the categories:\n"
    for key, (name, _) in sorted(CATEGORIES_MAP.items()):
        response += f"{key}. {name}\n"
    response += "\nPlease reply with the number of the category you'd like to explore."
    return response

def handle_surprise_me():
    """Selects and returns a random place."""
    all_places = [place for sublist in Jamshedpur_DATABASE.values() for place in sublist]
    random_place = random.choice(all_places)
    intro = "🎉 Surprise! How about this? 🎉"
    return generate_places_response([random_place], intro)

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
        response = generate_places_response(results, intro)
        user_sessions.pop(user_id, None)
        return response

    return "Something went wrong. Let's start over."

def chatbot_reply(user_id, message):
    """Main function to route user messages based on button taps or text."""
    # Check if user is already in a multi-step conversation
    if user_id in user_sessions:
        session = user_sessions[user_id]
        if session['flow'] == 'browse':
            return handle_browse_category(user_id, message)
        if session['flow'] == 'personalize':
            return handle_personalize(user_id, message)

    # Use .lower() for case-insensitive matching of button text
    msg_clean = message.strip().lower()

    if msg_clean == 'personalize my experience':
        user_sessions[user_id] = {'flow': 'personalize', 'step': 'ask_role'}
        return handle_personalize(user_id, message=None)
    
    elif msg_clean == 'browse categories':
        # Start the browse flow, which will ask the user to type a number
        return handle_browse_category(user_id, message=None)
    
    elif msg_clean == 'surprise me!':
        return handle_surprise_me()
    
    else:
        # For any other message ("Hi", "Hello", etc.), send the welcome message with buttons
        return "SEND_WELCOME_WITH_BUTTONS"

