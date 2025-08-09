import time
import pyrebase
import openai
import traceback
from flask import Flask, request, jsonify, session
from flask_cors import CORS
import random
import json

app = Flask(__name__)
# Use a strong secret key - this is used to encrypt the session
app.secret_key = "your-strong-secret-key-change-this-in-production"

# Configure CORS with more specific settings
CORS(app, 
     supports_credentials=True, 
     origins=["http://localhost:5000", "http://127.0.0.1:5000", "null"],
     allow_headers=["Content-Type", "Authorization"],
     expose_headers=["Content-Type", "Authorization"],
     methods=["GET", "POST", "OPTIONS"])

# Session configuration - critical for persistence
app.config['SESSION_TYPE'] = 'filesystem'  # Store sessions on filesystem
app.config['SESSION_PERMANENT'] = True     # Make sessions persistent
app.config['PERMANENT_SESSION_LIFETIME'] = 1800  # 30 minutes
app.config['SESSION_COOKIE_SAMESITE'] = None  # For development - in prod use 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False    # For development - in prod use True with HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True

# ----------------------------------------------------------------------------
# 1. OpenRouter / OpenAI Setup
# ----------------------------------------------------------------------------
api_key = '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'
openai_client = openai.OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1")

# ----------------------------------------------------------------------------
# 2. Firebase Connection & Setup
# ----------------------------------------------------------------------------
firebaseConfig = {
    'apiKey': "AIzaSyACg9ifco1xSUUJGkYT-bwJSsXgXuyAJm8",
    'authDomain': "drdruggs-26916.firebaseapp.com",
    'projectId': "drdruggs-26916",
    'storageBucket': "drdruggs-26916.firebasestorage.app",
    'messagingSenderId': "318973415310",
    'appId': "1:318973415310:web:6da6e7f1fe206af5d69edf",
    'measurementId': "G-RF7YN9JDTY",
    'databaseURL': "https://drdruggs-26916-default-rtdb.firebaseio.com/"
}

firebase = pyrebase.initialize_app(firebaseConfig)
auth = firebase.auth()
db = firebase.database()

# ----------------------------------------------------------------------------
# 3. User Intent & Emotion Analysis
# ----------------------------------------------------------------------------
def analyze_user_message(user_message):
    """
    Analyze the user's message to extract intent and emotional state.
    Returns a dictionary with intent and emotion analysis.
    """
    try:
        prompt = f"""
        Analyze the following user message and identify:
        1. User's main intent (seeking advice, venting, asking a question, sharing progress, etc.)
        2. User's emotional state (happy, sad, anxious, neutral, etc.)
        
        User message: "{user_message}"
        
        Provide only a JSON object with keys "intent" and "emotion" - no explanations:
        """
        
        response = openai_client.chat.completions.create(
            model="openai/gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            timeout=5
        )
        
        # Extract the JSON content from the response
        analysis_text = response.choices[0].message.content
        print(f"Analysis response: {analysis_text}")
        
        try:
            # Try proper JSON parsing first
            json_start = analysis_text.find('{')
            json_end = analysis_text.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = analysis_text[json_start:json_end]
                analysis = json.loads(json_str)
                return {
                    "intent": analysis.get("intent", "unknown"),
                    "emotion": analysis.get("emotion", "neutral")
                }
        except json.JSONDecodeError:
            # Fallback to manual parsing
            intent = None
            emotion = None
            
            if '"intent"' in analysis_text:
                intent_start = analysis_text.find('"intent"') + len('"intent"') + 1
                intent_end = analysis_text.find('"', intent_start + 1)
                intent = analysis_text[intent_start:intent_end].strip(': "')
            
            if '"emotion"' in analysis_text:
                emotion_start = analysis_text.find('"emotion"') + len('"emotion"') + 1
                emotion_end = analysis_text.find('"', emotion_start + 1)
                emotion = analysis_text[emotion_start:emotion_end].strip(': "')
                
            return {
                "intent": intent or "unknown",
                "emotion": emotion or "neutral"
            }
    
    except Exception as e:
        print(f"Error analyzing user message: {e}")
        return {"intent": "unknown", "emotion": "neutral"}

# ----------------------------------------------------------------------------
# 4. Storage Functions
# ----------------------------------------------------------------------------
def store_user_entry(user_id, content, is_name_response=False):
    """
    Store a user message with intent and emotion analysis in Firebase.
    """
    try:
        # Analyze the user message
        analysis = analyze_user_message(content)
        print(f"Analysis for '{content}': {analysis}")
        
        # Create the data structure
        data = {
            "content": content,
            "intent": analysis["intent"],
            "emotion": analysis["emotion"],
            "timestamp": int(time.time() * 1000)  # millisecond timestamp
        }
        
        # If this is a name response, add a flag
        if is_name_response:
            data["is_name"] = True
            # Store the name in a special profile entry as well
            db.child("conversations").child(user_id).child("profile").set({"name": content})
            print(f"Name '{content}' stored for user {user_id}")
        
        # Push the new message under conversations/<user_id>
        result = db.child("conversations").child(user_id).push(data)
        print(f"User entry stored for user {user_id} with key: {result['name']}")
        
        return result["name"]
    except Exception as e:
        print(f"Error storing user entry: {e}")
        return None

