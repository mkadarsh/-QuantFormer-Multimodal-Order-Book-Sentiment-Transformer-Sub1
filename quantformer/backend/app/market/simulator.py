"""
Market simulator for generating realistic mock L2 order book data
"""
import logging
import random
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import math

from app.market.orderbook import OrderBook

logger = logging.getLogger(__name__)


class MarketSimulator:
    """Simulates high-frequency L2 order book data
    
    Generates realistic market conditions including:
    - Random walk price movements
    - Realistic spreads
    - Dynamic bid/ask volumes
    - Market scenarios (normal, sell pressure, liquidity drop, flash events)
    """
    
    def __init__(
        self,
        symbol: str,
        initial_price: float,
        num_levels: int = 5,
        base_spread_bps: float = 2.0,  # basis points
    ):
        """Initialize market simulator
        
        Args:
            symbol: Market symbol
            initial_price: Starting price
            num_levels: Number of order book levels
            base_spread_bps: Base spread in basis points
        """
        self.symbol = symbol
        self.current_price = initial_price
        self.num_levels = num_levels
        self.base_spread_bps = base_spread_bps
        
        self.timestamp = datetime.utcnow()
        self.order_book = OrderBook(symbol, num_levels)
        
        # Price history for volatility
        self.price_history = [initial_price]
        
        # Market scenario state
        self.scenario = "normal"  # normal, sell_pressure, buy_pressure, liquidity_drop, flash_event
        self.scenario_counter = 0
        self.scenario_duration = 0
        
        # Base volumes (will vary)
        self.base_bid_volume = 1000
        self.base_ask_volume = 1000
        
        logger.info(f"Initialized MarketSimulator for {symbol} at price {initial_price}")
    
    def generate_tick(self) -> Dict:
        """Generate a new market tick
        
        Returns:
            Dictionary with market data
        """
        # Update timestamp
        self.timestamp = datetime.utcnow()
        
        # Apply price movement
        self._apply_price_movement()
        
        # Update market scenario
        self._update_scenario()
        
        # Generate order book
        self._generate_orderbook()
        
        return {
            "symbol": self.symbol,
            "timestamp": self.timestamp,
            "last_price": self.current_price,
            "bid_price": self.order_book.get_best_bid(),
            "ask_price": self.order_book.get_best_ask(),
            "bids": [
                {"price": level.price, "volume": level.volume}
                for level in self.order_book.bids
            ],
            "asks": [
                {"price": level.price, "volume": level.volume}
                for level in self.order_book.asks
            ],
        }
    
    def _apply_price_movement(self):
        """Apply realistic price movement using random walk"""
        # Random walk with mean reversion
        # Approximate returns: ~0.1% volatility per tick
        
        volatility = 0.001  # 0.1% per tick
        drift = 0.0  # No long-term drift
        
        # Random shock
        shock = random.gauss(0, 1)  # Normal distribution
        
        # Apply movement
        log_return = drift + volatility * shock
        price_change = self.current_price * log_return
        
        new_price = self.current_price + price_change
        
        # Prevent price going negative
        if new_price > 0:
            self.current_price = new_price
            self.price_history.append(new_price)
            
            # Keep history bounded
            if len(self.price_history) > 1000:
                self.price_history.pop(0)
    
    def _update_scenario(self):
        """Update market scenario state"""
        self.scenario_counter += 1
        
        # Change scenario occasionally
        if self.scenario_counter >= self.scenario_duration or self.scenario_duration == 0:
            self.scenario = self._select_scenario()
            # Scenario duration: 10-50 ticks
            self.scenario_duration = random.randint(10, 50)
            self.scenario_counter = 0
            
            if self.scenario != "normal":
                logger.info(f"Market scenario changed to: {self.scenario}")
    
    def _select_scenario(self) -> str:
        """Select next market scenario based on probabilities"""
        # Probabilities: mostly normal, occasional stress
        probabilities = {
            "normal": 0.75,
            "sell_pressure": 0.10,
            "buy_pressure": 0.08,
            "liquidity_drop": 0.05,
            "flash_event": 0.02,
        }
        
        scenarios = list(probabilities.keys())
        probs = list(probabilities.values())
        
        return random.choices(scenarios, weights=probs, k=1)[0]
    
    def _generate_orderbook(self):
        """Generate realistic order book based on current scenario"""
        spread = self._calculate_spread()
        best_bid = self.current_price - (spread / 2)
        best_ask = self.current_price + (spread / 2)
        
        # Generate bid and ask levels
        bids = self._generate_bid_levels(best_bid)
        asks = self._generate_ask_levels(best_ask)
        
        self.order_book.update(bids, asks)
    
    def _calculate_spread(self) -> float:
        """Calculate bid-ask spread based on scenario"""
        base_spread = self.current_price * (self.base_spread_bps / 10000)
        
        # Apply scenario modifiers
        if self.scenario == "normal":
            spread_multiplier = 1.0
        elif self.scenario == "sell_pressure":
            spread_multiplier = 1.5
        elif self.scenario == "buy_pressure":
            spread_multiplier = 1.2
        elif self.scenario == "liquidity_drop":
            spread_multiplier = 3.0
        elif self.scenario == "flash_event":
            spread_multiplier = 5.0
        else:
            spread_multiplier = 1.0
        
        spread = base_spread * spread_multiplier
        
        # Add some randomness
        spread += base_spread * random.uniform(-0.2, 0.5)
        
        return max(spread, base_spread * 0.5)  # Ensure minimum spread
    
    def _generate_bid_levels(self, best_bid: float) -> List[Tuple[float, float]]:
        """Generate bid levels (highest price first)
        
        Args:
            best_bid: Best bid price
            
        Returns:
            List of (price, volume) tuples, sorted descending
        """
        bids = []
        tick_size = 0.05  # $0.05 per level
        
        for level in range(self.num_levels):
            price = best_bid - (level * tick_size)
            volume = self._generate_volume("bid")
            bids.append((price, volume))
        
        return bids
    
    def _generate_ask_levels(self, best_ask: float) -> List[Tuple[float, float]]:
        """Generate ask levels (lowest price first)
        
        Args:
            best_ask: Best ask price
            
        Returns:
            List of (price, volume) tuples, sorted ascending
        """
        asks = []
        tick_size = 0.05  # $0.05 per level
        
        for level in range(self.num_levels):
            price = best_ask + (level * tick_size)
            volume = self._generate_volume("ask")
            asks.append((price, volume))
        
        return asks
    
    def _generate_volume(self, side: str) -> float:
        """Generate realistic bid/ask volume
        
        Args:
            side: "bid" or "ask"
            
        Returns:
            Volume at this level
        """
        # Base volume with randomness
        base = self.base_bid_volume if side == "bid" else self.base_ask_volume
        
        # Apply scenario modifiers
        if self.scenario == "normal":
            volume = base * random.uniform(0.7, 1.3)
        elif self.scenario == "sell_pressure":
            # Increase ask volume, decrease bid volume
            if side == "ask":
                volume = base * random.uniform(1.5, 2.5)
            else:
                volume = base * random.uniform(0.3, 0.7)
        elif self.scenario == "buy_pressure":
            # Increase bid volume
            if side == "bid":
                volume = base * random.uniform(1.5, 2.5)
            else:
                volume = base * random.uniform(0.7, 1.3)
        elif self.scenario == "liquidity_drop":
            # Dramatically reduce both
            volume = base * random.uniform(0.1, 0.3)
        elif self.scenario == "flash_event":
            # Extreme imbalance
            if side == "ask":
                volume = base * random.uniform(3.0, 5.0)
            else:
                volume = base * random.uniform(0.05, 0.15)
        else:
            volume = base * random.uniform(0.7, 1.3)
        
        return max(volume, 10)  # Minimum volume
    
    def create_market_event(self, event_type: str):
        """Manually create a market event
        
        Args:
            event_type: Type of event (sell_pressure, flash_event, etc.)
        """
        self.scenario = event_type
        self.scenario_counter = 0
        self.scenario_duration = 50
        logger.info(f"Created market event: {event_type}")
