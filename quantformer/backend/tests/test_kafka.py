"""
Tests for Kafka producer and consumer
"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from app.kafka.producer import KafkaProducerService
from app.kafka.consumer import KafkaConsumerService, MarketDataConsumer
from app.kafka.topics import get_topic, get_all_topics, TOPICS


class TestKafkaTopics:
    """Test Kafka topic configuration"""
    
    def test_get_topic(self):
        """Test getting topic by key"""
        assert get_topic("market_data") == TOPICS["market_data"]
        assert get_topic("news_data") == TOPICS["news_data"]
    
    def test_get_all_topics(self):
        """Test getting all topics"""
        topics = get_all_topics()
        assert len(topics) > 0
        assert "market-data" in topics


class TestKafkaProducer:
    """Test KafkaProducerService"""
    
    def test_initialization(self):
        """Test producer initialization"""
        with patch('app.kafka.producer.KafkaProducer'):
            producer = KafkaProducerService(
                bootstrap_servers="localhost:9092",
                client_id="test-producer"
            )
            assert producer.bootstrap_servers == "localhost:9092"
            assert producer.client_id == "test-producer"
    
    def test_serialize_json(self):
        """Test JSON serialization"""
        data = {"symbol": "DEMO", "price": 100.50}
        serialized = KafkaProducerService._serialize_json(data)
        
        assert isinstance(serialized, bytes)
        deserialized = json.loads(serialized.decode('utf-8'))
        assert deserialized == data
    
    def test_serialize_json_with_datetime(self):
        """Test JSON serialization with datetime"""
        from datetime import datetime
        
        data = {"timestamp": datetime(2024, 1, 1, 12, 0, 0)}
        serialized = KafkaProducerService._serialize_json(data)
        
        assert isinstance(serialized, bytes)
        # Should not raise an error
    
    def test_serialize_json_invalid(self):
        """Test JSON serialization with invalid data"""
        with pytest.raises(ValueError):
            # This should raise an error for circular reference
            data = {}
            data['self'] = data
            KafkaProducerService._serialize_json(data)
    
    @patch('app.kafka.producer.KafkaProducer')
    def test_is_connected(self, mock_kafka):
        """Test connection status check"""
        producer = KafkaProducerService(
            bootstrap_servers="localhost:9092"
        )
        
        # Should be connected after init (mocked)
        assert producer.is_connected()
        
        # Test disconnected state
        producer.producer = None
        assert not producer.is_connected()


class TestKafkaConsumer:
    """Test KafkaConsumerService"""
    
    def test_initialization(self):
        """Test consumer initialization"""
        with patch('app.kafka.consumer.KafkaConsumer'):
            consumer = KafkaConsumerService(
                topics=["market-data"],
                bootstrap_servers="localhost:9092",
                group_id="test-group"
            )
            assert consumer.topics == ["market-data"]
            assert consumer.group_id == "test-group"
    
    def test_deserialize_json(self):
        """Test JSON deserialization"""
        data = {"symbol": "DEMO", "price": 100.50}
        json_bytes = json.dumps(data).encode('utf-8')
        
        deserialized = KafkaConsumerService._deserialize_json(json_bytes)
        assert deserialized == data
    
    def test_deserialize_json_none(self):
        """Test JSON deserialization with None"""
        result = KafkaConsumerService._deserialize_json(None)
        assert result is None
    
    def test_deserialize_json_invalid(self):
        """Test JSON deserialization with invalid data"""
        with pytest.raises(ValueError):
            KafkaConsumerService._deserialize_json(b"invalid json")


class TestMarketDataConsumer:
    """Test MarketDataConsumer specialization"""
    
    def test_initialization(self):
        """Test market data consumer initialization"""
        with patch('app.kafka.consumer.KafkaConsumer'):
            consumer = MarketDataConsumer(
                group_id="market-processor"
            )
            
            assert consumer.group_id == "market-processor"
            assert get_topic("market_data") in consumer.topics


class TestKafkaIntegration:
    """Integration tests for producer and consumer"""
    
    def test_context_manager_producer(self):
        """Test producer context manager"""
        with patch('app.kafka.producer.KafkaProducer'):
            with KafkaProducerService() as producer:
                assert producer is not None
    
    def test_context_manager_consumer(self):
        """Test consumer context manager"""
        with patch('app.kafka.consumer.KafkaConsumer'):
            with KafkaConsumerService(topics=["test"]) as consumer:
                assert consumer is not None


class TestDataModels:
    """Test data serialization/deserialization with realistic models"""
    
    def test_market_tick_serialization(self):
        """Test market tick data serialization"""
        market_tick = {
            "symbol": "DEMO",
            "timestamp": "2024-01-01T10:00:00",
            "last_price": 500.25,
            "bid_price": 500.20,
            "ask_price": 500.30,
            "bids": [
                {"price": 500.20, "volume": 1000},
                {"price": 500.15, "volume": 800},
            ],
            "asks": [
                {"price": 500.30, "volume": 1200},
                {"price": 500.35, "volume": 900},
            ],
            "features": {
                "mid_price": 500.25,
                "spread": 0.10,
                "order_book_imbalance": 0.05,
            }
        }
        
        # Serialize
        serialized = KafkaProducerService._serialize_json(market_tick)
        assert isinstance(serialized, bytes)
        
        # Deserialize
        deserialized = KafkaConsumerService._deserialize_json(serialized)
        assert deserialized == market_tick
    
    def test_nested_data_serialization(self):
        """Test deeply nested data serialization"""
        complex_data = {
            "level1": {
                "level2": {
                    "level3": {
                        "values": [1, 2, 3],
                        "nested": {"key": "value"}
                    }
                }
            }
        }
        
        serialized = KafkaProducerService._serialize_json(complex_data)
        deserialized = KafkaConsumerService._deserialize_json(serialized)
        assert deserialized == complex_data
