"""
Tests for order book feature calculations
"""
import pytest
from app.market.orderbook import OrderBook, OrderBookLevel


class TestOrderBook:
    """Test OrderBook implementation"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.orderbook = OrderBook("DEMO", num_levels=5)
    
    def test_initialization(self):
        """Test order book initialization"""
        assert self.orderbook.symbol == "DEMO"
        assert self.orderbook.num_levels == 5
        assert self.orderbook.bids == []
        assert self.orderbook.asks == []
    
    def test_valid_update(self):
        """Test valid order book update"""
        bids = [(100.00, 1000), (99.95, 800), (99.90, 600)]
        asks = [(100.05, 1200), (100.10, 900), (100.15, 1100)]
        
        self.orderbook.update(bids, asks)
        
        assert len(self.orderbook.bids) == 3
        assert len(self.orderbook.asks) == 3
        assert self.orderbook.is_valid()
    
    def test_get_best_bid(self):
        """Test best bid extraction"""
        bids = [(100.00, 1000), (99.95, 800)]
        asks = [(100.05, 1200), (100.10, 900)]
        
        self.orderbook.update(bids, asks)
        
        assert self.orderbook.get_best_bid() == 100.00
    
    def test_get_best_ask(self):
        """Test best ask extraction"""
        bids = [(100.00, 1000), (99.95, 800)]
        asks = [(100.05, 1200), (100.10, 900)]
        
        self.orderbook.update(bids, asks)
        
        assert self.orderbook.get_best_ask() == 100.05
    
    def test_mid_price(self):
        """Test mid price calculation"""
        bids = [(100.00, 1000)]
        asks = [(100.10, 1000)]
        
        self.orderbook.update(bids, asks)
        
        mid = self.orderbook.get_mid_price()
        assert mid == pytest.approx(100.05, rel=0.001)
    
    def test_spread(self):
        """Test spread calculation"""
        bids = [(100.00, 1000)]
        asks = [(100.10, 1000)]
        
        self.orderbook.update(bids, asks)
        
        spread = self.orderbook.get_spread()
        assert spread == pytest.approx(0.10, rel=0.001)
    
    def test_total_bid_volume(self):
        """Test total bid volume calculation"""
        bids = [(100.00, 1000), (99.95, 800), (99.90, 600)]
        asks = [(100.05, 1200)]
        
        self.orderbook.update(bids, asks)
        
        total = self.orderbook.get_total_bid_volume()
        assert total == 2400
    
    def test_total_ask_volume(self):
        """Test total ask volume calculation"""
        bids = [(100.00, 1000)]
        asks = [(100.05, 1200), (100.10, 900), (100.15, 1100)]
        
        self.orderbook.update(bids, asks)
        
        total = self.orderbook.get_total_ask_volume()
        assert total == 3200
    
    def test_invalid_crossing(self):
        """Test invalid order book (bid >= ask)"""
        bids = [(100.10, 1000)]
        asks = [(100.05, 1000)]
        
        self.orderbook.update(bids, asks)
        
        # Should not update due to invalid crossing
        assert self.orderbook.bids == []
        assert self.orderbook.asks == []
    
    def test_empty_book(self):
        """Test empty order book handling"""
        assert self.orderbook.get_best_bid() is None
        assert self.orderbook.get_best_ask() is None
        assert self.orderbook.get_mid_price() is None
        assert self.orderbook.get_spread() is None
        assert not self.orderbook.is_valid()
    
    def test_num_levels_limit(self):
        """Test that only num_levels are kept"""
        bids = [(100.00 - i*0.05, 1000-i*100) for i in range(10)]
        asks = [(100.05 + i*0.05, 1200-i*100) for i in range(10)]
        
        self.orderbook.update(bids, asks)
        
        assert len(self.orderbook.bids) == 5
        assert len(self.orderbook.asks) == 5
    
    def test_to_dict(self):
        """Test conversion to dictionary"""
        bids = [(100.00, 1000)]
        asks = [(100.10, 1200)]
        
        self.orderbook.update(bids, asks)
        
        book_dict = self.orderbook.to_dict()
        
        assert book_dict["symbol"] == "DEMO"
        assert book_dict["best_bid"] == 100.00
        assert book_dict["best_ask"] == 100.10
        assert len(book_dict["bids"]) == 1
        assert len(book_dict["asks"]) == 1
