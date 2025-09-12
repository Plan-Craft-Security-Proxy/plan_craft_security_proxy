import abc
from pathlib import Path
from typing import Any, Dict

class ProxyServerReceiver(abc.ABC):
    def __init__(
            self,
            bin_file_path: Path,
            config_path: Path,
            cwd: Path
    ):
        self.bin_file_path = bin_file_path
        self.config_path = config_path
        self.cwd = cwd


    @abc.abstractmethod
    def start(self) -> Any: raise NotImplementedError

    @abc.abstractmethod
    def stop(self) -> Any: raise NotImplementedError

    @abc.abstractmethod
    def status(self) -> Any: raise NotImplementedError