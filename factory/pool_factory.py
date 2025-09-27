from functools import partial
from typing import Dict, Callable


from pool import Pool, IRepoPool
from .base import Factory, IFactory, PoolFactory
from common import EFactory, EPool, ERepo


class IPoolFactory(PoolFactory[Pool]):
    __instance_pool: Dict[EPool, Factory[Pool | Callable[..., Pool]]] = {
        EPool.APP_CONFIG_REPO_POOL: IFactory(partial(IRepoPool, e=ERepo.APP_CONFIG_REPO)),
        EPool.SERVER_CONFIG_REPO_POOL: IFactory(partial(IRepoPool, e=ERepo.SERVER_CONFIG_REPO))
    }

    __id = EFactory.POOL

    @classmethod
    def id(cls) -> EFactory: return cls.__id

    @classmethod
    def instance_pool(cls) -> Dict[EPool, Factory[Pool | Callable[..., Pool]]]:
        return cls.__instance_pool
