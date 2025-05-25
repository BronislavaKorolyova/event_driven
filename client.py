from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import httpx
import uuid
from datetime import datetime
import json
from confluent_kafka import Producer
import socket
import os

# Models
class PurchaseRequest(BaseModel):
    user_id: str
    item_id: str
    item_name: str
    quantity: int = 1
    price: float
    currency: str = "USD"

# Configuration
API_SERVER_URL = os.getenv("API_SERVER_URL", "http://localhost:8000")
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

# Initialize FastAPI app
app = FastAPI(title="E-Commerce Client Server")

# CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Kafka Producer configuration
producer_conf = {
    'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
    'client.id': socket.gethostname()
}
kafka_producer = Producer(producer_conf)

# Templates and static files for frontend
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Delivery callback for Kafka
def delivery_callback(err, msg):
    if err:
        print(f'Message delivery failed: {err}')
    else:
        print(f'Message delivered to {msg.topic()} [{msg.partition()}]')

# Routes
@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/purchase")
async def purchase_item(purchase: PurchaseRequest):
    # Create event for Kafka
    event = {
        "event_id": str(uuid.uuid4()),
        "timestamp": datetime.now().isoformat(),
        "user_id": purchase.user_id,
        "item_id": purchase.item_id,
        "item_name": purchase.item_name,
        "quantity": purchase.quantity,
        "price": purchase.price,
        "currency": purchase.currency
    }
    
    # Convert to JSON and produce to Kafka
    try:
        kafka_producer.produce(
            'purchase-events',
            json.dumps(event).encode('utf-8'),
            callback=delivery_callback
        )
        kafka_producer.flush()
        
        return {
            "status": "success",
            "message": "Purchase request submitted",
            "event_id": event["event_id"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process purchase: {str(e)}")

@app.get("/api/purchases")
async def get_purchases(user_id: str):
    # Proxy request to API server
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_SERVER_URL}/api/purchases", params={"user_id": user_id})
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail="Failed to fetch purchases from API server"
            )
        
        return response.json()

@app.get("/api/items")
async def get_items():
    # Proxy request to API server
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_SERVER_URL}/api/items")
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail="Failed to fetch items from API server"
            )
        
        return response.json()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
