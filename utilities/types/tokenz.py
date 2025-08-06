import uuid
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime

class Tokenz(BaseModel):
    id: str = Field(default_factory=uuid.uuid4, alias="_id")
    total_tokens: int
    input_tokens: int
    output_tokens: int
    model_name: str = "gemini_1_5_flash"
    question_type: Optional[str] = None
    thread_id: str
    user_id: str
    update_time: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "_id": "6790bfac3d32877717dcee94",
                "total_tokens": 284,
                "input_tokens": 192,
                "output_tokens": 92,
                "model_name": "gemini_1_5_flash",
                "question_type": "multiple_choice",
                "thread_id": "1d56d4f1-00e4-413e-998a-9e8b1830d05d",
                "user_id": "1b1242b0-46df-4e30-9491-df8f45ef1d9e",
                "update_time": "2025-01-22T09:51:40.669Z"
            }
        }

class TokenzUpdate(BaseModel):
    total_tokens: Optional[int]
    input_tokens: Optional[int]
    output_tokens: Optional[int]
    model_name: Optional[str]
    question_type: Optional[str]
    thread_id: Optional[str]
    user_id: Optional[str]
    update_time: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "total_tokens": 284,
                "input_tokens": 192,
                "output_tokens": 92,
                "model_name": "gemini_1_5_flash",
                "question_type": "multiple_choice",
                "thread_id": "1d56d4f1-00e4-413e-998a-9e8b1830d05d",
                "user_id": "1b1242b0-46df-4e30-9491-df8f45ef1d9e",
                "update_time": "2025-01-22T09:51:40.669Z"
            }
        }
