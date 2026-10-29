"""
Order book data structure and operations
"""
import logging
from typing import List, Tuple, Optional
from dataclasses import dataclass
import heapq

logger = logging.getLogger(__name__)


@dataclass
class OrderBookLevel:
    """Single level in order book (bid or ask)"""
    price: float
    volume: float
    
    def __eq__(self, other):
        if not isinstance(other, OrderBookLevel):
            return False
        return self.price == other.price and self.volume == other.volume
    
    def __lt__(self, other):
        return self.price < other.price


class OrderBook:
    """L2 Order Book implementation
    
    Maintains bid and ask levels sorted by price.
    Bids: highest price first (descending)
    Asks: lowest price first (ascending)
    """
    
    def __init__(self, symbol: str, num_levels: int = 5):
        """Initialize order book
        
        Args:
            symbol: Market symbol (e.g., "DEMO")
            num_levels: Number of bid/ask levels to maintain
        """
        self.symbol = symbol
        self.num_levels = num_levels
        self.bids: List[OrderBookLevel] = []
        self.asks: List[OrderBookLevel] = []
        logger.debug(f"Initialized OrderBook for {symbol} with {num_levels} levels")
    
    def update(self, bids: List[Tuple[float, float]], asks: List[Tuple[float, float]]):
        """Update order book with new bids and asks
        
        Args:
            bids: List of (price, volume) tuples, highest price first
            asks: List of (price, volume) tuples, lowest price first
        """
        # Validate input
        if not bids or not asks:
            logger.warning("Empty bids or asks provided")
            return
        
        # Validate bid-ask crossing
        if bids[0][0] >= asks[0][0]:
            logger.warning(f"Invalid book: best_bid ({bids[0][0]}) >= best_ask ({asks[0][0]})")
            return
        
        # Keep only num_levels
        self.bids = [OrderBookLevel(price, volume) for price, volume in bids[:self.num_levels]]
        self.asks = [OrderBookLevel(price, volume) for price, volume in asks[:self.num_levels]]
    
    def get_best_bid(self) -> Optional[float]:
        """Get best bid price (highest bid)"""
        return self.bids[0].price if self.bids else None
    
    def get_best_ask(self) -> Optional[float]:
        """Get best ask price (lowest ask)"""
        return self.asks[0].price if self.asks else None
    
    def get_mid_price(self) -> Optional[float]:
        """Calculate mid price (average of best bid and ask)"""
        best_bid = self.get_best_bid()
        best_ask = self.get_best_ask()
        
        if best_bid is None or best_ask is None:
            return None
        
        return (best_bid + best_ask) / 2.0
    
    def get_spread(self) -> Optional[float]:
        """Calculate bid-ask spread"""
        best_bid = self.get_best_bid()
        best_ask = self.get_best_ask()
        
        if best_bid is None or best_ask is None:
            return None
        
        spread = best_ask - best_bid
        
        if spread < 0:
            logger.warning(f"Negative spread detected: {spread}")
            return None
        
        return spread
    
    def get_total_bid_volume(self) -> float:
        """Get total bid-side volume"""
        return sum(level.volume for level in self.bids)
    
    def get_total_ask_volume(self) -> float:
        """Get total ask-side volume"""
        return sum(level.volume for level in self.asks)
    
    def is_valid(self) -> bool:
        """Check if order book is in valid state"""
        if not self.bids or not self.asks:
            return False
        
        # Best bid must be strictly less than best ask
        return self.bids[0].price < self.asks[0].price
    
    def to_dict(self) -> dict:
        """Convert order book to dictionary"""
        return {
            "symbol": self.symbol,
            "bids": [{"price": level.price, "volume": level.volume} for level in self.bids],
            "asks": [{"price": level.price, "volume": level.volume} for level in self.asks],
            "best_bid": self.get_best_bid(),
            "best_ask": self.get_best_ask(),
            "spread": self.get_spread(),
            "mid_price": self.get_mid_price(),
            "bid_volume_total": self.get_total_bid_volume(),
            "ask_volume_total": self.get_total_ask_volume(),
        }
