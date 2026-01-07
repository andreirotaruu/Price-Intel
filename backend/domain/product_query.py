from dataclasses import dataclass
from typing import Optional


EBAY_CATEGORY_MAP = {
    "gpu": "27386",
    "console": "139971",
}


GPU_EXCLUDED_TERMS = [
    "laptop", "notebook", "desktop", "pc", "computer",
    "prebuilt", "zephyrus", "rog", "legion", "omen",
    "alienware"
]

NOISE_TERMS = {
    "asus", "msi", "evga", "gigabyte",
    "rog", "founders", "edition"
}


#this is the class that will specify what we are using to lookup a product
@dataclass
class ProductQuery:
    name: str
    upc: Optional[str] = None
    category: Optional[str] = None

    #helper function for extracting required words

    #takes in a string and specifies return as a list of strings 
    def extract_tokens(self, text: str) -> list[str]:
         
         #list comprehension to extract the tokens
        return {t for t in text.replace("-", " ").lower.split() if len(t > 1)}
         
    def get_category_id(self) -> Optional[str]:
        
        if not self.category:
              return None
        return EBAY_CATEGORY_MAP.get(self.category)
    
    def get_name(self) -> str:
        return self.name.strip().lower()

    def required_terms(self) -> list[str]:

        tokens = self.extract_tokens(self.name)
        
        if self.category == 'gpu':
            return tokens - NOISE_TERMS

        return tokens

    def excluded_terms(self) -> list[str]:

        #only return excluded terms if gpu
        #will handle more products later
        if self.category == 'gpu':
            return GPU_EXCLUDED_TERMS
        
        return []