from pydantic import BaseModel

class AnalyzeRequest(BaseModel):
    name: str
    category: str
    
