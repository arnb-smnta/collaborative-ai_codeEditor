from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Set, Deque
import logging
import time
from collections import deque

router = APIRouter()
active_connections: Dict[int, Set[WebSocket]] = {}

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
    try:
        while True:
            data = await websocket.receive_text()

            # Check rate limiting
            current_time = time.time()
            message_history[websocket_id].append(current_time)

            # If we have MAX_MESSAGES messages, check if they're within the time window
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
        cleanup_connection(websocket, file_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        cleanup_connection(websocket, file_id)
        await websocket.close()
    finally:
        logger.info(f"Connection closed for file {file_id}.")


def cleanup_connection(websocket: WebSocket, file_id: int):
    """Helper function to clean up connection resources"""
    websocket_id = id(websocket)

    if file_id in active_connections:
        active_connections[file_id].discard(websocket)
        if not active_connections[file_id]:
            del active_connections[file_id]

    if websocket_id in message_history:
        del message_history[websocket_id]
