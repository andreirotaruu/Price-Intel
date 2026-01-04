"""
This class is an interface that is setting the standard for a sell_provider
"""

from abc import ABC, abstractmethod
from typing import Dict

class SellPriceProvider(ABC):

    @abstractmethod
    def get_sell_metrics(self, upc: str) -> Dict:

        #returns resale metrics like median price and sold count
        pass