from collections import OrderedDict


class LRUCacheDict(OrderedDict):
    """带有大小限制的字典，自动淘汰最近最少使用的项"""

    def __init__(self, *args, maxsize: int = 10, **kwargs):
        assert maxsize > 0
        self.maxsize = maxsize
        super().__init__(*args, **kwargs)

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        super().move_to_end(key)

        while len(self) > self.maxsize:
            oldkey = next(iter(self))
            super().__delitem__(oldkey)

    def __getitem__(self, key):
        val = super().__getitem__(key)
        super().move_to_end(key)
        return val 