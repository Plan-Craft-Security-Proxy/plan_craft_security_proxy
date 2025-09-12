
import re
import subprocess
from typing import Any

import psutil
from core.receiver.base import ProxyServerReceiver


class NginxProxyServerReceiver(ProxyServerReceiver):
    def start(self) -> subprocess.Popen:
        return subprocess.Popen(
            [str(self.bin_file_path.absolute())],
            cwd=str(self.cwd.absolute()),
            universal_newlines=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW
        )

    def stop(self) -> Any:
        subprocess.Popen(
            [str(self.bin_file_path.absolute()), '-s', 'stop'],
            cwd=str(self.cwd.absolute()),
            universal_newlines=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW
        )

    def status(self) -> bool:
        """
        代理服务器运行状态
        :return: true正在运行，false已经停止
        """
        with open(self.config_path, 'rt', encoding='utf8') as f:
            config: str = f.read()

        pattern: re.Pattern = re.compile(
            r'listen\s+([0-9]+)',
            re.MULTILINE | re.DOTALL
        )

        obj_searched = pattern.search(config)
        if obj_searched:
            port = int(obj_searched.group(1))
            pids = {
                conn.pid
                for conn in psutil.net_connections('all')
                if conn.status == psutil.CONN_LISTEN and conn.laddr.port == port
            }
            return len(pids) != 0
        raise RuntimeError('没有读取到nginx的配置文件')