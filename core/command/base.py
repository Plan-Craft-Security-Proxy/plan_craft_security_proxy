import abc
from typing import Any

from core.receiver import ProxyServerReceiver


class ProxyServerCommand(abc.ABC):
    def __init__(
            self,
            receiver: ProxyServerReceiver
    ):
        self.receiver = receiver

    @abc.abstractmethod
    def execute(self) -> Any: raise NotImplementedError

