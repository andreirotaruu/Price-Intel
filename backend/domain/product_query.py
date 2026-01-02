from dataclasses import dataclass
from typing import Optional

@dataclass
class ProductQuery:
    name: str
    upc: Optional[str] = None
    category: Optional[str] = None
