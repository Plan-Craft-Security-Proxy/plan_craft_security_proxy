
from typing import Any

from core.command import ProxyServerCommand


class ProxyServerStopCommand(ProxyServerCommand):

    def execute(self) -> Any:
        return self.receiver.stop()


