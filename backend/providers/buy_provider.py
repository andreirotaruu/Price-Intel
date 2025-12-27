from abc import ABC, abstractmethod

class BuyPriceProvider(ABC):

    @abstractmethod
    def get_buy_price(self, upc: str) -> float:
        pass


    


