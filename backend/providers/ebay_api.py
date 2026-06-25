import requests
import os

class EbayAPIProvider: 
    
    def search(self, query):

        token = os.getenv("EBAY_API_TOKEN")
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        params = {
            "q": query, 
            "limit": 20,
        }

        response = requests.get("https://api.ebay.com/buy/browse/v1/item_summary/search", params=params, headers=headers)

        return response.json()