def get_user_name(user_id):
    """Get user name from profile or recent entries."""
    try:
        # First try the profile
        profile = db.child("conversations").child(user_id).child("profile").get().val()
        if profile and "name" in profile:
            return profile["name"]
        
        # If no profile, check recent entries with is_name flag
        entries = db.child("conversations").child(user_id).order_by_child("timestamp").get()
        if entries.each():
            for entry in entries.each():
                data = entry.val()
                if data.get("is_name", False):
                    return data.get("content")
                
        return None
    except Exception as e:
        print(f"Error getting user name: {e}")
        return None

def check_conversation_history(user_id):
    """Check if the user has any conversation history."""
    try:
        # Get one entry to check if the user exists
        entries = db.child("conversations").child(user_id).limit_to_first(1).get()
        return entries.each() is not None and len(list(entries.each())) > 0
    except Exception as e:
        print(f"Error checking conversation history: {e}")
        return False

def get_user_entries(user_id, limit=10):
    """
    Retrieve the most recent user entries with their analysis.
    """
    try:
        entries = db.child("conversations").child(user_id).order_by_child("timestamp").limit_to_last(limit).get()
        
        user_entries = []
        if entries.each():
            for entry in entries.each():
                # Skip special entries
                if entry.key() == "profile":
                    continue
                    
                entry_data = entry.val()
                entry_data["id"] = entry.key()  # Add the entry ID to the data
                user_entries.append(entry_data)
        
        return user_entries
    except Exception as e:
        print(f"Error getting user entries: {e}")
        return []

# ----------------------------------------------------------------------------
# 5. Helper Functions (Tips, Emojis, etc.)
# ----------------------------------------------------------------------------
def add_emoji(response):
    emoji_map = {
        "sad": "😔", "happy": "😊", "anxious": "😟", "excited": "😃",
        "angry": "😠", "stress": "😩", "support": "🤗", "love": "❤",
        "sorry": "☹😟", "bullying": "😞", "understand": "🤍",
    }
    for word, emoji in emoji_map.items():
        if word in response.lower():
            return f"{response} {emoji}"
    return response

def get_stress_and_headache_tips():
    return (
        "Based on your mention of a headache or stress, you might benefit from these tips:\n"
        "- Take short breaks to breathe deeply or do light stretching.\n"
        "- Drink plenty of water throughout the day.\n"
        "- Identify any stress triggers and try to manage or reduce them.\n"
        "- Ensure you get enough sleep (7–9 hours) when possible.\n\n"
        "How have you been feeling since you last mentioned your headache?"
    )

def call_openai_with_retry(messages, max_retries=3, delay=2):
    """Call OpenAI with retry logic to handle transient errors."""
    for attempt in range(max_retries):
        try:
            response = openai_client.chat.completions.create(
                model="openai/gpt-3.5-turbo",
                messages=messages,
                timeout=10
            )
            return response
        except Exception as e:
            print(f"OpenAI connection error on attempt {attempt+1}/{max_retries}: {e}")
            time.sleep(delay)
    raise Exception("Max retries exceeded for OpenAI call.")

def get_system_prompt():
    """Return the system prompt for Dr. Druggs."""
    return (
        "You are Dr. Druggs, a compassionate therapy Indian chatbot. You provide emotional support, "
        "ask follow up questions based on the user's previous condition, and check in with the user "
        "about how they are doing. You also give suggestions regarding coping strategies, mental health "
        "guidance, and simple healthcare tips. Note that you are not a doctor, and you should always "
        "include a short disclaimer and encourage professional advice if necessary."
    )

def is_likely_name(text):
    """Simple heuristic to determine if text is likely a name."""
    # Clean the text
    text = text.strip()
    
    # Basic validation to check if it looks like a name
    non_name_indicators = [
        "hi", "hello", "hey", "good morning", "good afternoon", 
        "good evening", "thanks", "thank you", "ok", "okay",
        "yes", "no", "not", "don't", "do not", "cannot", "can't",
        "?", "!", ".", ",", ":", ";", "-", "/", "\\", "http", "www"
    ]
    
    # Check if the message is a likely name (simple heuristic)
    words = text.split()
    if not words:
        return False
        
    first_word = words[0].lower()
    
    return (len(text) <= 30 and  # Not too long
        not any(indicator in text.lower() for indicator in non_name_indicators) and
        not text.isdigit() and  # Not just a number
        not first_word in ["i", "my", "me", "we", "us", "our", "you", "your", "they", "them", "their"])

# ----------------------------------------------------------------------------
# 6. Flask Chat Endpoint
# ----------------------------------------------------------------------------
user_id_store = None
first_time_users = set()  # Keep track of users in their first session

