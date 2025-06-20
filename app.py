from flask import Flask, render_template, request, jsonify, session
import json
import os
import requests
from config import Config
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "default-secret-key")  # Add this line
print("Server started")

# Load listings once at startup
with open(os.path.join(os.path.dirname(__file__), 'listings.json'), 'r') as f:
    listings = json.load(f)


def find_matching_listings(user_message, listings, max_results=3):
    # Very simple keyword-based filter for demo purposes
    # Extract suburb, bedrooms, or type keywords
    user_lower = user_message.lower()

    results = []
    for prop in listings:
        if len(results) >= max_results:
            break
        # Basic matching logic:
        match_suburb = any(suburb.lower() in user_lower for suburb in [prop['suburb']])
        match_type = any(ptype.lower() in user_lower for ptype in [prop['type']])
        match_bedrooms = False
        if 'bedroom' in user_lower:
            # check if number mentioned matches bedrooms
            import re
            match = re.search(r'(\d+)[ -]?bedroom', user_lower)
            if match and int(match.group(1)) == int(prop.get('bedrooms', 0)):
                match_bedrooms = True

        # If any match, add
        if match_suburb or match_type or match_bedrooms:
            results.append(prop)

    # If no specific filters matched, return some random samples
    if not results:
        results = listings[:max_results]

    return results


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/ask_property", methods=["POST"])
def ask_property():
    user_question = request.json.get("question")

    # TEMPORARY: Print the API key to the logs (remove this after debugging)
    print("DEBUG: OpenRouter API Key is:", Config.OPENROUTER_API_KEY)

    # Initialize session chat history if not present
    if 'chat_history' not in session:
        session['chat_history'] = []

    # Load prompt template
    with open("prompts/property_faq.txt", "r") as file:
        prompt_template = file.read()

    # Find matching listings from user message
    matched_props = find_matching_listings(user_question, listings)

    # Format matched properties info as a string to append to prompt
    if matched_props:
        props_info = "\nHere are some properties that might interest you:\n"
        for p in matched_props:
            props_info += f"- {p['address']}, {p['suburb']}: {p['bedrooms']} bed / {p['bathrooms']} bath / {p['type']} - Price: {p['price']}\n"
    else:
        props_info = "\nNo matching properties found."

    # Build conversation messages for GPT
    messages = [{"role": "system", "content": prompt_template}]

    # Add previous chat history from session (up to last 6 messages for context)
    history = session['chat_history'][-6:]
    messages.extend(history)

    # Add user current question
    messages.append({"role": "user", "content": user_question + props_info})

    headers = {
        "Authorization": f"Bearer {Config.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "Referer": "https://real-estate-chatbot-kp5e.onrender.com"
    }

    body = {
        "model": "openai/gpt-3.5-turbo",
        "messages": messages,
        "temperature": 0.7,
    }

    try:
        response = requests.post(Config.OPENROUTER_URL, headers=headers, json=body)

        # 🔍 Debug print
        print("Status Code:", response.status_code)
        print("Response Text:", response.text)

        response.raise_for_status()
        data = response.json()
        answer = data["choices"][0]["message"]["content"].strip()


    except Exception as e:
        answer = f"Error: {str(e)}"
        import traceback
        print("⚠️ OpenRouter request failed:")
        print("Exception:", e)
        traceback.print_exc()
        print("\n🔐 Headers Sent:")
        print(headers)
        print("\n📦 Payload Sent:")
        print(json.dumps(body, indent=2))
        try:
            print("\n📬 Response from OpenRouter:")
            print("Status code:", response.status_code)
            print("Response body:", response.text)
        except:
            print("❌ No response object available")
        # Update chat history
        session['chat_history'].append({"role": "user", "content": user_question + props_info})
        session['chat_history'].append({"role": "assistant", "content": answer})
        session.modified = True
        return jsonify({"answer": answer})


@app.route("/book_inspection", methods=["POST"])
def book_inspection():
    data = request.json
    name = data.get("name", "").strip()
    email = data.get("email", "").strip()
    phone = data.get("phone", "").strip()
    preferred_time = data.get("preferred_time", "").strip()

    # Here you could add real booking logic (database/email/etc.)
    # For demo, just confirm the booking details:

    message = (
        f"Thanks {name}! Your inspection has been booked for {preferred_time}. "
        f"We will contact you at {email} or {phone} if needed."
    )

    return jsonify({"message": message})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
