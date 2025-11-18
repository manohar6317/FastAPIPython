# app.py

from fastapi import FastAPI, Depends, Query
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel
from typing import List, Optional

# --- Configuration & Constants ---

DATABASE_URL = "sqlite:///./test.db"
CATEGORY_WEIGHTS = {"laptop": 1.2, "smartphone": 1.0, "headphones": 0.9, "monitor": 1.1}

# --- SQLAlchemy Setup ---

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- Database Model (ORM) ---

class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    category = Column(String)
    value = Column(Float)

# --- Pydantic Models (for API request/response) ---

class ItemBase(BaseModel):
    name: str
    category: str
    value: float

class ItemResponse(ItemBase):
    id: int

    class Config:
        from_attributes = True

class ItemWithScore(ItemBase):
    id: int
    score: float

    class Config:
        from_attributes = True

class ProcessResponse(BaseModel):
    top_items: List[ItemWithScore]
    count: int
    average_score: float

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
        if db.query(Item).first() is None:
            print("Database is empty. Seeding with sample data...")
            sample_items = [
                Item(name="Laptop Pro X", category="laptop", value=1499.99),
                Item(name="Smartphone Z", category="smartphone", value=899.50),
                Item(name="AudioMax Headphones", category="headphones", value=199.00),
                Item(name="UltraWide Monitor", category="monitor", value=650.0),
                Item(name="Laptop Air M2", category="laptop", value=1299.00),
                Item(name="Gamer Headset v2", category="headphones", value=120.75),
                Item(name="Smartwatch 5", category="wearable", value=350.0), # Category with no weight
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
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    seed_database(db)
    db.close()
    print("Startup complete.")

# --- Dependency for Database Session ---

def get_db():
    """FastAPI dependency to get a DB session for each request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- API Endpoint ---

@app.get("/", include_in_schema=False)
def read_root():
    """A simple root endpoint that provides a welcome message and a link to the docs."""
    return {"message": "Welcome to the Item Processing API. Visit /docs for interactive documentation."}

@app.post("/items", response_model=ItemResponse, status_code=201, tags=["Items"])
def create_item(item: ItemBase, db: Session = Depends(get_db)):
    """
    Create a new item in the database. The request body should be a JSON object
    with 'name', 'category', and 'value'.
    """
    # Create a SQLAlchemy model instance from the Pydantic model
    db_item = Item(**item.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item) # Refresh to get the new ID from the database
    return db_item


@app.post("/reset-database", status_code=200, tags=["Development"])
def reset_database():
    """
    Drops all data, recreates tables, and reseeds with sample data.
    USE WITH CAUTION. Intended for development.
    """
    print("Resetting database...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    seed_database(db)
    db.close()
    return {"message": "Database has been successfully reset and reseeded."}


@app.get("/process", response_model=ProcessResponse, tags=["Items"])
def process_items(
    top_n: int = Query(3, ge=1, description="Number of top-scoring items to return."),
    category: Optional[str] = Query(None, description="Filter items by a specific category."),
    db: Session = Depends(get_db)
):
    """
    Processes items, calculates their scores, and returns the top N items
    along with overall statistics. Can be filtered by category.
    """
    query = db.query(Item)
    if category:
        # If a category is provided, filter the database query
        query = query.filter(Item.category == category)

    items_to_process = query.all()
    
    # Calculate score for each item
    scored_items = []
    total_score = 0.0
    for item in items_to_process:
        weight = CATEGORY_WEIGHTS.get(item.category, 1.0) # Default to 1.0 if category not in weights
        score = item.value * weight
        total_score += score
        scored_items.append(ItemWithScore(
            id=item.id,
            name=item.name,
            category=item.category,
            value=item.value,
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
