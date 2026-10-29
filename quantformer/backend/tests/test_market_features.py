"""
Tests for order book feature calculations
"""
import pytest
from app.market.features import OrderBookFeatureCalculator


class TestOrderBookFeatureCalculator:
    """Test OrderBookFeatureCalculator implementation"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.calculator = OrderBookFeatureCalculator(window_size=10)
    
    def test_mid_price(self):
        """Test mid price calculation"""
        mid = self.calculator.calculate_mid_price(100.00, 100.10)
        assert mid == pytest.approx(100.05, rel=0.001)
    
    def test_mid_price_none_handling(self):
        """Test mid price with None values"""
        assert self.calculator.calculate_mid_price(None, 100.10) is None
        assert self.calculator.calculate_mid_price(100.00, None) is None
    
    def test_spread(self):
        """Test spread calculation"""
        spread = self.calculator.calculate_spread(100.00, 100.10)
        assert spread == pytest.approx(0.10, rel=0.001)
    
    def test_spread_negative(self):
        """Test spread with negative value (invalid book)"""
        spread = self.calculator.calculate_spread(100.10, 100.00)
        assert spread == pytest.approx(0.0, rel=0.001)
    
    def test_spread_bps(self):
        """Test spread in basis points"""
        spread_bps = self.calculator.calculate_spread_bps(100.00, 100.10, 100.05)
        # spread_bps = (0.10 / 100.05) * 10000 ~= 99.95 bps
        assert spread_bps == pytest.approx(99.95, rel=0.01)
    
    def test_order_book_imbalance_balanced(self):
        """Test imbalance with balanced volumes"""
        imbalance = self.calculator.calculate_order_book_imbalance(1000, 1000)
        assert imbalance == pytest.approx(0.0, abs=0.001)
    
    def test_order_book_imbalance_positive(self):
        """Test imbalance with more bid volume"""
        imbalance = self.calculator.calculate_order_book_imbalance(2000, 1000)
        # imbalance = (2000 - 1000) / 3000 = 1/3
        assert imbalance == pytest.approx(1/3, rel=0.01)
    
    def test_order_book_imbalance_negative(self):
        """Test imbalance with more ask volume"""
        imbalance = self.calculator.calculate_order_book_imbalance(1000, 2000)
        # imbalance = (1000 - 2000) / 3000 = -1/3
        assert imbalance == pytest.approx(-1/3, rel=0.01)
    
    def test_order_book_imbalance_range(self):
        """Test that imbalance is in valid range [-1, 1]"""
        # Extreme case: all bid volume
        imbalance1 = self.calculator.calculate_order_book_imbalance(10000, 0.001)
        assert -1.0 <= imbalance1 <= 1.0
        
        # Extreme case: all ask volume
        imbalance2 = self.calculator.calculate_order_book_imbalance(0.001, 10000)
        assert -1.0 <= imbalance2 <= 1.0
    
    def test_order_book_imbalance_zero_volume(self):
        """Test imbalance with zero volume"""
        imbalance = self.calculator.calculate_order_book_imbalance(0, 0)
        assert imbalance == pytest.approx(0.0, abs=0.001)
    
    def test_bid_ask_volume_ratio(self):
        """Test bid/ask volume ratio"""
        ratio = self.calculator.calculate_bid_ask_volume_ratio(2000, 1000)
        assert ratio == pytest.approx(2.0, rel=0.001)
    
    def test_bid_ask_volume_ratio_zero_ask(self):
        """Test ratio with zero ask volume"""
        ratio = self.calculator.calculate_bid_ask_volume_ratio(1000, 0)
        assert ratio == float('inf')
    
    def test_liquidity_score(self):
        """Test liquidity score calculation"""
        # High volume, tight spread
        score1 = self.calculator.calculate_liquidity_score(
            bid_volume=25000,
            ask_volume=25000,
            spread=0.01,
            mid_price=100.00
        )
        assert 0 <= score1 <= 100
        
        # Low volume, wide spread
        score2 = self.calculator.calculate_liquidity_score(
            bid_volume=500,
            ask_volume=500,
            spread=1.00,
            mid_price=100.00
        )
        assert 0 <= score2 <= 100
        
        # Score should be higher for better liquidity
        assert score1 > score2
    
    def test_price_change(self):
        """Test price change calculation"""
        change = self.calculator.calculate_price_change(101.00, 100.00)
        assert change == pytest.approx(1.00, rel=0.001)
    
    def test_price_change_pct(self):
        """Test percentage price change"""
        pct_change = self.calculator.calculate_price_change_pct(105.00, 100.00)
        # (105 - 100) / 100 = 0.05 = 5%
        assert pct_change == pytest.approx(0.05, rel=0.001)
    
    def test_rolling_volatility(self):
        """Test rolling volatility calculation"""
        # Add prices
        prices = [100.0, 100.5, 99.8, 100.2, 101.0]
        
        for price in prices:
            vol = self.calculator.calculate_rolling_volatility(price)
        
        # Should have some volatility
        assert vol >= 0
    
    def test_get_all_features(self):
        """Test complete feature calculation"""
        orderbook_data = {
            "last_price": 100.50,
            "bid_price": 100.00,
            "ask_price": 100.10,
            "bids": [
                {"price": 100.00, "volume": 1000},
                {"price": 99.95, "volume": 800},
            ],
            "asks": [
                {"price": 100.10, "volume": 1200},
                {"price": 100.15, "volume": 900},
            ],
        }
        
        features = self.calculator.get_all_features(orderbook_data)
        
        # Check all expected keys exist
        expected_keys = [
            "mid_price",
            "spread",
            "spread_bps",
            "total_bid_volume",
            "total_ask_volume",
            "order_book_imbalance",
            "bid_ask_volume_ratio",
            "price_change",
            "price_change_pct",
            "rolling_volatility",
            "liquidity_score",
        ]
        
        for key in expected_keys:
            assert key in features
            assert isinstance(features[key], (int, float))
        
        # Check specific values
        assert features["total_bid_volume"] == 1800
        assert features["total_ask_volume"] == 2100
        assert features["mid_price"] == pytest.approx(100.05, rel=0.001)
