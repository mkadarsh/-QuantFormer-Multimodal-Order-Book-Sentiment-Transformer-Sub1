"""
Tests for market simulator
"""
import pytest
from datetime import datetime
from app.market.simulator import MarketSimulator


class TestMarketSimulator:
    """Test MarketSimulator implementation"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.simulator = MarketSimulator(
            symbol="DEMO",
            initial_price=500.00,
            num_levels=5,
        )
    
    def test_initialization(self):
        """Test simulator initialization"""
        assert self.simulator.symbol == "DEMO"
        assert self.simulator.current_price == 500.00
        assert self.simulator.num_levels == 5
        assert len(self.simulator.price_history) == 1
    
    def test_generate_tick(self):
        """Test tick generation"""
        tick = self.simulator.generate_tick()
        
        # Check required fields
        assert "symbol" in tick
        assert "timestamp" in tick
        assert "last_price" in tick
        assert "bid_price" in tick
        assert "ask_price" in tick
        assert "bids" in tick
        assert "asks" in tick
        
        assert tick["symbol"] == "DEMO"
        assert isinstance(tick["timestamp"], datetime)
        assert tick["last_price"] > 0
        assert tick["bid_price"] > 0
        assert tick["ask_price"] > 0
    
    def test_price_movement(self):
        """Test that price changes over time"""
        initial_price = self.simulator.current_price
        
        # Generate multiple ticks
        prices = []
        for _ in range(100):
            tick = self.simulator.generate_tick()
            prices.append(tick["last_price"])
        
        # Price should have changed
        assert len(set(prices)) > 1  # Not all prices are identical
        
        # Price shouldn't drift too far (random walk, not trending)
        final_price = prices[-1]
        price_change_pct = abs(final_price - initial_price) / initial_price
        assert price_change_pct < 0.1  # Less than 10% change in 100 ticks
    
    def test_bid_ask_crossing(self):
        """Test that bid < ask is always maintained"""
        for _ in range(50):
            tick = self.simulator.generate_tick()
            
            bid = tick["bid_price"]
            ask = tick["ask_price"]
            
            assert bid < ask, f"Bid ({bid}) should be < Ask ({ask})"
    
    def test_orderbook_levels(self):
        """Test correct number of order book levels"""
        tick = self.simulator.generate_tick()
        
        assert len(tick["bids"]) == 5
        assert len(tick["asks"]) == 5
    
    def test_bid_prices_descending(self):
        """Test that bid prices are in descending order"""
        tick = self.simulator.generate_tick()
        
        bids = [b["price"] for b in tick["bids"]]
        
        for i in range(len(bids) - 1):
            assert bids[i] > bids[i+1], "Bids should be in descending order"
    
    def test_ask_prices_ascending(self):
        """Test that ask prices are in ascending order"""
        tick = self.simulator.generate_tick()
        
        asks = [a["price"] for a in tick["asks"]]
        
        for i in range(len(asks) - 1):
            assert asks[i] < asks[i+1], "Asks should be in ascending order"
    
    def test_volumes_positive(self):
        """Test that all volumes are positive"""
        for _ in range(20):
            tick = self.simulator.generate_tick()
            
            for bid in tick["bids"]:
                assert bid["volume"] > 0
            
            for ask in tick["asks"]:
                assert ask["volume"] > 0
    
    def test_market_scenarios(self):
        """Test different market scenarios"""
        scenarios_seen = set()
        
        for _ in range(500):
            tick = self.simulator.generate_tick()
            scenarios_seen.add(self.simulator.scenario)
        
        # Should see at least some variety in scenarios
        assert len(scenarios_seen) > 1
    
    def test_scenario_normal(self):
        """Test normal scenario generates balanced book"""
        self.simulator.scenario = "normal"
        self.simulator.scenario_duration = 1000
        
        tick = self.simulator.generate_tick()
        
        total_bid = sum(b["volume"] for b in tick["bids"])
        total_ask = sum(a["volume"] for a in tick["asks"])
        
        # Volumes should be relatively balanced
        ratio = max(total_bid, total_ask) / min(total_bid, total_ask)
        assert ratio < 2.0, "Normal scenario should have relatively balanced volumes"
    
    def test_scenario_sell_pressure(self):
        """Test sell pressure increases ask volume"""
        self.simulator.scenario = "sell_pressure"
        self.simulator.scenario_duration = 100
        
        tick = self.simulator.generate_tick()
        
        total_bid = sum(b["volume"] for b in tick["bids"])
        total_ask = sum(a["volume"] for a in tick["asks"])
        
        # Ask volume should be higher than bid
        assert total_ask > total_bid
    
    def test_scenario_buy_pressure(self):
        """Test buy pressure increases bid volume"""
        self.simulator.scenario = "buy_pressure"
        self.simulator.scenario_duration = 100
        
        tick = self.simulator.generate_tick()
        
        total_bid = sum(b["volume"] for b in tick["bids"])
        total_ask = sum(a["volume"] for a in tick["asks"])
        
        # Bid volume should be higher than ask
        assert total_bid > total_ask
    
    def test_scenario_liquidity_drop(self):
        """Test liquidity drop reduces volumes"""
        # Generate normal tick
        self.simulator.scenario = "normal"
        self.simulator.scenario_duration = 10
        for _ in range(10):
            tick_normal = self.simulator.generate_tick()
        
        normal_volume = (
            sum(b["volume"] for b in tick_normal["bids"]) +
            sum(a["volume"] for a in tick_normal["asks"])
        )
        
        # Generate liquidity drop tick
        self.simulator.scenario = "liquidity_drop"
        self.simulator.scenario_duration = 100
        for _ in range(10):
            tick_drop = self.simulator.generate_tick()
        
        drop_volume = (
            sum(b["volume"] for b in tick_drop["bids"]) +
            sum(a["volume"] for a in tick_drop["asks"])
        )
        
        # Liquidity drop should reduce volume
        assert drop_volume < normal_volume * 0.5
    
    def test_create_market_event(self):
        """Test manual market event creation"""
        self.simulator.create_market_event("flash_event")
        
        assert self.simulator.scenario == "flash_event"
        assert self.simulator.scenario_counter == 0
        assert self.simulator.scenario_duration == 50
