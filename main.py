import json
import os
import random
import logging
from uuid import uuid4
from typing import Literal, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from mangum import Mangum

# 1) LOGGING CONFIGURATION
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s — %(levelname)s — %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

# 2) YOUR MODELS
class Book(BaseModel):
    name: str
    genre: Literal["fiction", "non-fiction"]
    price: float
    book_id: Optional[str] = uuid4().hex

class Location(BaseModel):
    time: float  # milliseconds since epoch
    lat: float
    lng: float

# 3) DATA FILES
BOOKS_FILE = "books.json"
BOOKS = []
if os.path.exists(BOOKS_FILE):
    with open(BOOKS_FILE, "r") as f:
        BOOKS = json.load(f)

LOCATIONS_FILE = "locations.json"
LOCATIONS = []
if os.path.exists(LOCATIONS_FILE):
    with open(LOCATIONS_FILE, "r") as f:
        LOCATIONS = json.load(f)

# 4) FASTAPI APP
app = FastAPI()
handler = Mangum(app)

# 5) LOGGING MIDDLEWARE
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"→ {request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"← {request.method} {request.url.path} — {response.status_code}")
    return response

# 6) ROUTES
@app.get("/")
async def root():
    return {"message": "Welcome to my bookstore app!"}

@app.get("/list-books")
async def list_books():
    return {"books": BOOKS}

@app.get("/book_by_index/{index}")
async def book_by_index(index: int):
    if index < len(BOOKS):
        return BOOKS[index]
    else:
        raise HTTPException(404, f"Book index {index} out of range ({len(BOOKS)}).")

@app.post("/add-book")
async def add_book(book: Book):
    book.book_id = uuid4().hex
    json_book = jsonable_encoder(book)
    BOOKS.append(json_book)
    with open(BOOKS_FILE, "w") as f:
        json.dump(BOOKS, f)
    return {"book_id": book.book_id}

@app.post("/add-location")
async def add_location(location: Location):
    json_location = jsonable_encoder(location)
    LOCATIONS.append(json_location)
    with open(LOCATIONS_FILE, "w") as f:
        json.dump(LOCATIONS, f)
    return {}

@app.get("/get-locations")
async def get_locations():
    # Return locations sorted by time in descending order, converting ms timestamp to ISO datetime
    sorted_locations = sorted(LOCATIONS, key=lambda x: x["time"], reverse=True)
    converted = []
    for loc in sorted_locations:
        # Convert milliseconds to seconds and then to datetime
        dt = datetime.fromtimestamp(loc["time"] / 1000.0)
        loc_copy = loc.copy()
        loc_copy["time"] = dt.isoformat()
        converted.append(loc_copy)
    return converted

@app.get("/get-book")
async def get_book(book_id: str):
    for book in BOOKS:
        if book.book_id == book_id:
            return book
    raise HTTPException(404, f"Book ID {book_id} not found in database.")
