from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from replit import auth
from datetime import datetime
import json
import requests
import os

app = Flask(__name__)
CORS(app)

# Hugging Face model endpoint
headers = {
    "Authorization": f"Bearer {os.environ.get('HF_TOKEN')}"
}

def ask_code_mentor(prompt, model_name):
    payload = {
        "inputs": f"<|user|>\n{prompt}\n<|assistant|>\n",
        "options": {"wait_for_model": True}
    }

    model_url = f"https://api-inference.huggingface.co/models/{model_name}"

    response = requests.post(model_url, headers=headers, json=payload)
    try:
        return response.json()[0]['generated_text']
    except Exception as e:
        print("❌ ERROR:", e)
        print("⚠️ Response text:", response.text)
        return "❌ AI failed to respond. Check backend logs or HuggingFace token."

@app.route("/")
def home():
    return render_template("test.html")

@app.route('/ask', methods=['POST'])
def ask():
    user = auth.get_user()
    username = user['username']
    print(f"🔐 User asking: {username}")

    data = request.get_json()
    question = data.get('question')
    model = data.get('model')

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
    user = auth.get_user()
    username = user['username']
    filename = f"chats/{username}.json"

    if os.path.exists(filename):
        with open(filename, "r") as f:
            chats = json.load(f)
    else:
        chats = []

    return jsonify({"history": chats})

if __name__ == "__main__":
    print("✅ Testing AI backend...")
    print(ask_code_mentor("def greet(name): print('Hello ' + name)", "HuggingFaceH4/zephyr-7b-beta"))
    app.run(host="0.0.0.0", port=5000)
