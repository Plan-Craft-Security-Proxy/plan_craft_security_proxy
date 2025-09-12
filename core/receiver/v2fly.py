import json
import os
import signal
import subprocess
from typing import Dict, Any, List

import psutil

from core.receiver.base import ProxyServerReceiver


class V2flyProxyServerReceiver(ProxyServerReceiver):

    def start(self) -> subprocess.Popen:
        return subprocess.Popen(
            [str(self.bin_file_path.absolute()), 'run', '-c', str(self.config_path.absolute())],
            cwd=str(self.cwd.absolute()),
            universal_newlines=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW
        )

    def stop(self) -> None:
        with open(self.config_path, 'rt', encoding='utf8') as f:
            config: Dict[str, Any] = json.load(f)
        ports: List[int] = [inbound['port'] for inbound in config['inbounds']]
        pids = {
            conn.pid
            for conn in psutil.net_connections('all')
            if conn.status == psutil.CONN_LISTEN and conn.laddr.port in ports
        }
        for pid in pids:
            os.kill(pid, signal.SIGTERM)

    def status(self) -> bool:
        """
        代理服务器运行状态
        :return: true正在运行，false已经停止
        """
        with open(self.config_path, 'rt', encoding='utf8') as f:
            config: Dict[str, Any] = json.load(f)
        ports: List[int] = [inbound['port'] for inbound in config['inbounds']]
        pids = {
            conn.pid
            for conn in psutil.net_connections('all')
            if conn.status == psutil.CONN_LISTEN and conn.laddr.port in ports
        }
        return len(pids) != 0