from typing import Any, Annotated, Type, TypeVar, Iterable
from pydantic import validate_call, Field

from common import EFactory, ELoggerLevel, Logger
from factory import ICoreFactory, Factory, IServerFactory, ICommandFactory, IModelFactory, IRepoFactory, IPoolFactory, \
    ILoggerFactory


T = TypeVar('T')

@validate_call()
def create(
        e: Annotated[
            EFactory,
            Field(title='工厂枚举')
        ],
        t: Type[T] | None = None,
        *args,
        **kwargs
) -> T:
    factory: Factory | None = None
    match e:
        case EFactory.CORE: factory = ICoreFactory()
        case EFactory.SERVER: factory = IServerFactory()
        case EFactory.COMMAND: factory = ICommandFactory()
        case EFactory.MODEL: factory = IModelFactory()
        case EFactory.REPO: factory = IRepoFactory()
        case EFactory.POOL: factory = IPoolFactory()
        case EFactory.LOGGER: factory = ILoggerFactory()
        case _: raise NotImplementedError

    return factory.create(*args, **kwargs)


def log(
        level: ELoggerLevel,
        msg: str,
        logger: Iterable[Logger]
) -> None:
    for l in logger:
        match level:
            case ELoggerLevel.DEBUG: l.logger.debug(msg)
            case ELoggerLevel.INFO: l.logger.info(msg)
            case ELoggerLevel.WARN: l.logger.warning(msg)
            case ELoggerLevel.ERROR: l.logger.error(msg)
            case _: raise NotImplementedError