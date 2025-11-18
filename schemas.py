from pydantic import BaseModel
from typing import List

class ItemBase(BaseModel):
    name: str
    category: str
    value: float
    rating: int

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