from common import ERepo, EFactory
from repository import PRepository
from .base import IPool

class IRepoPool(IPool[PRepository]):
    def __init__(
            self,
            size: int = 1,
            block: bool = True,
            time_wait: float = 5,
            auto_get: bool = True,
            e: ERepo = ERepo.APP_CONFIG_REPO,
            *args,
            **kwargs
    ):
        super().__init__(size, block, time_wait, auto_get, EFactory.REPO, *[e, *args], **kwargs)

