from collections.abc import Callable
from typing import Dict
from .base import Factory, IFactory, PoolFactory
from common import ECore, EFactory
from core import PCore, IV2flyCore, INginxCore, EmptyCore


class ICoreFactory(PoolFactory[PCore]):
    __instance_pool: Dict[ECore, Factory[PCore | Callable[..., PCore]]] = {
        ECore.V2FLY: IFactory(IV2flyCore),
        ECore.NGINX: IFactory(INginxCore),
        ECore.EMPTY: IFactory(EmptyCore),
    }

    __id = EFactory.CORE

    @classmethod
    def id(cls) -> EFactory: return cls.__id

    @classmethod
    def instance_pool(cls) -> Dict[ECore, Factory[PCore | Callable[..., PCore]]]:
        return cls.__instance_pool
