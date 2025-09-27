from collections.abc import Callable
from typing import Dict, TypeAlias

from pydantic import BaseModel

from model import LoggerConfig, ConsoleLoggerConfig, FileLoggerConfig, AppConfig, ServerConfig
from .base import Factory, IFactory, PoolFactory
from common import EFactory, EModel

T: TypeAlias = (
        BaseModel |
        LoggerConfig |
        ConsoleLoggerConfig |
        FileLoggerConfig |
        AppConfig
)

class IModelFactory(PoolFactory[T]):
    __instance_pool: Dict[EModel, Factory[BaseModel | Callable[..., BaseModel]]] = {
        EModel.CONSOLE_LOGGER_CONFIG: IFactory(ConsoleLoggerConfig),
        EModel.FILE_LOGGER_CONFIG: IFactory(FileLoggerConfig),
        EModel.APP_CONFIG: IFactory(AppConfig),
        EModel.SERVER_CONFIG: IFactory(ServerConfig)
    }

    __id = EFactory.MODEL

    @classmethod
    def id(cls) -> EFactory: return cls.__id

    @classmethod
    def instance_pool(cls) -> Dict[EModel, Factory[BaseModel | Callable[..., BaseModel]]]:
        return cls.__instance_pool
