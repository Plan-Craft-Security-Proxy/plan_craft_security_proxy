from .base import Command


class IStartCommand(Command):

    def execute(self) -> None: self.core.start()