@app.route("/check-session", methods=["GET"])
def check_session():
    global user_id_store
    if user_id_store:
        return jsonify({"message": "Session active", "userId": user_id_store})
    else:
        return jsonify({"message": "No active session", "userId": None})

@app.route("/save-user", methods=["POST"])
def save_user():
    global user_id_store, first_time_users
    data = request.get_json()
    user_id = data.get("userId")
    if not user_id:
        return jsonify({"error": "No user id provided"}), 400
    
    # Store the user id in global variable
    user_id_store = user_id
    print(f"User ID saved in global variable: {user_id_store}")
    
    # Check if this is a first-time user
    has_history = check_conversation_history(user_id)
    if not has_history:
        first_time_users.add(user_id)
        print(f"New user detected: {user_id}")
    
    # Set as a cookie too (backup method)
    response = jsonify({
        "message": "User ID saved", 
        "userId": user_id,
        "isFirstTime": not has_history
    })
    response.set_cookie('user_id', user_id, max_age=86400)  # 24 hour cookie
    
    return response

@app.route("/chat", methods=["POST"])
def chat():
    global user_id_store, first_time_users
    data = request.json
    user_input = data.get("message", "")
    
    # Get user ID
    user_id = user_id_store or request.cookies.get('user_id')
    print(f"Retrieved user ID: {user_id}")
    
    try:
        # Get user's name if it exists
        user_name = get_user_name(user_id)
        
        # Determine if this is a first-time user (no history)
        is_first_time = user_id in first_time_users
        
        # CASE 1: First message for first-time user - always ask for name
        # CASE 1: First message for first-time user - always ask for name
        if is_first_time and not user_name:
            # If user has sent input, check if it's a name
            if user_input:
                # Make sure this doesn't look like regular chat
                if is_likely_name(user_input):
                    store_user_entry(user_id, user_input, is_name_response=True)
                    first_time_users.discard(user_id)  # No longer a first-time user
                    return jsonify({"reply": f"Nice to meet you, {user_input}! How are you feeling today?"})
                else:
                    # Not a name, but we need one - ask again
                    return jsonify({"reply": "I'd love to know your name before we continue. What would you like me to call you?"})
            else:
                # First connection, no input yet - ask for name
                return jsonify({"reply": "Hello, I'm Dr. Druggs, your compassionate therapy chatbot. May I know your name?"})
        
        # CASE 2: Returning user with no input (just opened the chat)
        elif not user_input:
            greeting = f"Welcome back, {user_name}!" if user_name else "Welcome back!"
            return jsonify({"reply": f"{greeting} How can I help you today?"})
        
        # CASE 3: Normal chat message processing
        store_user_entry(user_id, user_input)
        
        # Check for special keywords
        lower_input = user_input.lower()
        if "headache" in lower_input or "stress" in lower_input:
            tips_message = get_stress_and_headache_tips()
            return jsonify({"reply": add_emoji(tips_message)})
        
        # Build conversation context and generate response
        messages = [{"role": "system", "content": get_system_prompt()}]
        
        # Add user name context if available
        if user_name:
            messages.append({
                "role": "system", 
                "content": f"The user's name is {user_name}. Address them by name occasionally."
            })
        
        # Add conversation history
        entries = get_user_entries(user_id, limit=5)
        for entry in entries:
            emotion_context = f"User's emotion: {entry.get('emotion', 'neutral')}. "
            intent_context = f"User's intent: {entry.get('intent', 'unknown')}. "
            
            messages.append({
                "role": "assistant", 
                "content": emotion_context + intent_context
            })
            
            messages.append({
                "role": "user",
                "content": entry.get("content", "")
            })
        
        # Ensure latest message is included
        if not any(msg["content"] == user_input and msg["role"] == "user" for msg in messages):
            messages.append({"role": "user", "content": user_input})
        
        # Call OpenAI
        response = call_openai_with_retry(messages)
        bot_reply = response.choices[0].message.content
        
        # Add emoji and return
        bot_reply_with_emoji = add_emoji(bot_reply)
        return jsonify({"reply": bot_reply_with_emoji})

    except Exception as e:
        traceback.print_exc()
        print(f"❌ Error processing request: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/feel-good-lists", methods=["GET"])
def feel_good_lists():
    feel_good_data = {
        "quote": random.choice([
            "You are capable of amazing things! 💪",
            "Happiness is not out there, it's in you! 😊",
            "You deserve love and kindness. ❤",
            "You are special!!"
        ]),
        "song": random.choice([
            "🎶 'Here Comes the Sun' - The Beatles",
            "🎵 'Happy' - Pharrell Williams",
            "🎧 'Don't Stop Believin'' - Journey",
            "🎵 'Baby Shark dududdududu!!"
        ]),
        "activity": random.choice([
            "Take a deep breath and smile. 🌿",
            "Go for a 10-minute walk. 🚶‍♂",
            "Take yourself on a beach date!!",
            "Write down three things you're grateful for. ✍"
        ])
    }
    return jsonify(feel_good_data)

if __name__ == "__main__":
    app.run(debug=True, port=5000)