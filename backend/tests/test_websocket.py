import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.main import app

client = TestClient(app)


def test_ws_connect_and_ping():
    with client.websocket_connect("/ws") as websocket:
        connected = websocket.receive_json()
        assert connected["type"] == "CONNECTED"
        assert connected["data"]["role"] == "anonymous"

        websocket.send_json({"type": "ping"})
        pong = websocket.receive_json()
        assert pong["type"] == "PONG"


def test_ws_denies_admin_topic_for_anonymous():
    with client.websocket_connect("/ws") as websocket:
        websocket.receive_json()
        websocket.send_json({"type": "subscribe", "topics": ["public", "admin"]})
        message = websocket.receive_json()
        assert message["type"] == "SUBSCRIBED"
        assert "public" in message["data"]["topics"]
        assert message["data"]["denied"] == ["admin"]


def test_ws_rejects_unknown_message_type():
    with client.websocket_connect("/ws") as websocket:
        websocket.receive_json()
        websocket.send_json({"type": "nope"})
        message = websocket.receive_json()
        assert message["type"] == "ERROR"


def test_ws_rejects_invalid_token():
    with pytest.raises(WebSocketDisconnect) as closed:
        with client.websocket_connect("/ws?token=invalid") as websocket:
            websocket.receive_json()
    assert closed.value.code == 4401
