import asyncio
from contextlib import asynccontextmanager
from typing import Set, Dict

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from voice_dialogue.core.constants import websocket_message_queue, session_manager
from voice_dialogue.utils.logger import logger

ws = APIRouter()


class WebSocketConnectionManager:
    """WebSocket 连接管理器 - 管理所有活跃连接"""

    def __init__(self):
        # 使用 WeakSet 避免内存泄漏
        self._connections: Set[WebSocket] = set()
        # 会话ID到连接的映射
        self._session_connections: Dict[str, Set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, session_id: str = None):
        """建立新连接"""
        async with self._lock:
            await websocket.accept()
            self._connections.add(websocket)

            # 如果指定了会话ID，建立映射关系
            if session_id:
                if session_id not in self._session_connections:
                    self._session_connections[session_id] = set()
                self._session_connections[session_id].add(websocket)

            logger.info(f"WebSocket连接已建立，当前活跃连接数: {len(self._connections)}")

    async def disconnect(self, websocket: WebSocket):
        """断开连接"""
        async with self._lock:
            self._connections.discard(websocket)

            # 从会话映射中移除
            for session_id, connections in list(self._session_connections.items()):
                connections.discard(websocket)
                if not connections:  # 如果该会话没有活跃连接，清理映射
                    del self._session_connections[session_id]

            logger.info(f"WebSocket连接已断开，当前活跃连接数: {len(self._connections)}")

    async def close_session_connections(self, session_id: str):
        """关闭指定会话的所有连接"""
        async with self._lock:
            if session_id in self._session_connections:
                connections_to_close = list(self._session_connections[session_id])
                for connection in connections_to_close:
                    try:
                        await connection.close()
                        logger.info(f"已关闭会话 {session_id} 的一个连接")
                    except Exception as e:
                        logger.warning(f"关闭连接时出错: {e}")

                # 清理映射
                del self._session_connections[session_id]

    async def send_to_session(self, session_id: str, message: dict):
        """向指定会话的所有连接发送消息"""
        async with self._lock:
            if session_id in self._session_connections:
                connections = list(self._session_connections[session_id])
                disconnected_connections = []

                for connection in connections:
                    try:
                        await connection.send_json(message)
                    except Exception as e:
                        logger.warning(f"发送消息失败，标记连接为断开: {e}")
                        disconnected_connections.append(connection)

                # 清理断开的连接
                for connection in disconnected_connections:
                    await self.disconnect(connection)

    async def broadcast(self, message: dict):
        """向所有活跃连接广播消息"""
        async with self._lock:
            if not self._connections:
                return

            connections = list(self._connections)
            disconnected_connections = []

            for connection in connections:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.warning(f"广播消息失败，标记连接为断开: {e}")
                    disconnected_connections.append(connection)

            # 清理断开的连接
            for connection in disconnected_connections:
                await self.disconnect(connection)

    @property
    def connection_count(self) -> int:
        """获取当前连接数"""
        return len(self._connections)

    def get_session_connection_count(self, session_id: str) -> int:
        """获取指定会话的连接数"""
        return len(self._session_connections.get(session_id, set()))


# 全局连接管理器实例
connection_manager = WebSocketConnectionManager()


@asynccontextmanager
async def websocket_connection_context(websocket: WebSocket):
    """WebSocket连接上下文管理器"""
    current_session_id = session_manager.current_id

    # 关闭同一会话的旧连接
    if connection_manager.get_session_connection_count(current_session_id) > 0:
        logger.info(f"检测到会话 {current_session_id} 已有连接，关闭旧连接")
        await connection_manager.close_session_connections(current_session_id)

    try:
        # 建立新连接
        await connection_manager.connect(websocket, current_session_id)
        yield websocket
    finally:
        # 确保连接被正确清理
        await connection_manager.disconnect(websocket)


@ws.websocket("/api/v1/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket连接端点"""
    async with websocket_connection_context(websocket) as websocket_connection:
        disconnect_task = asyncio.create_task(websocket_connection.receive_text())
        get_message_task = None

        try:
            # 保持连接活跃
            while True:
                get_message_task = asyncio.create_task(websocket_message_queue.get())

                done, pending = await asyncio.wait(
                    {disconnect_task, get_message_task},
                    return_when=asyncio.FIRST_COMPLETED
                )

                # 如果是 disconnect_task 完成，说明客户端已断开连接。
                if disconnect_task in done:
                    # 这将重新引发 WebSocketDisconnect 异常并跳出循环。
                    if get_message_task in done:
                        # 如果有，将消息放回队列，然后让连接断开
                        message = get_message_task.result()
                        websocket_message_queue.put_nowait(message)
                        logger.info("连接已关闭，将消息重新入队。")

                    disconnect_task.result()

                # 如果是 queue_task 完成，说明有可用的消息。
                if get_message_task in done:
                    message = get_message_task.result()
                    await connection_manager.send_to_session(message.session_id, message.model_dump())
                    # queue_task 现已完成，我们将在循环的下一次迭代中创建一个新的。

        except WebSocketDisconnect:
            logger.info("WebSocket连接已断开")
        except Exception as e:
            logger.error(f"WebSocket连接异常: {e}")
        finally:
            # 确保如果循环因其他原因退出，disconnect_task 会被取消。
            disconnect_task.cancel()
            if get_message_task and not get_message_task.done():
                get_message_task.cancel()
