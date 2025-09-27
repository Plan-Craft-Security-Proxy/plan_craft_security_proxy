from collections.abc import Callable
from typing import Dict

from repository import PRepository, IAppConfigRepo, IServerConfigRepo
from .base import Factory, IFactory, PoolFactory
from common import EFactory, ERepo


class IRepoFactory(PoolFactory[PRepository]):
    __instance_pool: Dict[ERepo, Factory[PRepository | Callable[..., PRepository]]] = {
        ERepo.APP_CONFIG_REPO: IFactory(IAppConfigRepo),
        ERepo.SERVER_CONFIG_REPO: IFactory(IServerConfigRepo)
    }

    __id = EFactory.REPO

    @classmethod
    def id(cls) -> EFactory: return cls.__id

    @classmethod
    def instance_pool(cls) -> Dict[ERepo, Factory[PRepository | Callable[..., PRepository]]]:
        return cls.__instance_pool
