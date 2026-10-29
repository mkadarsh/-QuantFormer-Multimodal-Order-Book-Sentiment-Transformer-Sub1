"""
Generate mock market data for training and testing
"""
import argparse
import csv
import sys
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.market.simulator import MarketSimulator
from app.market.features import OrderBookFeatureCalculator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_market_data(
    output_path: str,
    symbol: str = "DEMO",
    initial_price: float = 500.25,
    duration_seconds: int = 86400,
    interval_ms: int = 100,
    num_levels: int = 5,
):
    """Generate mock L2 order book data to CSV
    
    Args:
        output_path: Output CSV file path
        symbol: Market symbol
        initial_price: Starting price
        duration_seconds: Duration of simulation in seconds
        interval_ms: Update interval in milliseconds
        num_levels: Number of order book levels
    """
    logger.info(f"Generating market data")
    logger.info(f"  Symbol: {symbol}")
    logger.info(f"  Initial price: ${initial_price}")
    logger.info(f"  Duration: {duration_seconds}s ({duration_seconds/3600:.1f} hours)")
    logger.info(f"  Interval: {interval_ms}ms (~{1000/interval_ms:.0f} updates/sec)")
    logger.info(f"  Order book levels: {num_levels}")
    logger.info(f"  Output: {output_path}")
    
    # Create output directory if needed
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize simulator and calculator
    simulator = MarketSimulator(
        symbol=symbol,
        initial_price=initial_price,
        num_levels=num_levels,
    )
    calculator = OrderBookFeatureCalculator()
    
    # Calculate number of ticks
    num_ticks = int((duration_seconds * 1000) / interval_ms)
    logger.info(f"  Total ticks: {num_ticks:,}")
    
    # Open CSV for writing
    with open(output_path, 'w', newline='') as csvfile:
        fieldnames = [
            'timestamp',
            'symbol',
            'last_price',
            'bid_price',
            'ask_price',
            'mid_price',
            'spread',
            'spread_bps',
            'total_bid_volume',
            'total_ask_volume',
            'order_book_imbalance',
            'bid_ask_volume_ratio',
            'price_change',
            'price_change_pct',
            'rolling_volatility',
            'liquidity_score',
        ]
        
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        # Generate data
        for i in range(num_ticks):
            # Generate tick
            tick = simulator.generate_tick()
            
            # Calculate features
            features = calculator.get_all_features(tick)
            
            # Prepare row
            row = {
                'timestamp': tick['timestamp'].isoformat(),
                'symbol': tick['symbol'],
                'last_price': tick['last_price'],
                'bid_price': tick['bid_price'],
                'ask_price': tick['ask_price'],
                'mid_price': features['mid_price'],
                'spread': features['spread'],
                'spread_bps': features['spread_bps'],
                'total_bid_volume': features['total_bid_volume'],
                'total_ask_volume': features['total_ask_volume'],
                'order_book_imbalance': features['order_book_imbalance'],
                'bid_ask_volume_ratio': features['bid_ask_volume_ratio'],
                'price_change': features['price_change'],
                'price_change_pct': features['price_change_pct'],
                'rolling_volatility': features['rolling_volatility'],
                'liquidity_score': features['liquidity_score'],
            }
            
            writer.writerow(row)
            
            # Progress logging
            progress_interval = max(1, num_ticks // 10)
            if (i + 1) % progress_interval == 0 or i + 1 == num_ticks:
                progress = (i + 1) / num_ticks * 100
                logger.info(f"  Progress: {progress:.0f}% ({i+1:,}/{num_ticks:,} ticks)")
    
    logger.info(f"✓ Data generation complete: {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate mock L2 order book data for QuantFormer"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/market_data.csv",
        help="Output CSV file path (default: data/market_data.csv)"
    )
    parser.add_argument(
        "--symbol",
        type=str,
        default="DEMO",
        help="Market symbol (default: DEMO)"
    )
    parser.add_argument(
        "--initial-price",
        type=float,
        default=500.25,
        help="Starting price (default: 500.25)"
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=3600,
        help="Duration in seconds (default: 3600 = 1 hour)"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=100,
        help="Update interval in milliseconds (default: 100 = 10/sec)"
    )
    parser.add_argument(
        "--levels",
        type=int,
        default=5,
        help="Number of order book levels (default: 5)"
    )
    
    args = parser.parse_args()
    
    generate_market_data(
        output_path=args.output,
        symbol=args.symbol,
        initial_price=args.initial_price,
        duration_seconds=args.duration,
        interval_ms=args.interval,
        num_levels=args.levels,
    )
