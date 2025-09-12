import abc
from typing import Any, Callable, Tuple, List, Dict

from common import Observer


class UiViewer(Observer, abc.ABC):
    def __init__(
            self,
            **attrs: Any
    ) -> None:
        self.__dict__.update(attrs)

    def clone(self, **attrs: Any) -> 'UiViewer':
        """Clone a prototype and update inner attributes dictionary"""
        # Python in Practice, Mark Summerfield
        # copy.deepcopy can be used instead of next line.
        obj = self.__class__(**self.__dict__)
        obj.__dict__.update(attrs)
        return obj

    @abc.abstractmethod
    def update(self, *args, **kwargs) -> None: raise NotImplementedError


class CallbackUiViewer(UiViewer):
    def __init__(
            self,
            **callback: Tuple[Callable, List[Any], Dict[str, Any]]
    ):
        """
        :param callback: Ui回调函数
        """
        super().__init__(**callback)
        print()


    def update(self, *args, **kwargs) -> None:
        # 依次调用每一个注册的回调函数
        for name, (c, position, keyword) in self.__dict__.items():
            c(*position, **keyword)
