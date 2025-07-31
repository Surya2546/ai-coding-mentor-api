def ask_code_mentor(prompt, model_name):
    # Map model names to your HF Space URLs
    model_urls = {
        "zephyr": "https://chakri1211-zephyr-api.hf.space",
        "mistral": "https://chakri1211-mistral-api.hf.space"
    }

    # Pick the correct Space endpoint
    if model_name.lower() in model_urls:
        model_url = model_urls[model_name.lower()] + "/run/predict"
    else:
        return "❌ Unknown model selected."

    payload = {
        "data": [f"<|user|>\n{prompt}\n<|assistant|>\n"]
    }

    try:
        response = requests.post(model_url, json=payload)
        if response.status_code == 200:
            result = response.json()
            # Gradio Spaces return the output inside result['data']
            return result['data'][0]
        else:
            return f"❌ Space API Error {response.status_code}: {response.text}"
    except Exception as e:
        return f"❌ Error calling Space API: {str(e)}"
