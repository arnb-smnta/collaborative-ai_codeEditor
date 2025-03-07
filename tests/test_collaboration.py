import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import pytest
import time
import json
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocketDisconnect
from main import app  # Adjust import path according to your project structure
from routes.collaboration import (
    cleanup_connection,
    cleanup_notification_connection,
    active_connections,
    notification_connections,
    message_history,
)

client = TestClient(app)


@pytest.mark.asyncio
async def test_websocket_connection():
    """Test if the WebSocket connection opens successfully"""
    file_id = 1
    with client.websocket_connect(f"/ws/{file_id}") as websocket:
        assert websocket is not None


@pytest.mark.asyncio
async def test_websocket_message_exchange():
    """Test if messages are properly sent and received"""
    file_id = 2
    with (
        client.websocket_connect(f"/collaborate/ws/{file_id}") as websocket1,
        client.websocket_connect(f"/collaborate/ws/{file_id}") as websocket2,
    ):
        message = "Hello, WebSocket!"
        websocket1.send_text(message)
        received = websocket2.receive_text()
        assert received == message


@pytest.mark.asyncio
async def test_websocket_rate_limiting():
    """Test if the rate limiter blocks excessive messages"""
    file_id = 3
    with client.websocket_connect(f"/collaborate/ws/{file_id}") as websocket:
        for _ in range(10):  # Send MAX_MESSAGES
            websocket.send_text("Test Message")
            time.sleep(0.05)  # Ensure messages are within TIME_WINDOW

        websocket.send_text("Excess Message")
        error_response = websocket.receive_text()
        assert "Error: Rate limit exceeded" in error_response


@pytest.mark.asyncio
async def test_websocket_cleanup_on_disconnect():
    """Test if the WebSocket cleans up connections properly after disconnect"""
    file_id = 4
    with client.websocket_connect(f"/collaborate/ws/{file_id}") as websocket:
        websocket_id = id(websocket)
        assert file_id in active_connections
        assert websocket in active_connections[file_id]

    # Simulate cleanup after disconnect
    cleanup_connection(websocket, file_id)

    assert file_id not in active_connections
    assert websocket_id not in message_history


@pytest.mark.asyncio
async def test_websocket_multiple_clients():
    """Test multiple clients communicating via WebSocket"""
    file_id = 5
    with (
        client.websocket_connect(f"/collaborate/ws/{file_id}") as websocket1,
        client.websocket_connect(f"/collaborate/ws/{file_id}") as websocket2,
    ):
        websocket1.send_text("Client 1 says hi")
        websocket2.send_text("Client 2 replies hello")

        received1 = websocket1.receive_text()
        received2 = websocket2.receive_text()

        assert received1 == "Client 2 replies hello"
        assert received2 == "Client 1 says hi"


@pytest.mark.asyncio
async def test_websocket_disconnection():
    """Test if the WebSocket handles disconnection gracefully"""
    file_id = 6
    with client.websocket_connect(f"/collaborate/ws/{file_id}") as websocket:
        websocket.close()

    # Ensure connection is cleaned up
    assert file_id not in active_connections


# New tests for the notification WebSocket functionality


@pytest.mark.asyncio
async def test_notification_websocket_connection():
    """Test if the notification WebSocket connection opens successfully"""
    with client.websocket_connect("/collaborate/notifications") as websocket:
        assert websocket is not None
        assert websocket in notification_connections


@pytest.mark.asyncio
async def test_notification_message_exchange():
    """Test if notification messages are properly sent and received"""
    with (
        client.websocket_connect("/collaborate/notifications") as websocket1,
        client.websocket_connect("/collaborate/notifications") as websocket2,
    ):
        notification = {
            "type": "test_notification",
            "message": "Test notification message",
        }

        websocket1.send_text(json.dumps(notification))
        received = json.loads(websocket2.receive_text())

        assert received["type"] == notification["type"]
        assert received["message"] == notification["message"]


@pytest.mark.asyncio
async def test_notification_rate_limiting():
    """Test if the rate limiter blocks excessive notification messages"""
    with client.websocket_connect("/collaborate/notifications") as websocket:
        notification = {
            "type": "test_notification",
            "message": "Test notification message",
        }

        for _ in range(10):  # Send MAX_MESSAGES
            websocket.send_text(json.dumps(notification))
            time.sleep(0.05)  # Ensure messages are within TIME_WINDOW

        websocket.send_text(json.dumps(notification))
        error_response = websocket.receive_text()

        assert "Error: Rate limit exceeded" in error_response


@pytest.mark.asyncio
async def test_notification_cleanup_on_disconnect():
    """Test if the notification WebSocket cleans up connections properly after disconnect"""
    with client.websocket_connect("/collaborate/notifications") as websocket:
        websocket_id = id(websocket)
        assert websocket in notification_connections

    # Simulate cleanup after disconnect
    cleanup_notification_connection(websocket)

    assert websocket not in notification_connections
    assert websocket_id not in message_history


@pytest.mark.asyncio
async def test_notification_invalid_json():
    """Test handling of invalid JSON in notification messages"""
    with client.websocket_connect("/collaborate/notifications") as websocket:
        # Send invalid JSON
        websocket.send_text("{invalid json")
        error_response = websocket.receive_text()

        assert "Error: Invalid notification format" in error_response


@pytest.mark.asyncio
async def test_user_join_notification():
    """Test if joining a file broadcasts a notification"""
    file_id = 7

    # First connect to the notification WebSocket
    with client.websocket_connect(
        "/collaborate/notifications"
    ) as notification_websocket:
        # Then connect to a file WebSocket
        with client.websocket_connect(f"/collaborate/ws/{file_id}") as file_websocket:
            # We should receive a user_joined notification
            notification = json.loads(notification_websocket.receive_text())

            assert notification["type"] == "user_joined"
            assert notification["file_id"] == file_id


@pytest.mark.asyncio
async def test_user_leave_notification():
    """Test if leaving a file broadcasts a notification"""
    file_id = 8

    # First connect to the notification WebSocket
    with client.websocket_connect(
        "/collaborate/notifications"
    ) as notification_websocket:
        # Create a context for the file WebSocket that we'll exit
        with client.websocket_connect(f"/collaborate/ws/{file_id}"):
            # Receive and ignore the join notification
            notification_websocket.receive_text()

        # After the file WebSocket context exits, we should receive a user_left notification
        notification = json.loads(notification_websocket.receive_text())

        assert notification["type"] == "user_left"
        assert notification["file_id"] == file_id
