from typing import Any

from .command import ProxyServerCommand


class ProxyServerInvoker:

    def __init__(self, command: ProxyServerCommand | None = None):
        self.command = command

    def run(self) -> Any:  return self.command.execute()