import abc
from typing import Annotated

from pydantic import BaseModel, Field, FilePath

from common import EServer


class ServerConfig(BaseModel):

    id: Annotated[
        str,
        Field(title='id')
    ]

    server: Annotated[
        EServer,
        Field(title='服务器类型')
    ]

    bin: Annotated[
        FilePath,
        Field(title='可执行文件路径')
    ]

    conf: Annotated[
        FilePath,
        Field(title='配置文件路径')
    ]

    time_wait: Annotated[
        int,
        Field(title='超时时间')
    ]
