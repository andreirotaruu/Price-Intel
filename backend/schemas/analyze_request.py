from pydantic import BaseModel
from typing import Optional

class AnalyzeRequest(BaseModel):
    name: str
    category: str
    current_price: Optional[float] = None
    condition: Optional[str] = None
    item_id: Optional[str] = None
    
