from dataclasses import dataclass
from typing import Optional

#this is the class that will specify what we are using to lookup a product
@dataclass
class ProductQuery:
    name: str
    upc: Optional[str] = None
    category: Optional[str] = None
