from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pydantic import BaseModel
import uuid
from datetime import datetime
import pymongo
from pymongo import MongoClient
import os
import json
from confluent_kafka import Consumer, KafkaError

# Models
class Item(BaseModel):
    item_id: str
    name: str
    description: str
    price: float
    currency: str = "USD"
    available: bool = True

class Purchase(BaseModel):
    purchase_id: str
    user_id: str
    item_id: str
    item_name: str
    quantity: int
    price: float
    currency: str
    timestamp: str
    status: str

# Configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

# Initialize FastAPI app
app = FastAPI(title="E-Commerce API Server")

# CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection
def get_db():
    client = MongoClient(MONGO_URI)
    db = client.ecommerce_db
    try:
        yield db
    finally:
        client.close()

# Routes

@app.get("/")
def root():
    return {"message": "Welcome to the E-Commerce API Server"}


@app.get("/api/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/api/purchases", response_model=List[Purchase])
def get_purchases(user_id: str, db=Depends(get_db)):
    purchases = list(db.purchases.find({"user_id": user_id}, {"_id": 0}))
    return purchases

@app.get("/api/purchases/{purchase_id}", response_model=Purchase)
def get_purchase(purchase_id: str, db=Depends(get_db)):
    purchase = db.purchases.find_one({"purchase_id": purchase_id}, {"_id": 0})
    if not purchase:
        raise HTTPException(status_code=404, detail="Purchase not found")
    return purchase

@app.get("/api/items", response_model=List[Item])
def get_items(db=Depends(get_db)):
    items = list(db.items.find({"available": True}, {"_id": 0}))
    return items

# Kafka consumer background task
@app.on_event("startup")
async def startup_event():
    # This would typically be a more complex background task
    # that runs the Kafka consumer in a separate thread
    pass

# For demonstration: This would be a separate worker process
def start_kafka_consumer():
    consumer_conf = {
        'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
        'group.id': 'purchase-processor',
        'auto.offset.reset': 'earliest'
    }
    
    consumer = Consumer(consumer_conf)
    consumer.subscribe(['purchase-events'])
    
    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                else:
                    print(f"Consumer error: {msg.error()}")
                    break
                    
            try:
                purchase_event = json.loads(msg.value().decode('utf-8'))
                process_purchase(purchase_event)
            except Exception as e:
                print(f"Error processing message: {e}")
    finally:
        consumer.close()

def process_purchase(purchase_event):
    # Connect to MongoDB
    client = MongoClient(MONGO_URI)
    db = client.ecommerce_db
    
    # Create purchase record
    purchase = {
        "purchase_id": str(uuid.uuid4()),
        "user_id": purchase_event["user_id"],
        "item_id": purchase_event["item_id"],
        "item_name": purchase_event["item_name"],
        "quantity": purchase_event["quantity"],
        "price": purchase_event["price"],
        "currency": purchase_event["currency"],
        "timestamp": datetime.now().isoformat(),
        "status": "completed"
    }
    
    # Store in MongoDB
    db.purchases.insert_one(purchase)
    
    # In a real implementation, you would also produce a confirmation
    # message to the 'purchase-processed' topic

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
