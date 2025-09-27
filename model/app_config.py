import abc
from pathlib import Path
from typing import Annotated, List, Iterable, Any

from pydantic import BaseModel, Field
from pydantic.functional_validators import BeforeValidator
from common import ELoggerLevel, ELoggerHandler


class LoggerConfig(BaseModel, abc.ABC):
    handler: Annotated[
        ELoggerHandler,
        Field(title='日志打印到控制台还是文件中', default=ELoggerHandler.FILE)
    ]

    level: Annotated[
        ELoggerLevel,
        Field(title='日志打印等级', default=ELoggerLevel.INFO)
    ]

class ConsoleLoggerConfig(LoggerConfig): pass

class FileLoggerConfig(LoggerConfig):

    file: Annotated[
        Path,
        Field(title='日志文件路径')
    ]


def log_before_validator(data: Iterable[dict[str, Any]]) -> Iterable[LoggerConfig]:
    def __validate(item: dict[str, Any]) -> LoggerConfig:
        match ELoggerHandler(item['handler']):
            case ELoggerHandler.FILE: return FileLoggerConfig.model_validate(item)
            case ELoggerHandler.CONSOLE: return ConsoleLoggerConfig.model_validate(item)
        raise NotImplementedError
    return [__validate(item) for item in data]

class AppConfig(BaseModel):

    log: Annotated[
        List[LoggerConfig],
        Field(title='日志配置', default=[]),
        BeforeValidator(log_before_validator)
    ]
