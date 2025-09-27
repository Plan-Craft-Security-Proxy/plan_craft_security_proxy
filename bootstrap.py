import sys
from collections.abc import Iterable
from pathlib import Path
from common import EPool, ELogger, Logger, EFactory, EApp, ELoggerLevel, ELoggerHandler, EServer, EServerAction, \
    EServerState
from model import AppConfig, ServerConfig
import utils
from pool import Pool
from art import text2art
import argparse

from server import Cluster, Server


class Bootstrap:

    def __init__(
            self
    ):
        # 全局应用配置
        app_config_repo_pool =  utils.create(
            EFactory.POOL,
            Pool,
            EPool.APP_CONFIG_REPO_POOL,
            file=Path('conf/app.json'),
        )
        with app_config_repo_pool as app_config_repo:
            self.__app_config: AppConfig = app_config_repo.query(None, 0)

        # 日志器
        self.__loggers: Iterable[Logger] = [
            utils.create(EFactory.LOGGER, Logger, ELogger.DEFAULT_LOGGER, f'{logger_config.handler.value}-{EApp.APP_SHORT_NAME.value}', logger_config)
            for logger_config in self.__app_config.log
        ]

        self.__setup()


    def __setup(self):
        self.__hello_world()
        self.__parse_args()
        self.__create_cluster()

    def __hello_world(self):
        utils.log(ELoggerLevel.INFO, f"\n{text2art('Welcome', 'starwars')}" , self.__loggers)
        utils.log(
            ELoggerLevel.INFO,
            f"\n{text2art('  '.join([EApp.APP_SHORT_NAME.value, 'cmd', EApp.APP_VERSION.value]), 'starwars')}",
            self.__loggers
        )

        utils.log(ELoggerLevel.INFO, '日志配置为：', self.__loggers)
        for logger_config in self.__app_config.log:
            if logger_config.handler == ELoggerHandler.CONSOLE:
                utils.log(
                    ELoggerLevel.INFO,
                    ''.join([
                        '日志输出类型: ',
                        '日志输出到控制台; ',
                        '日志输出级别: ',
                        logger_config.level.value
                    ]),
                    self.__loggers
                )
            else:
                utils.log(
                    ELoggerLevel.INFO,
                    ''.join([
                        '日志输出类型: ',
                        '日志输出到文件中; ',
                        '日志输出级别: ',
                        f'{logger_config.level.value}; ',
                        '日志文件路径: ',
                        str(logger_config.file.absolute())
                    ]),
                    self.__loggers
                )

    def __parse_args(self):
        # 命令行参数解析器
        parser = argparse.ArgumentParser(prog=EApp.APP_FULL_NAME.value,)
        parser.add_argument(
            'conf',
            action='store',
            nargs='?',
            const=Path('./conf/default.json'),
            default=Path('./conf/default.json'),
            type=Path,
            help='配置文件路径，不指定则默认为安装目录下：conf/default.json'
        )
        self.__args = parser.parse_args(sys.argv[1:])
        utils.log(ELoggerLevel.INFO, '命令行参数解析成功', self.__loggers)

    def __create_cluster(self):

        utils.log(
            ELoggerLevel.INFO,
            f'读取到的配置文件为：{str(self.__args.conf.absolute())}',
            self.__loggers
        )
        utils.log(ELoggerLevel.INFO, '实例化配置对象中...', self.__loggers)
        # 实例化配置对象
        server_config_repo_pool = utils.create(
            EFactory.POOL,
            Pool,
            EPool.SERVER_CONFIG_REPO_POOL,
            file=self.__args.conf,
        )
        with server_config_repo_pool as server_config_repo:
            server_config: Iterable[ServerConfig] = server_config_repo.query(None, 0)
            self.__cluster: Cluster = utils.create(EFactory.SERVER, Cluster, EServer.CLUSTER)
            for index, config in enumerate(server_config):
                utils.log(ELoggerLevel.INFO, f'实例化第{index + 1}个配置对象', self.__loggers)
                utils.log(ELoggerLevel.INFO, f'代理服务器类型：{config.server.value}', self.__loggers)
                utils.log(ELoggerLevel.INFO, f'代理服务器可执行文件路径为：{str(config.bin.absolute())}', self.__loggers)
                utils.log(ELoggerLevel.INFO, f'代理服务器配置文件路径为：{str(config.conf.absolute())}', self.__loggers)
                utils.log(ELoggerLevel.INFO, f'代理服务器动作超时时间为：{str(config.time_wait)}s', self.__loggers)
                server = utils.create(
                    EFactory.SERVER,
                    Server,
                    config.server,
                    **config.model_dump(include={'bin', 'conf', 'time_wait'})
                )
                utils.log(ELoggerLevel.INFO, f'第{index + 1}个配置对象创建完毕', self.__loggers)
                utils.log(ELoggerLevel.INFO, f'正在注册第{index + 1}个配置对象', self.__loggers)
                self.__cluster.register(config.id, server)
                utils.log(ELoggerLevel.INFO, f'第{index + 1}个配置对象已成功注册', self.__loggers)

    def run(self, action: EServerAction):
        match action:
            case EServerAction.STARTUP:
                utils.log(ELoggerLevel.INFO, '启动中...', self.__loggers)
                state = self.__cluster.update(action)
                if state == EServerState.RUN:
                    utils.log(ELoggerLevel.INFO, '已成功启动', self.__loggers)
                else:
                    utils.log(ELoggerLevel.WARN, '启动失败，请尝试重启选项', self.__loggers)
            case EServerAction.SHUTDOWN:
                utils.log(ELoggerLevel.INFO, '关闭中...', self.__loggers)
                state = self.__cluster.update(action)
                if state == EServerState.STOP:
                    utils.log(ELoggerLevel.INFO, '已成功关闭', self.__loggers)
                else:
                    utils.log(ELoggerLevel.WARN, '关闭失败，当前已经关闭或者关闭失败，请尝试重新关闭', self.__loggers)
            case EServerAction.EMPTY:
                state = self.__cluster.update(action)
                match state:
                    case EServerState.RUN:
                        utils.log(ELoggerLevel.INFO, '当前状态为：正常运行', self.__loggers)
                    case EServerState.STOP | EServerState.INIT:
                        utils.log(ELoggerLevel.INFO, '当前状态为：停止运行', self.__loggers)
                    case EServerState.SEMI_RUN | EServerState.SEMI_STOP | EServerState.CHAOS:
                        utils.log(ELoggerLevel.INFO, '当前状态为：忙碌', self.__loggers)
            case EServerAction.REBOOT:
                for _ac in [EServerAction.SHUTDOWN, EServerAction.STARTUP]:
                    self.run(_ac)

            case _: raise NotImplementedError