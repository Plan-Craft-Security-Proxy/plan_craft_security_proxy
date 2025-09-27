from common import ECoreStatus
from .base import Command

class IStatusCommand(Command):

    def execute(self) -> ECoreStatus: return self.core.status()
