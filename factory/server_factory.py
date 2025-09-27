from collections.abc import Callable
from typing import Dict

from server import Server, IV2flyServer, INginxServer, Cluster
from .base import Factory, IFactory, PoolFactory
from common import EFactory, EServer


class IServerFactory(PoolFactory[Server | Cluster]):
    __instance_pool: Dict[EServer, Factory[Server | Callable[..., Server]]] = {
        EServer.V2FLY: IFactory(IV2flyServer),
        EServer.NGINX: IFactory(INginxServer),
        EServer.CLUSTER: IFactory(Cluster),
    }

    __id = EFactory.SERVER

    @classmethod
    def id(cls) -> EFactory: return cls.__id

    @classmethod
    def instance_pool(cls) -> Dict[EServer, Factory[Server | Callable[..., Server]]]:
        return cls.__instance_pool
