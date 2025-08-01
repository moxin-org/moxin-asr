import threading
import uuid


class SessionIdManager:
    def __init__(self):
        self._current_id: str = f'{uuid.uuid4()}'
        self._lock = threading.Lock()  # 为线程安全添加锁

    def get_id(self) -> str:
        """获取当前的会话ID (线程安全)。"""
        with self._lock:
            return self._current_id

    def set_id(self, new_id: str) -> None:
        """设置新的会话ID (线程安全)。"""
        with self._lock:
            self._current_id = new_id

    def reset_id(self) -> str:
        """生成一个新的UUID作为会话ID，并更新当前ID，然后返回新的ID (线程安全)。"""
        with self._lock:
            self._current_id = f'{uuid.uuid4()}'
            return self._current_id

    @property
    def current_id(self) -> str:
        """通过属性方式获取当前的会话ID (线程安全)。"""
        return self.get_id()

    @current_id.setter
    def current_id(self, value: str) -> None:
        """通过属性方式设置新的会话ID (线程安全)。"""
        self.set_id(value)
