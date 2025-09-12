import abc
from contextlib import suppress


class Observer(abc.ABC):
    @abc.abstractmethod
    def update(self, *args, **kwargs) -> None: raise NotImplementedError

class Subject(abc.ABC):
    def __init__(self) -> None:
        self._observers: list[Observer] = []

    def attach(self, observer: Observer) -> None:
        if observer not in self._observers:
            self._observers.append(observer)

    def detach(self, observer: Observer) -> None:
        with suppress(ValueError):
            self._observers.remove(observer)

    def notify(self, modifier: Observer | None = None, *args, **kwargs) -> None:
        for observer in self._observers:
            if modifier != observer:
                observer.update(self)