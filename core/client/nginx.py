
from pathlib import Path

from core.client import ProxyServerClient
from core.command import ProxyServerStartCommand, ProxyServerStopCommand, ProxyServerStatusCommand, ProxyServerCommand
from core.invoker import ProxyServerInvoker
from core.receiver import ProxyServerReceiver
from core.receiver import NginxProxyServerReceiver


class NginxProxyServerClient(ProxyServerClient):

    @property
    def receiver(self) -> ProxyServerReceiver: return self.__receiver

    @property
    def invoker(self) -> ProxyServerInvoker: return self.__invoker

    @property
    def start_cmd(self) -> ProxyServerCommand: return self.__start_cmd

    @property
    def stop_cmd(self) -> ProxyServerCommand: return self.__stop_cmd

    @property
    def status_cmd(self) -> ProxyServerCommand: return self.__status_cmd

    def __init__(
            self,
            bin_file_path: Path,
            config_path: Path,
            cwd: Path
    ):
        self.__receiver = NginxProxyServerReceiver(bin_file_path, config_path, cwd)
        self.__invoker = ProxyServerInvoker()
        self.__start_cmd = ProxyServerStartCommand(self.receiver)
        self.__stop_cmd = ProxyServerStopCommand(self.receiver)
        self.__status_cmd = ProxyServerStatusCommand(self.receiver)
        super().__init__()

