"""
Order book feature engineering
"""
import logging
from typing import Dict, List, Optional
import numpy as np

logger = logging.getLogger(__name__)


class OrderBookFeatureCalculator:
    """Calculates features from L2 order book data
    
    All features are designed for multimodal time-series forecasting.
    """
    
    def __init__(self, window_size: int = 20):
        """Initialize feature calculator
        
        Args:
            window_size: Window size for rolling calculations
        """
        self.window_size = window_size
        self.price_history: List[float] = []
        self.feature_history: List[Dict[str, float]] = []
    
    def calculate_mid_price(self, best_bid: float, best_ask: float) -> float:
        """Calculate mid price from order book
        
        Args:
            best_bid: Best bid price
            best_ask: Best ask price
            
        Returns:
            Mid price (average of bid and ask)
        """
        if best_bid is None or best_ask is None:
            return None
        
        return (best_bid + best_ask) / 2.0
    
    def calculate_spread(self, best_bid: float, best_ask: float) -> float:
        """Calculate bid-ask spread
        
        Args:
            best_bid: Best bid price
            best_ask: Best ask price
            
        Returns:
            Spread (ask - bid)
        """
        if best_bid is None or best_ask is None:
            return None
        
        spread = best_ask - best_bid
        
        if spread < 0:
            logger.warning(f"Negative spread: {spread}")
            return 0.0
        
        return spread
    
    def calculate_spread_bps(self, best_bid: float, best_ask: float, mid_price: float) -> float:
        """Calculate spread in basis points
        
        Args:
            best_bid: Best bid price
            best_ask: Best ask price
            mid_price: Mid price
            
        Returns:
            Spread in basis points (bps)
        """
        if mid_price is None or mid_price == 0:
            return 0.0
        
        spread = self.calculate_spread(best_bid, best_ask)
        if spread is None:
            return 0.0
        
        return (spread / mid_price) * 100000
    
    def calculate_order_book_imbalance(self, bid_volume: float, ask_volume: float) -> float:
        """Calculate order book imbalance
        
        imbalance = (bid_volume - ask_volume) / (bid_volume + ask_volume)
        Range: [-1, 1]
        
        Args:
            bid_volume: Total bid-side volume
            ask_volume: Total ask-side volume
            
        Returns:
            Imbalance in range [-1, 1]
        """
        total_volume = bid_volume + ask_volume
        
        # Handle division by zero
        if total_volume == 0:
            logger.warning("Zero total volume in imbalance calculation")
            return 0.0
        
        imbalance = (bid_volume - ask_volume) / total_volume
        
        # Clamp to [-1, 1]
        return max(-1.0, min(1.0, imbalance))
    
    def calculate_bid_ask_volume_ratio(self, bid_volume: float, ask_volume: float) -> float:
        """Calculate bid/ask volume ratio
        
        Args:
            bid_volume: Total bid-side volume
            ask_volume: Total ask-side volume
            
        Returns:
            Ratio of bid to ask volume
        """
        if ask_volume == 0:
            logger.warning("Zero ask volume in ratio calculation")
            return 0.0 if bid_volume == 0 else float('inf')
        
        return bid_volume / ask_volume
    
    def calculate_liquidity_score(self, bid_volume: float, ask_volume: float, spread: float, mid_price: float) -> float:
        """Calculate liquidity score based on depth and spread
        
        Higher score = more liquid
        
        Args:
            bid_volume: Total bid-side volume
            ask_volume: Total ask-side volume
            spread: Bid-ask spread
            mid_price: Mid price
            
        Returns:
            Liquidity score (0-100 range, normalized)
        """
        if mid_price is None or mid_price == 0:
            return 0.0
        
        # Volume component (normalized)
        # Assume 50k is "high" liquidity
        total_volume = bid_volume + ask_volume
        volume_score = min(total_volume / 50000, 1.0)
        
        # Spread component (lower is better)
        # Assume 0.01 spread is "tight"
        spread_bps = (spread / mid_price) * 10000
        spread_score = max(1.0 - (spread_bps / 100), 0.0)  # Normalize by 100 bps
        
        # Combined score
        liquidity = (volume_score * 0.6 + spread_score * 0.4) * 100
        
        return max(0.0, min(100.0, liquidity))
    
    def calculate_price_change(self, current_price: float, previous_price: Optional[float] = None) -> float:
        """Calculate price change from previous observation
        
        Args:
            current_price: Current price
            previous_price: Previous price (uses history if None)
            
        Returns:
            Absolute price change
        """
        if previous_price is None:
            if len(self.price_history) < 2:
                return 0.0
            previous_price = self.price_history[-2]
        
        return current_price - previous_price
    
    def calculate_price_change_pct(self, current_price: float, previous_price: Optional[float] = None) -> float:
        """Calculate percentage price change
        
        Args:
            current_price: Current price
            previous_price: Previous price (uses history if None)
            
        Returns:
            Percentage change (0.01 = 1%)
        """
        if previous_price is None:
            if len(self.price_history) < 2:
                return 0.0
            previous_price = self.price_history[-2]
        
        if previous_price == 0:
            logger.warning("Zero previous price in pct change calculation")
            return 0.0
        
        return (current_price - previous_price) / previous_price
    
    def calculate_rolling_volatility(self, current_price: float, window: Optional[int] = None) -> float:
        """Calculate rolling volatility from price history
        
        Uses standard deviation of returns over a rolling window
        
        Args:
            current_price: Current price (added to history)
            window: Window size (uses default if None)
            
        Returns:
            Rolling volatility (std dev of log returns)
        """
        self.price_history.append(current_price)
        
        # Keep history bounded
        if len(self.price_history) > 1000:
            self.price_history.pop(0)
        
        if window is None:
            window = self.window_size
        
        # Need at least 2 prices to calculate returns
        if len(self.price_history) < max(2, window):
            return 0.0
        
        # Get recent prices
        recent_prices = self.price_history[-window:]
        
        # Calculate log returns
        log_returns = []
        for i in range(1, len(recent_prices)):
            if recent_prices[i-1] > 0:
                log_return = np.log(recent_prices[i] / recent_prices[i-1])
                log_returns.append(log_return)
        
        if len(log_returns) == 0:
            return 0.0
        
        # Return standard deviation of returns
        volatility = np.std(log_returns)
        
        return float(volatility)
    
    def get_all_features(self, orderbook_data: Dict) -> Dict[str, float]:
        """Calculate all features from order book data
        
        Args:
            orderbook_data: Order book dictionary with keys:
                - last_price
                - bid_price
                - ask_price
                - bids (list of dicts with price, volume)
                - asks (list of dicts with price, volume)
        
        Returns:
            Dictionary of all calculated features
        """
        # Extract data
        last_price = orderbook_data.get("last_price", 0)
        bid_price = orderbook_data.get("bid_price", 0)
        ask_price = orderbook_data.get("ask_price", 0)
        bids = orderbook_data.get("bids", [])
        asks = orderbook_data.get("asks", [])
        
        # Calculate bid/ask volumes
        bid_volume = sum(level.get("volume", 0) for level in bids)
        ask_volume = sum(level.get("volume", 0) for level in asks)
        
        # Calculate features
        mid_price = self.calculate_mid_price(bid_price, ask_price)
        spread = self.calculate_spread(bid_price, ask_price)
        spread_bps = self.calculate_spread_bps(bid_price, ask_price, mid_price) if mid_price else 0.0
        imbalance = self.calculate_order_book_imbalance(bid_volume, ask_volume)
        volume_ratio = self.calculate_bid_ask_volume_ratio(bid_volume, ask_volume)
        liquidity = self.calculate_liquidity_score(bid_volume, ask_volume, spread or 0, mid_price or 0)
        price_change = self.calculate_price_change(last_price)
        price_change_pct = self.calculate_price_change_pct(last_price)
        volatility = self.calculate_rolling_volatility(last_price)
        
        features = {
            "mid_price": mid_price or last_price,
            "spread": spread or 0.0,
            "spread_bps": spread_bps,
            "total_bid_volume": bid_volume,
            "total_ask_volume": ask_volume,
            "order_book_imbalance": imbalance,
            "bid_ask_volume_ratio": volume_ratio,
            "price_change": price_change,
            "price_change_pct": price_change_pct,
            "rolling_volatility": volatility,
            "liquidity_score": liquidity,
        }
        
        # Store for reference
        self.feature_history.append(features)
        if len(self.feature_history) > 1000:
            self.feature_history.pop(0)
        
        return features
