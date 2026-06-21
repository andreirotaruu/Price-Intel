from pydantic import BaseModel
from typing import List

class CollectRequest(BaseModel):
    name: str
    category: str
    marketplace: str
    current_price: float
    condition: str


class CollectBulkRequest(BaseModel):
    listings: List[CollectRequest]
