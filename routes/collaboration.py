from fastapi import APIRouter,WebSocket,WebSocketDisconnect
from typing import Dict, Set
import logging
router=APIRouter()
active_connections:Dict[int,Set[WebSocket]]={}
logger=logging.getLogger("websockets")
@router.websocket("/ws/{file_id}")
async def websocket_endpoint(websocket:WebSocket,file_id:int):
    await websocket.accept()

    if file_id not in active_connections:
        active_connections[file_id]=set()
    active_connections[file_id].add(websocket)

    logger.info(f"New Websocket Connectopn for file {file_id} .")
    try:
        while True:
            data=await websocket.receive_text()
            logger.info(f"Recieved data for file {file_id}:{data}")


            if file_id in active_connections:
                for conn in active_connections[file_id]:
                    if conn !=websocket:
                        await conn.send_text(data)
    except WebSocketDisconnect:
        logger.info(f"Web socket disconnected for file {file_id}")
        active_connections[file_id].discard(websocket)


        if not active_connections[file_id]:
            del active_connections[file_id]
    except Exception as e:
        logger.error(f"Websocket error :{e}")
        await websocket.close()
    finally
        logger.info(f"Connection closed for file {file_id} .")