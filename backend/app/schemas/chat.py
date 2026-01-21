from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class ChatQuery(BaseModel):
    query: str
    context: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    answer: str
    sources: Optional[List[Dict[str, Any]]] = None
    confidence: Optional[float] = None
