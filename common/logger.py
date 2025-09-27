import datetime
import logging
from pathlib import Path
from pydantic import TypeAdapter
from common import ELoggerHandler, ELoggerLevel
from model import LoggerConfig, FileLoggerConfig

class Logger:

    def __init__(
            self,
            name: str,
            logger_config: LoggerConfig
    ):
        formatter = logging.Formatter(
            fmt='%(asctime)s %(name)s [%(pathname)s line:%(lineno)d] %(levelname)s %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        self.__logger = logging.getLogger(name)

        match logger_config.handler:
            case ELoggerHandler.CONSOLE:
                self.__handler = logging.StreamHandler()
            case ELoggerHandler.FILE:
                file_logger_config = TypeAdapter(FileLoggerConfig).validate_python(logger_config)
                log_file: Path = file_logger_config.file.parent / '_'.join([
                    datetime.datetime.now().strftime('%Y-%m-%d'),
                    file_logger_config.file.name
                ])
                log_file.parent.mkdir(parents=True, exist_ok=True)
                self.__handler = logging.FileHandler(log_file, encoding='utf8')
            case _: raise NotImplementedError

        match logger_config.level:
            case ELoggerLevel.DEBUG:
                self.__logger.setLevel(logging.DEBUG)
                self.__handler.setLevel(logging.DEBUG)
            case ELoggerLevel.INFO:
                self.__logger.setLevel(logging.INFO)
                self.__handler.setLevel(logging.INFO)
            case ELoggerLevel.WARN:
                self.__logger.setLevel(logging.WARN)
                self.__handler.setLevel(logging.WARN)
            case ELoggerLevel.ERROR:
                self.__logger.setLevel(logging.ERROR)
                self.__handler.setLevel(logging.ERROR)
            case _: raise NotImplementedError

        self.__handler.setFormatter(formatter)
        self.__logger.addHandler(self.__handler)

    @property
    def logger(self) -> logging.Logger: return self.__logger