from fastapi import FastAPI, Request, Response
import os

app = FastAPI()

@app.get("/webhook")
async def verify(request: Request):
    params = request.query_params
    verify_token = "meow_secret_123" 
    
    if params.get("hub.mode") == "subscribe" and params.get("hub.verify_token") == verify_token:
        return Response(content=params.get("hub.challenge"), media_type="text/plain")
    return "Verification failed", 403

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    print("Received event:", data)
    return {"status": "ok"}
