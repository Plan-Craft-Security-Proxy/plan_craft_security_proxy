from common import EModel, ERepoDatasource
from model import AppConfig
from .base import IRepository


class IAppConfigRepo(IRepository[AppConfig]):
    def __init__(
            self,
            repo_datasource: ERepoDatasource = ERepoDatasource.LOCAL_JSON_FILE,
            *args,
            **kwargs
    ):
        super().__init__(repo_datasource, EModel.APP_CONFIG, *args, **kwargs)