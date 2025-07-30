from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from datetime import datetime
import json
import requests
import os

# Handle Replit auth import with fallback
try:
    from replit import auth
    REPLIT_AUTH_AVAILABLE = True
except ImportError:
    REPLIT_AUTH_AVAILABLE = False

app = Flask(__name__)
CORS(app)

# Hugging Face API Token
HF_TOKEN = os.environ.get("HF_TOKEN")
headers = {"Authorization": f"Bearer {HF_TOKEN}"}


def ask_code_mentor(prompt, model_name):
    # Format payload depending on model type
    if "zephyr" in model_name.lower():
        payload = {
            "inputs": [
                {"role": "system", "content": "You are a helpful coding mentor."},
                {"role": "user", "content": prompt}
            ],
            "options": {"wait_for_model": True}
        }
    else:
        # Mistral and other instruct models expect plain text
        payload = {
            "inputs": prompt,
            "options": {"wait_for_model": True}
        }

    model_url = f"https://api-inference.huggingface.co/models/{model_name}"

    print(f"📡 Request to: {model_url}")
    print(f"📤 Headers: {headers}")
    print(f"📄 Payload: {payload}")

    try:
        response = requests.post(model_url, headers=headers, json=payload)
        print("🔽 Status Code:", response.status_code)
        print("🧾 Response Text:", response.text)

        # Return Hugging Face errors clearly
        if response.status_code != 200:
            return f"❌ HF API Error {response.status_code}: {response.text}"

        data = response.json()

        # Zephyr returns a list of messages
        if isinstance(data, list):
            if "generated_text" in data[0]:
                return data[0]["generated_text"]
            elif "content" in data[-1]:
                return data[-1]["content"]

        # Mistral usually returns generated_text
        if isinstance(data, dict) and "generated_text" in data:
            return data["generated_text"]

        return str(data)  # fallback
    except Exception as e:
        return f"❌ Exception: {str(e)}"


@app.route("/")
def home():
    return render_template("test.html")


@app.route("/ask", methods=["POST"])
def ask():
    if REPLIT_AUTH_AVAILABLE:
        try:
            user = auth.get_user()
            username = user["username"]
        except:
            username = "anonymous"
    else:
        username = "anonymous"
    print(f"🔐 User asking: {username}")

    data = request.get_json()
    question = data.get("question")
    model = data.get("model")

    answer = ask_code_mentor(question, model)

    # Save chat history
    history_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "question": question,
        "answer": answer
    }

    if not os.path.exists("chats"):
        os.makedirs("chats")

    filename = f"chats/{username}.json"
    try:
        with open(filename, "r") as f:
            chat_history = json.load(f)
    except:
        chat_history = []

    chat_history.append(history_entry)

    with open(filename, "w") as f:
        json.dump(chat_history, f, indent=2)

    return jsonify({"answer": answer})


@app.route("/history")
def get_history():
    if REPLIT_AUTH_AVAILABLE:
        try:
            user = auth.get_user()
            username = user["username"]
        except:
            username = "anonymous"
    else:
        username = "anonymous"
    filename = f"chats/{username}.json"

    if os.path.exists(filename):
        with open(filename, "r") as f:
            chats = json.load(f)
    else:
        chats = []

    return jsonify({"history": chats})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
