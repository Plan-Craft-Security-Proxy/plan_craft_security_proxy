from .base import Command

class IVersionCommand(Command):

    def execute(self) -> str: return self.core.version()