import abc
from typing import Annotated, Iterable, Protocol
from pydantic import BaseModel, FilePath, Field, validate_call

from common import ECoreStatus

class PCore(Protocol):
    def start(self) -> None:
        """
        启动内核
        :return: None
        """
        raise NotImplementedError

    def stop(self) -> None:
        """
        停止内核
        :return: None
        """
        raise NotImplementedError

    def status(self) -> ECoreStatus:
        """
        返回内核当前运行状态
        :return: 运行状态枚举值：{ECoreStatus.RUN: 启动状态; ECoreStatus.STOP: 停止状态;}
        """
        raise NotImplementedError

    def version(self) -> str:
        """
        返回内核版本号
        :return: 内核版本号
        """
        raise NotImplementedError

    def port(self) -> Iterable[int]:
        """
        返回内核监听本地端口号
        :return: 内核监听的本体端口号
        """
        raise NotImplementedError


class Core(BaseModel, abc.ABC):

    bin: Annotated[
        FilePath,
        Field(title='可执行文件')
    ]

    conf: Annotated[
        FilePath | None,
        Field(title='配置文件', default=None)
    ]

    @abc.abstractmethod
    def start(self) -> None:
        """
        启动内核
        :return: None
        """
        raise NotImplementedError

    @abc.abstractmethod
    def stop(self) -> None:
        """
        停止内核
        :return: None
        """
        raise NotImplementedError

    @abc.abstractmethod
    def status(self) -> ECoreStatus:
        """
        返回内核当前运行状态
        :return: 运行状态枚举值：{ECoreStatus.RUN: 启动状态; ECoreStatus.STOP: 停止状态;}
        """
        raise NotImplementedError

    @abc.abstractmethod
    def version(self) -> str:
        """
        返回内核版本号
        :return: 内核版本号
        """
        raise NotImplementedError

    @abc.abstractmethod
    def port(self) -> Iterable[int]:
        """
        返回内核监听本地端口号
        :return: 内核监听的本体端口号
        """
        raise NotImplementedError


class EmptyCore:
    def start(self) -> None:
        """
        启动内核
        :return: None
        """
        pass

    def stop(self) -> None:
        """
        停止内核
        :return: None
        """
        pass

    def status(self) -> ECoreStatus:
        """
        返回内核当前运行状态
        :return: 运行状态枚举值：{ECoreStatus.RUN: 启动状态; ECoreStatus.STOP: 停止状态;}
        """
        pass

    def version(self) -> str:
        """
        返回内核版本号
        :return: 内核版本号
        """
        pass

    def port(self) -> Iterable[int]:
        """
        返回内核监听本地端口号
        :return: 内核监听的本体端口号
        """
        pass