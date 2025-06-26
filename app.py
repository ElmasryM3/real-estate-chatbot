from flask import Flask, render_template, request, jsonify, session
from flask_mail import Mail, Message
import json
import os
import requests
from config import Config
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "default-secret-key")

mail = Mail(app)
print("Server started")

# Load listings on startup
with open(os.path.join(os.path.dirname(__file__), 'listings.json'), 'r') as f:
    listings = json.load(f)

def find_matching_listings(user_message, listings, max_results=3):
    user_lower = user_message.lower()
    results = []

    for prop in listings:
        if len(results) >= max_results:
            break
        match_suburb = prop['suburb'].lower() in user_lower
        match_type = prop['type'].lower() in user_lower
        match_bedrooms = False
        if 'bedroom' in user_lower:
            import re
            match = re.search(r'(\d+)[ -]?bedroom', user_lower)
            if match and int(match.group(1)) == int(prop.get('bedrooms', 0)):
                match_bedrooms = True
        if match_suburb or match_type or match_bedrooms:
            results.append(prop)

    return results if results else listings[:max_results]

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/ask_property", methods=["POST"])
def ask_property():
    user_question = request.json.get("question")
    if 'chat_history' not in session:
        session['chat_history'] = []

    with open("prompts/property_faq.txt", "r") as file:
        prompt_template = file.read()

    matched_props = find_matching_listings(user_question, listings)
    props_info = "\nHere are some properties that might interest you:\n"
    for p in matched_props:
        props_info += f"- {p['address']}, {p['suburb']}: {p['bedrooms']} bed / {p['bathrooms']} bath / {p['type']} - Price: {p['price']}\n"

    messages = [{"role": "system", "content": prompt_template}]
    messages.extend(session['chat_history'][-6:])
    messages.append({"role": "user", "content": user_question + props_info})

    headers = {
        "Authorization": f"Bearer {Config.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "Referer": "https://real-estate-chatbot-kp5e.onrender.com"
    }

    body = {
        "model": "openrouter/openai/gpt-3.5-turbo",
        "messages": messages,
        "temperature": 0.7
    }

    try:
        print("🔐 API Key:", Config.OPENROUTER_API_KEY)

        # ✅ Add this just before sending the request
        print("🔍 FINAL REQUEST DEBUG:")
        print("Headers:", headers)
        print("Body:", json.dumps(body, indent=2))

        response = requests.post(Config.OPENROUTER_URL, headers=headers, json=body)

        print("Response status code:", response.status_code)

        # ✅ Add this after the request
        print("❌ Response from OpenRouter:", response.text)

        response.raise_for_status()

        data = response.json()
        answer = data["choices"][0]["message"]["content"].strip()

    except Exception as e:
        import traceback
        print("❌ Error contacting OpenRouter:", str(e))
        traceback.print_exc()
        answer = f"Error: {str(e)}"

    session['chat_history'].append({"role": "user", "content": user_question + props_info})
    session['chat_history'].append({"role": "assistant", "content": answer})
    session.modified = True

    return jsonify({"answer": answer})

@app.route("/book_inspection", methods=["POST"])
def book_inspection():
    data = request.get_json()
    name = data.get("name")
    email = data.get("email")
    phone = data.get("phone")
    preferred_time = data.get("preferred_time")
    property_info = data.get("property", "N/A")

    try:
        msg = Message(
            subject="🔔 New Property Inspection Booking",
            recipients=["botivaai@gmail.com"],  # 🔁 Replace with your actual email
            body=f"""
New Inspection Booking:

Name: {name}
Email: {email}
Phone: {phone}
Property: {property_info}
Preferred Time: {preferred_time}
"""
        )
        mail.send(msg)
        return jsonify({"success": True, "message": "✅ Booking confirmation sent!"})
    except Exception as e:
        print("❌ Error sending email:", e)
        return jsonify({"success": False, "message": "Failed to send booking email."}), 500

@app.route("/book_property", methods=["POST"])
def book_property():
    return book_inspection()

@app.route("/demo")
def demo():
    return render_template("demo.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
