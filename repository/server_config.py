from common import EModel, ERepoDatasource
from model import ServerConfig
from .base import IRepository


class IServerConfigRepo(IRepository[ServerConfig]):
    def __init__(
            self,
            repo_datasource: ERepoDatasource = ERepoDatasource.LOCAL_JSON_FILE,
            *args,
            **kwargs
    ):
        super().__init__(repo_datasource, EModel.SERVER_CONFIG, *args, **kwargs)