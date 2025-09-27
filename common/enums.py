from enum import Enum

class ECore(Enum):
    V2FLY = 'v2fly'
    NGINX = 'nginx'
    EMPTY = 'empty'

class EServer(Enum):
    V2FLY = 'v2fly'
    NGINX = 'nginx'
    CLUSTER = 'cluster'


class ECoreStatus(Enum):
    RUN = 'run'
    STOP = 'stop'
    # 半挂状态
    SEMI = 'semi'

class EServerState(Enum):
    INIT = 'init'
    SEMI_RUN = 'semi_run'
    RUN = 'run'
    SEMI_STOP = 'semi_stop'
    STOP = 'stop'

    # cluster
    CHAOS = 'chaos'

class ECoreCommand(Enum):
    START = 'start'
    STOP = 'stop'
    STATUS = 'status'
    VERSION = 'version'
    PORT = 'port'

class EServerAction(Enum):
    STARTUP = 'startup'
    SHUTDOWN = 'shutdown'
    REBOOT = 'reboot'
    EMPTY = 'empty'

class EFactory(Enum):
    CORE = 'core'
    SERVER = 'server'
    COMMAND = 'command'
    MODEL = 'model'
    REPO = 'repo'
    POOL = 'pool'
    LOGGER = 'logger'

class EApp(Enum):
    APP_FULL_NAME = 'Plain Craft Security Proxy'
    APP_SHORT_NAME = 'PCSP'
    APP_VERSION = '0.1.4'

class ELoggerLevel(Enum):
    INFO = 'info'
    DEBUG = 'debug'
    WARN = 'warn'
    ERROR = 'error'

class ELoggerHandler(Enum):
    CONSOLE = 'console'
    FILE = 'file'

class EModel(Enum):
    CONSOLE_LOGGER_CONFIG = 'console_logger_config'
    FILE_LOGGER_CONFIG = 'file_logger_config'
    APP_CONFIG = 'app_config'
    SERVER_CONFIG = 'server_config'

class ERepoDatasource(Enum):
    LOCAL_JSON_FILE = 'local_json_file'

class ERepo(Enum):
    APP_CONFIG_REPO = 'app_config_repo'
    SERVER_CONFIG_REPO = 'server_config_repo'

class EPool(Enum):
    APP_CONFIG_REPO_POOL = 'app_config_repo_pool'
    SERVER_CONFIG_REPO_POOL = 'server_config_repo_pool'

class ELogger(Enum):
    DEFAULT_LOGGER = 'default_logger'
