import threading


class BaseThread(threading.Thread):

    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None, *, daemon=None):
        super().__init__(group, target, name, args, kwargs, daemon=daemon)

        self._exit_event = threading.Event()
        self._is_ready_event = threading.Event()
        self._stop_event = threading.Event()

    def exit(self):
        self._exit_event.set()

    @property
    def is_exited(self):
        return self._exit_event.is_set()

    @property
    def is_ready(self):
        return self._is_ready_event.is_set()

    @is_ready.setter
    def is_ready(self, value: bool):
        if value:
            self._is_ready_event.set()
        else:
            self._is_ready_event.clear()

    def stop(self):
        self._stop_event.set()

    @property
    def is_stopped(self):
        return self._stop_event.is_set()

    def resume(self):
        self._stop_event.clear()
