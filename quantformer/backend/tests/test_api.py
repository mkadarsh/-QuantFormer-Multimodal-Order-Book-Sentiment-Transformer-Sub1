from fastapi.testclient import TestClient

from app.main import app


def test_health_and_prediction_endpoints():
    with TestClient(app) as client:
        assert client.get("/api/health").status_code == 200
        prediction = client.get("/api/prediction/latest")
        assert prediction.status_code == 200
        assert "risk_level" in prediction.json()


def test_explanation_endpoint_contract():
    with TestClient(app) as client:
        response = client.get("/api/explanation")
        assert response.status_code == 200
        body = response.json()
        assert body["label"] == "Signal Contribution Estimate"
        assert "prediction" in body
        assert "risk_level" in body
        assert "feature_contributions" in body
        assert "human_readable_explanation" in body


def test_websocket_snapshot():
    with TestClient(app) as client:
        with client.websocket_connect("/ws/market") as websocket:
            snapshot = websocket.receive_json()
            assert snapshot["type"] == "market"
            assert snapshot["prediction"]["risk_level"]
