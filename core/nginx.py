import re
import subprocess
from typing import Iterable, Any, Dict, List
import psutil
from common import ECoreStatus
from .base import Core


class INginxCore(Core):
    def start(self) -> None:
        subprocess.Popen(
            [str(self.bin.absolute())],
            cwd=str(self.bin.parent.absolute()),
            universal_newlines=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW
        )

    def stop(self) -> None:
        subprocess.Popen(
            [str(self.bin.absolute()), '-s', 'stop'],
            cwd=str(self.bin.parent.absolute()),
            universal_newlines=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW
        )

    def status(self) -> ECoreStatus:
        listen_num: int = len({
            conn.laddr.port
            for conn in psutil.net_connections(kind='all')
            if conn.laddr.port in self.port() and conn.status == psutil.CONN_LISTEN
        })
        status: ECoreStatus
        if listen_num == len(list(self.port())): status = ECoreStatus.RUN
        elif listen_num > 0: status = ECoreStatus.SEMI
        else: status = ECoreStatus.STOP
        return status

    def version(self) -> str:
        version_pattern: re.Pattern = re.compile(r'nginx/([0-9.]+)', re.IGNORECASE)
        p = subprocess.Popen(
            [str(self.bin.absolute()), '-v'],
            cwd=str(self.bin.parent.absolute()),
            universal_newlines=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        return version_pattern.search(''.join(p.stdout.readlines())).group(1)

    def port(self) -> Iterable[int]:
        # 配置文件中注释的正则表达式
        comment_pattern: re.Pattern = re.compile(r'#.*')
        port_patterns: List[re.Pattern] = [
            re.compile(r'listen.+:([0-9]+)'),
            re.compile(r'listen\s+([0-9]+)')
        ]

        with open(self.conf, 'r', encoding='utf8') as config:
            for line in config:
                # 删除一行中的所有注释
                line: str = comment_pattern.sub('', line)

                # 提取端口号
                for port_pattern in port_patterns:
                    obj = port_pattern.search(line)
                    if obj:
                        yield int(obj.group(1))
                        break
