from pydantic import BaseModel

class CollectRequest(BaseModel):
    name: str
    category: str
    marketplace: str
    current_price: float
    condition: str