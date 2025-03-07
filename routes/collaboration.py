from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Set, Deque
import logging
import time
import json
from collections import deque

router = APIRouter()

# Existing file-specific connections
active_connections: Dict[int, Set[WebSocket]] = {}

# New global notification connections
notification_connections: Set[WebSocket] = set()

message_history: Dict[int, Deque[float]] = {}
# Rate limit settings
MAX_MESSAGES = 10  # Maximum messages per time window
TIME_WINDOW = 1.0  # Time window in seconds
logger = logging.getLogger("websockets")


@router.websocket("/ws/{file_id}")
async def websocket_endpoint(websocket: WebSocket, file_id: int):
    await websocket.accept()

    websocket_id = id(websocket)

    active_connections.setdefault(file_id, set()).add(websocket)
    message_history[websocket_id] = deque(maxlen=MAX_MESSAGES)

    logger.info(f"New WebSocket Connection for file {file_id}.")

    # Notify all users someone joined this file
    await broadcast_notification(
        {
            "type": "user_joined",
            "file_id": file_id,
            "message": f"A new user joined file {file_id}",
        }
    )

    try:
        while True:
            data = await websocket.receive_text()

            # Check rate limiting
            current_time = time.time()
            message_history[websocket_id].append(current_time)

            if (
                len(message_history[websocket_id]) == MAX_MESSAGES
                and current_time - message_history[websocket_id][0] < TIME_WINDOW
            ):
                logger.warning(
                    f"Rate limit exceeded for file {file_id}, connection {websocket_id}"
                )
                await websocket.send_text(
                    "Error: Rate limit exceeded. Please slow down."
                )
                continue

            logger.info(f"Received data for file {file_id}: {data}")

            if file_id in active_connections:
                for conn in active_connections[file_id]:
                    if conn != websocket:
                        await conn.send_text(data)
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for file {file_id}")

        # Notify all users someone left this file
        await broadcast_notification(
            {
                "type": "user_left",
                "file_id": file_id,
                "message": f"A user left file {file_id}",
            }
        )

        cleanup_connection(websocket, file_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        cleanup_connection(websocket, file_id)
        await websocket.close()
    finally:
        logger.info(f"Connection closed for file {file_id}.")


@router.websocket("/notifications")
async def notifications_websocket(websocket: WebSocket):
    await websocket.accept()

    websocket_id = id(websocket)
    notification_connections.add(websocket)
    message_history[websocket_id] = deque(maxlen=MAX_MESSAGES)

    logger.info(f"New notification WebSocket connection: {websocket_id}")

    try:
        while True:
            data = await websocket.receive_text()

            # Check rate limiting
            current_time = time.time()
            message_history[websocket_id].append(current_time)

            if (
                len(message_history[websocket_id]) == MAX_MESSAGES
                and current_time - message_history[websocket_id][0] < TIME_WINDOW
            ):
                logger.warning(
                    f"Rate limit exceeded for notification connection {websocket_id}"
                )
                await websocket.send_text(
                    "Error: Rate limit exceeded. Please slow down."
                )
                continue

            try:
                notification_data = json.loads(data)
                logger.info(f"Received notification: {notification_data}")

                await broadcast_notification(notification_data, exclude=websocket)
            except json.JSONDecodeError:
                logger.warning(f"Invalid notification format: {data}")
                await websocket.send_text(
                    "Error: Invalid notification format. Must be valid JSON."
                )

    except WebSocketDisconnect:
        logger.info(f"Notification WebSocket disconnected: {websocket_id}")
        cleanup_notification_connection(websocket)
    except Exception as e:
        logger.error(f"Notification WebSocket error: {e}", exc_info=True)
        cleanup_notification_connection(websocket)
        await websocket.close()
    finally:
        logger.info(f"Notification connection closed: {websocket_id}")


async def broadcast_notification(notification_data: dict, exclude: WebSocket = None):
    """Send a notification to all connected notification clients"""
    if not notification_connections:
        return

    message = json.dumps(notification_data)
    for conn in notification_connections:
        if conn != exclude:  # Don't send back to sender if specified
            try:
                await conn.send_text(message)
            except Exception as e:
                logger.error(f"Error sending notification: {e}")


def cleanup_connection(websocket: WebSocket, file_id: int):
    """Helper function to clean up connection resources"""
    websocket_id = id(websocket)

    if file_id in active_connections:
        active_connections[file_id].discard(websocket)
        if not active_connections[file_id]:
            del active_connections[file_id]

    if websocket_id in message_history:
        del message_history[websocket_id]


def cleanup_notification_connection(websocket: WebSocket):
    """Helper function to clean up notification connection resources"""
    websocket_id = id(websocket)

    notification_connections.discard(websocket)

    if websocket_id in message_history:
        del message_history[websocket_id]
