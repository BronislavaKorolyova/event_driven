#https://github.com/BronislavaKorolyova/event_driven

# Rebuild everything clean
docker compose build --no-cache

# Start everything fresh
docker compose up -d


#Fill mongo DB
docker exec -it mongo mongosh -u root -p example


use ecommerce_db
db.items.insertMany([
  {
    "item_id": "item1",
    "name": "Sample Item 1",
    "description": "A great product",
    "price": 19.99,
    "currency": "USD",
    "available": true
  },
  {
    "item_id": "item2",
    "name": "Sample Item 2",
    "description": "Another awesome product",
    "price": 29.99,
    "currency": "USD",
    "available": true
  }
])

