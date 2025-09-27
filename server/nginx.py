from typing import Annotated, List

from common import EServerAction, EServerState, ECoreCommand, ECore
from factory import ICoreFactory
from .base import Server
from pydantic import validate_call, FilePath, Field


class INginxServer(Server):

    @validate_call()
    def __init__(
            self,
            bin: Annotated[FilePath, Field(title='二进制可执行文件路径')],
            conf: Annotated[FilePath | None, Field(title='配置文件路径', default=None)],
            time_wait: Annotated[int, Field(title='等待时间', ge=0, default=5)]
    ):
        core = ICoreFactory().create(ECore.NGINX, bin=bin, conf=conf)
        commands: List[ECoreCommand] = [
            ECoreCommand.START, ECoreCommand.STOP, ECoreCommand.STATUS, ECoreCommand.VERSION, ECoreCommand.PORT
        ]
        super().__init__(core, commands, time_wait)

    def update(self, action: EServerAction) -> EServerState:
        return super().update(action)