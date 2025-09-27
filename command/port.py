from typing import Iterable

from .base import Command
class IPortCommand(Command):

    def execute(self) -> Iterable[int]: yield from self.core.port()