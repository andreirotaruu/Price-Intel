from pydantic import BaseModel

class AnalyzeRequest(BaseModel):
    name: str
    category: str
    current_price: float
    marketplace: str
    condition: str
