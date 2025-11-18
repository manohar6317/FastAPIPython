import random
from fastapi import FastAPI, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

import models
import schemas
from database import SessionLocal, engine, get_db

# --- Configuration & Constants ---

CATEGORY_WEIGHTS = {"laptop": 1.2, "smartphone": 1.0, "headphones": 0.9, "monitor": 1.1}

# Create all database tables
models.Base.metadata.create_all(bind=engine)

# --- FastAPI App Initialization ---

app = FastAPI(
    title="Item Processing API",
    description="An API to process items, calculate scores, and return analytics.",
    version="1.0.0"
)

# --- Database Seeding and Startup Event ---

def seed_database(db: Session):
    """Seeds the database with sample items if it's empty."""
    try:
        # Check if the table is empty
        if db.query(models.Item).first() is None:
            print("Database is empty. Seeding with sample data...")
            sample_items = [
                models.Item(name="Laptop Pro X", category="laptop", value=1499.99, rating=random.randint(1, 4)),
                models.Item(name="Smartphone Z", category="smartphone", value=899.50, rating=random.randint(1, 4)),
                models.Item(name="AudioMax Headphones", category="headphones", value=199.00, rating=random.randint(1, 4)),
                models.Item(name="UltraWide Monitor", category="monitor", value=650.0, rating=random.randint(1, 4)),
                models.Item(name="Laptop Air M2", category="laptop", value=1299.00, rating=random.randint(1, 4)),
                models.Item(name="Gamer Headset v2", category="headphones", value=120.75, rating=random.randint(1, 4)),
                models.Item(name="Smartwatch 5", category="wearable", value=350.0, rating=random.randint(1, 4)), # Category with no weight
            ]
            db.add_all(sample_items)
            db.commit()
            print("Seeding complete.")
        else:
            print("Database already contains data. Skipping seed.")
    except Exception as e:
        print(f"An error occurred during seeding: {e}")
        db.rollback()

@app.on_event("startup")
def on_startup():
    """Create database tables and seed data on application startup."""
    print("Application starting up...")
    db = SessionLocal()
    seed_database(db)
    db.close()
    print("Startup complete.")

# --- API Endpoint ---

@app.get("/", include_in_schema=False)
def read_root():
    """A simple root endpoint that provides a welcome message and a link to the docs."""
    return {"message": "Welcome to the Item Processing API. Visit /docs for interactive documentation."}

@app.post("/items", response_model=schemas.ItemResponse, status_code=201, tags=["Items"])
def create_item(item: schemas.ItemBase, db: Session = Depends(get_db)):
    """
    Create a new item in the database. The request body should be a JSON object
    with 'name', 'category', and 'value'.
    """
    # Create a SQLAlchemy model instance from the Pydantic model
    db_item = models.Item(**item.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item) # Refresh to get the new ID from the database
    return db_item

@app.get("/items", response_model=List[schemas.ItemResponse], tags=["Items"])
def read_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retrieve a list of items, with optional pagination.
    """
    items = db.query(models.Item).offset(skip).limit(limit).all()
    return items

@app.get("/items/{item_id}", response_model=schemas.ItemResponse, tags=["Items"])
def read_item(item_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a single item by its ID.
    """
    db_item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return db_item

@app.put("/items/{item_id}", response_model=schemas.ItemResponse, tags=["Items"])
def update_item(item_id: int, item: schemas.ItemBase, db: Session = Depends(get_db)):
    """
    Update an existing item's name, category, and value by its ID.
    """
    db_item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")

    # Update the fields of the existing item
    item_data = item.model_dump()
    for key, value in item_data.items():
        setattr(db_item, key, value)

    db.commit()
    db.refresh(db_item)
    return db_item

@app.delete("/items/{item_id}", status_code=204, tags=["Items"])
def delete_item(item_id: int, db: Session = Depends(get_db)):
    """
    Delete an item from the database by its ID.
    """
    db_item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    db.delete(db_item)
    db.commit()

@app.post("/reset-database", status_code=200, tags=["Development"])
def reset_database():
    """
    Drops all data, recreates tables, and reseeds with sample data.
    USE WITH CAUTION. Intended for development.
    """
    print("Resetting database...")
    models.Base.metadata.drop_all(bind=engine)
    models.Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    seed_database(db)
    db.close()
    return {"message": "Database has been successfully reset and reseeded."}


@app.get("/process", response_model=schemas.ProcessResponse, tags=["Items"])
def process_items(
    top_n: int = Query(3, ge=1, description="Number of top-scoring items to return."),
    category: Optional[str] = Query(None, description="Filter items by a specific category."),
    db: Session = Depends(get_db)
):
    """
    Processes items, calculates their scores, and returns the top N items
    along with overall statistics. Can be filtered by category.
    """
    query = db.query(models.Item)
    if category:
        # If a category is provided, filter the database query
        query = query.filter(models.Item.category == category)

    items_to_process = query.all()
    
    # Calculate score for each item
    scored_items = []
    total_score = 0.0
    for item in items_to_process:
        weight = CATEGORY_WEIGHTS.get(item.category, 1.0) # Default to 1.0 if category not in weights
        score = item.value * weight
        total_score += score
        scored_items.append(schemas.ItemWithScore(
            id=item.id,
            name=item.name,
            category=item.category,
            value=item.value,
            rating=item.rating,
            score=score
        ))

    # Sort items by score in descending order
    scored_items.sort(key=lambda x: x.score, reverse=True)

    item_count = len(scored_items)
    average_score = (total_score / item_count) if item_count > 0 else 0.0

    return {
        "top_items": scored_items[:top_n],
        "count": item_count,
        "average_score": round(average_score, 2)
    }
