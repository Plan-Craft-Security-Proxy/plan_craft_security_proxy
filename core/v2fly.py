import json
import os
import re
import signal
import subprocess
from typing import Iterable, Any, Dict
import psutil
import asyncio
from common import ECoreStatus
from .base import Core

class IV2flyCore(Core):

    def start(self) -> None:
        subprocess.Popen(
            [str(self.bin.absolute()), 'run', '-c', str(self.conf.absolute())],
            cwd=str(self.bin.parent.absolute()),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW
        )

    def stop(self) -> None:
        async def __stop(pid: int) -> None:
            os.kill(pid, signal.SIGTERM)

        async def _wrapper() -> None:
            await asyncio.gather(*[
                asyncio.create_task(__stop(pid))
                for pid in {
                    conn.pid
                    for conn in psutil.net_connections(kind='all')
                    if conn.laddr.port in self.port() and conn.status == psutil.CONN_LISTEN
                }
            ])

        asyncio.run(_wrapper())

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
        version_pattern: re.Pattern = re.compile(r'v2ray\s+([0-9.]+)', re.IGNORECASE)
        p = subprocess.Popen(
            [str(self.bin.absolute()), 'version'],
            cwd=str(self.bin.parent.absolute()),
            universal_newlines=True,
            stdout=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        return version_pattern.search(''.join(p.stdout.readlines())).group(1)

    def port(self) -> Iterable[int]:
        with open(self.conf, 'r', encoding='utf8') as f:
            config: Dict[str, Any] = json.load(f)
        yield from [inbound['port'] for inbound in config['inbounds']]