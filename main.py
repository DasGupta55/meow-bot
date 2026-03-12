import os
import requests
from fastapi import FastAPI, Request, Response

app = FastAPI()

# CONFIGURATION
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
GEMINI_KEY = os.getenv("GEMINI_KEY")
VERIFY_TOKEN = "meow_secret_123"

def get_ai_response(user_text):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    # This 'system_instruction' makes it behave like a professional agent
    payload = {
        "contents": [{
            "parts":[{"text": f"System: You are a premium business assistant with a sharp, Thomas Shelby-style intelligence. Be professional, cold, and efficient. Never use emojis. Reply to this: {user_text}"}]
        }]
    }
    try:
        response = requests.post(url, json=payload)
        data = response.json()
        # Fixed the 'candidates' error by adding a safety check
        if 'candidates' in data and len(data['candidates']) > 0:
            return data['candidates'][0]['content']['parts'][0]['text']
        else:
            return "I'm busy at the moment. State your business clearly."
    except:
        return "Connection lost. Speak again later."

def send_whatsapp(text, recipient_id):
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}", "Content-Type": "application/json"}
    payload = {
        "messaging_product": "whatsapp",
        "to": recipient_id,
        "type": "text",
        "text": {"body": text}
    }
    requests.post(url, json=payload)

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
        if 'entry' in data:
            value = data['entry'][0]['changes'][0]['value']
            
            # Handle Messages
            if 'messages' in value:
                msg = value['messages'][0]
                sender = msg['from']
                text = msg.get('text', {}).get('body', 'Hello')
                
                reply = get_ai_response(text)
                send_whatsapp(reply, sender)

            # Handle Missed Calls
            elif 'calls' in value:
                sender = value['calls'][0]['from']
                send_whatsapp("I don't appreciate being kept waiting. I'll get back to you when the time is right.", sender)
    except Exception as e:
        print(f"Log Error: {e}")
    
    return {"status": "ok"}
