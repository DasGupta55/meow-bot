import os
import requests
from fastapi import FastAPI, Request, Response

app = FastAPI()

# --- CONFIGURATION ---
# We will set these in Render so they stay secret
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
GEMINI_KEY = os.getenv("GEMINI_KEY")
VERIFY_TOKEN = "meow_secret_123"

def get_ai_response(user_text):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    payload = {"contents": [{"parts":[{"text": f"You are a helpful WhatsApp assistant. Reply concisely: {user_text}"}]}]}
    response = requests.post(url, json=payload)
    return response.json()['candidates'][0]['content']['parts'][0]['text']

def send_whatsapp(text, recipient_id):
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}", "Content-Type": "application/json"}
    payload = {
        "messaging_product": "whatsapp",
        "to": recipient_id,
        "type": "text",
        "text": {"body": text}
    }
    requests.post(url, json=payload, headers=headers)

@app.get("/webhook")
async def verify(request: Request):
    params = request.query_params
    if params.get("hub.verify_token") == VERIFY_TOKEN:
        return Response(content=params.get("hub.challenge"), media_type="text/plain")
    return "Error", 403

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    try:
        value = data['entry'][0]['changes'][0]['value']
        
        # 1. Handle Messages
        if 'messages' in value:
            msg = value['messages'][0]
            sender = msg['from']
            text = msg.get('text', {}).get('body', '')
            
            ai_reply = get_ai_response(text)
            send_whatsapp(ai_reply, sender)

        # 2. Handle Missed Calls
        elif 'calls' in value:
            call_data = value['calls'][0]
            sender = call_data['from']
            send_whatsapp("Hey! I just missed your call. How can I help you?", sender)

    except Exception as e:
        print(f"Error: {e}")
    
    return {"status": "ok"}
