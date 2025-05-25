+-------------------+                  +-------------------+
|                   |     1. Buy       |                   |
|    Frontend       |----------------->|  Client Server    |
|    (Browser)      |                  |  (Python/FastAPI) |
|                   |<-----------------|                   |
+-------------------+  6. Show Results +-------------------+
         ^                                      |
         |                                      | 2. Produce
         |                                      v
         |                             +-------------------+
         |                             |                   |
         |                             |  Kafka Broker     |
         |                             |  purchase-events  |
         |                             |                   |
         |                             +-------------------+
         |                                      |
         |                                      | 3. Consume
         |                                      v
         |                             +-------------------+
5. Return Purchases                    |                   |
         |                             |  API Server       |
         +-----------------------------+  (Python/FastAPI) |
                                       |                   |
                                       +-------------------+
                                                |
                                                | 4. Store/Read
                                                v
                                       +-------------------+
                                       |                   |
                                       |  MongoDB          |
                                       |  Database         |
                                       |                   |
                                       +-------------------+
