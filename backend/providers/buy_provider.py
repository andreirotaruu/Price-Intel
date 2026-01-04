"""
This is the interface that sets the standard for the buy price provider
"""

from abc import ABC, abstractmethod

class BuyPriceProvider(ABC):

    @abstractmethod
    def get_buy_price(self, upc: str) -> float:
        pass


    


