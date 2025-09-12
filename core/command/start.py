
import subprocess


from core.command import ProxyServerCommand


class ProxyServerStartCommand(ProxyServerCommand):

    def execute(self) -> subprocess.Popen:
        return self.receiver.start()

