"""
Test consumer for market data topic

Subscribes to market-data topic and prints incoming messages.

Usage:
    python scripts/test_market_consumer.py
    python scripts/test_market_consumer.py --group test-consumer
    python scripts/test_market_consumer.py --auto-offset earliest
"""
import argparse
import sys
import logging
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.kafka.consumer import MarketDataConsumer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_consumer(
    group_id: str = "test-consumer",
    auto_offset_reset: str = "latest",
    max_messages: int = None,
):
    """Run test consumer
    
    Args:
        group_id: Consumer group ID
        auto_offset_reset: Where to start reading (earliest or latest)
        max_messages: Maximum messages to consume (None = infinite)
    """
    logger.info("=== MARKET DATA CONSUMER ===")
    logger.info(f"  Group ID: {group_id}")
    logger.info(f"  Auto-offset-reset: {auto_offset_reset}")
    logger.info(f"  Max messages: {max_messages or 'unlimited'}")
    logger.info("")
    
    try:
        consumer = MarketDataConsumer(
            group_id=group_id,
            auto_offset_reset=auto_offset_reset,
        )
        
        if not consumer.is_connected():
            logger.error("Failed to connect to Kafka")
            return
        
        logger.info("Connected to Kafka, listening for messages (Ctrl+C to exit)...")
        logger.info("")
        
        message_count = 0
        
        for message in consumer.consume_iter():
            if message is None:
                continue
            
            message_count += 1
            
            # Display message
            logger.info(f"Message #{message_count}:")
            logger.info(f"  Timestamp: {message.get('timestamp')}")
            logger.info(f"  Symbol: {message.get('symbol')}")
            logger.info(f"  Price: ${message.get('last_price'):.2f}")
            logger.info(f"  Bid: ${message.get('bid_price'):.2f} | "
                       f"Ask: ${message.get('ask_price'):.2f}")
            
            # Display features if available
            features = message.get('features')
            if features:
                logger.info(f"  Mid Price: ${features.get('mid_price'):.2f}")
                logger.info(f"  Spread: ${features.get('spread'):.4f} "
                           f"({features.get('spread_bps'):.1f} bps)")
                logger.info(f"  Imbalance: {features.get('order_book_imbalance'):.3f}")
                logger.info(f"  Liquidity: {features.get('liquidity_score'):.1f}")
            
            logger.info("")
            
            # Check if we've hit the max
            if max_messages and message_count >= max_messages:
                logger.info(f"Reached max messages ({max_messages}), exiting")
                break
        
        logger.info(f"✓ Consumer closed after {message_count} messages")
        
    except KeyboardInterrupt:
        logger.info("Consumer interrupted by user")
    except Exception as e:
        logger.error(f"Consumer error: {e}", exc_info=True)
    finally:
        if 'consumer' in locals():
            consumer.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Test consumer for market data topic"
    )
    parser.add_argument(
        "--group",
        type=str,
        default="test-consumer",
        help="Consumer group ID (default: test-consumer)"
    )
    parser.add_argument(
        "--auto-offset",
        type=str,
        choices=["earliest", "latest"],
        default="latest",
        help="Starting offset (default: latest)"
    )
    parser.add_argument(
        "--max",
        type=int,
        default=None,
        help="Max messages to consume (default: unlimited)"
    )
    
    args = parser.parse_args()
    
    run_consumer(
        group_id=args.group,
        auto_offset_reset=args.auto_offset,
        max_messages=args.max,
    )
