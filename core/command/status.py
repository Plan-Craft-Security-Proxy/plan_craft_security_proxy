from core.command import ProxyServerCommand


class ProxyServerStatusCommand(ProxyServerCommand):

    def execute(self) -> bool:
        return self.receiver.status()
