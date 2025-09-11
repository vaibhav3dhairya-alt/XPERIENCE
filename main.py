# This is the core server code for your WhatsApp chatbot, written in Python using Flask.
# It listens for messages from Twilio, processes them, and sends back a response.

import os
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

@app.route('/whatsapp', methods=['POST'])
def whatsapp_reply():
    """Responds to incoming messages with a TwiML response."""
    incoming_msg = request.values.get('Body', '').lower().strip()
    
    # Start our TwiML response
    resp = MessagingResponse()
    msg = resp.message()
    
    print(f"Received message: {incoming_msg}") # Log incoming messages for debugging

    # --- Chatbot Logic ---
    # This section replicates the flow from your design.

    # Initial greeting or main menu request
    if 'hi' in incoming_msg or 'hello' in incoming_msg or 'hey' in incoming_msg:
        response_text = (
            "Hi there! Welcome to Xperience, your exploration companion for Jamshedpur. 🧭\n\n"
            "Choose a path:\n"
            "1️⃣ Personalize my experience\n"
            "2️⃣ Browse 7 categories\n"
            "3️⃣ Surprise Me"
        )
        msg.body(response_text)
    
    # Browse categories command
    elif incoming_msg == '2' or 'browse' in incoming_msg:
        response_text = (
            "Great! Here are the 7 categories:\n\n"
            "*A.* Adventure & Outdoors 🌲\n"
            "*B.* Dining & Food 🍔\n"
            "*C.* Getaways & Nature 🏞️\n"
            "*D.* Cultural & Shopping 🛍️\n"
            "*E.* Entertainment & Leisure 🎬\n"
            "*F.* Sports & Fitness 🏋️\n"
            "*G.* Events & Wellness ✨\n\n"
            "Reply with the letter of the category you'd like to explore!"
        )
        msg.body(response_text)

    # Responses for each category
    elif incoming_msg == 'a':
        response_text = (
            "*Adventure & Outdoors* 🌲:\n\n"
            "*Jubilee Park*\n"
            "A central park with gardens, a zoo, and a laser show.\n"
            "Directions: https://maps.google.com/?q=Jubilee+Park,Jamshedpur\n\n"
            "*Dalma Wildlife Sanctuary*\n"
            "Known for its elephants and scenic trekking routes.\n"
            "Directions: https://maps.google.com/?q=Dalma+Wildlife+Sanctuary,Jamshedpur"
        )
        msg.body(response_text)
        
    elif incoming_msg == 'b':
        response_text = (
            "*Dining & Food* 🍔:\n\n"
            "*The Blue Diamond Restaurant*\n"
            "Popular for its North Indian and Chinese cuisine.\n"
            "Directions: https://maps.google.com/?q=The+Blue+Diamond+Restaurant,Jamshedpur\n\n"
            "*Dastarkhan*\n"
            "A well-regarded spot for authentic Mughlai dishes.\n"
            "Directions: https://maps.google.com/?q=Dastarkhan,Jamshedpur"
        )
        msg.body(response_text)

    elif incoming_msg == 'c':
        response_text = (
            "*Getaways & Nature* 🏞️:\n\n"
            "*Dimna Lake*\n"
            "A beautiful artificial lake at the foothills of the Dalma hills, perfect for picnics and boating.\n"
            "Directions: https://maps.google.com/?q=Dimna+Lake,Jamshedpur\n\n"
            "*Hudco Lake*\n"
            "Located in the Telco Colony, it offers a serene environment and boating facilities.\n"
            "Directions: https://maps.google.com/?q=Hudco+Lake,Jamshedpur"
        )
        msg.body(response_text)

    # Fallback message if the command is not understood
    else:
        msg.body("Sorry, I didn't quite get that. Please reply with 'Hi' to see the main menu again.")

    return str(resp)

if __name__ == "__main__":
    # The port is set by Render's environment variables.
    port = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=port)
