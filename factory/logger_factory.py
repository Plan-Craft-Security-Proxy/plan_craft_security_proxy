from collections.abc import Callable
from typing import Dict
from common import EFactory, Logger, ELogger
from .base import Factory, IFactory, PoolFactory


class ILoggerFactory(PoolFactory[Logger]):
    __instance_pool: Dict[ELogger, Factory[Logger | Callable[..., Logger]]] = {
        ELogger.DEFAULT_LOGGER: IFactory(Logger)
    }

    __id = EFactory.LOGGER

    @classmethod
    def id(cls) -> EFactory: return cls.__id

    @classmethod
    def instance_pool(cls) -> Dict[ELogger, Factory[Logger | Callable[..., Logger]]]:
        return cls.__instance_pool
