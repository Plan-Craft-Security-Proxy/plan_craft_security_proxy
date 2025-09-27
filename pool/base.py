"""
    缓存池
"""
import abc
from queue import Queue
from typing import Generic, TypeVar

from common import EFactory
from factory import IRepoFactory, IModelFactory, ICoreFactory, IServerFactory, ICommandFactory

T = TypeVar('T')

class Pool(abc.ABC, Generic[T]):

    def __init__(
            self,
            queue: Queue[T],
            block: bool = True,
            time_wait: float = 5,
            auto_get: bool = True,
    ):
        self.__queue: Queue[T] = queue
        self.__block = block
        self.__time_wait = time_wait
        self.__item = self.__queue.get(self.__block, self.__time_wait) if auto_get else None

    def __enter__(self) -> T | None:
        if self.__item is None:
            self.__item = self.__queue.get(self.__block, self.__time_wait)
        return self.__item

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.__item is not None:
            self.__queue.put(self.__item, self.__block, self.__time_wait)
            self.__item = None

    def __del__(self):
        if self.__item is not None:
            self.__queue.put(self.__item)
            self.__item = None

class IPool(Pool[T], Generic[T]):

    def __init__(
            self,
            size: int = 1,
            block: bool = True,
            time_wait: float = 5,
            auto_get: bool = True,
            f: EFactory = EFactory.REPO,
            *args,
            **kwargs
    ):
        queue: Queue[T] = Queue(size)
        for i in range(0, size):
            obj: T | None = None
            match f:
                case EFactory.REPO: obj = IRepoFactory().create(*args, **kwargs)
                case EFactory.MODEL: obj = IModelFactory().create(*args, **kwargs)
                case EFactory.CORE: obj = ICoreFactory().create(*args, **kwargs)
                case EFactory.SERVER: obj = IServerFactory().create(*args, **kwargs)
                case EFactory.COMMAND: obj = ICommandFactory().create(*args, **kwargs)
                case _: raise NotImplementedError
            queue.put(obj)
        super().__init__(queue, block, time_wait, auto_get)