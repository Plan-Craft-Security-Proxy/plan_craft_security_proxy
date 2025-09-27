from .base import Command

class IStopCommand(Command):

    def execute(self) -> None: self.core.stop()
