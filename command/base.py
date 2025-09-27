import abc
from typing import Annotated, Any
from pydantic import BaseModel, Field
from core import Core

class Command(BaseModel, abc.ABC):

    core: Annotated[
        Core | None,
        Field(title='内核', default=None),
    ]

    @abc.abstractmethod
    def execute(self) -> Any: raise NotImplementedError