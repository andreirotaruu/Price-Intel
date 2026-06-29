from pydantic import BaseModel
from typing import Optional

class AnalyzeRequest(BaseModel):
    name: str
    category: str
    current_price: Optional[float] = None
    
