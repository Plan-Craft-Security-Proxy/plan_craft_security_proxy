from collections.abc import Callable
from typing import Dict
from command import Command, IPortCommand, IStartCommand, IStatusCommand, IStopCommand, IVersionCommand
from common import ECoreCommand, EFactory
from .base import Factory, IFactory, PoolFactory


class ICommandFactory(PoolFactory[Command]):
    __instance_pool: Dict[ECoreCommand, Factory[Command | Callable[..., Command]]] = {
        ECoreCommand.PORT: IFactory(IPortCommand),
        ECoreCommand.START: IFactory(IStartCommand),
        ECoreCommand.STATUS: IFactory(IStatusCommand),
        ECoreCommand.STOP: IFactory(IStopCommand),
        ECoreCommand.VERSION: IFactory(IVersionCommand)
    }

    __id = EFactory.COMMAND

    @classmethod
    def id(cls) -> EFactory: return cls.__id

    @classmethod
    def instance_pool(cls) -> Dict[ECoreCommand, Factory[Command | Callable[..., Command]]]:
        return cls.__instance_pool
