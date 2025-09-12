import abc
import subprocess
from typing import Any
from common import Subject, Observer
from core.command import ProxyServerCommand
from core.invoker import ProxyServerInvoker
from core.receiver import ProxyServerReceiver
from enum import Enum
import weakref

class ProxyServerReceiverAction(Enum):
    START = 'start'
    STOP = 'stop'
    STATUS = 'status'


class ProxyServerReceiverState(abc.ABC):

    # 防止子类不断创建，消耗内存
    _pool: weakref.WeakValueDictionary = weakref.WeakValueDictionary()

    def __new__(cls):
        # If the object exists in the pool - just return it
        obj = cls._pool.get(cls.state())
        # otherwise - create new one (and add it to the pool)
        if obj is None:
            obj = object.__new__(cls)
            cls._pool[cls.state()] = obj
        return obj

    @classmethod
    @abc.abstractmethod
    def state(cls) -> str: raise NotImplementedError

    def __hash__(self): return hash(self.state())

    def __eq__(self, other):
        if other is None:
            return False
        return self.state() == other.state()

    @abc.abstractmethod
    def update(
            self,
            proxy_server_client: 'ProxyServerClient',
            action: ProxyServerReceiverAction
    ) -> Any: raise NotImplementedError

class ProxyServerReceiverInitState(ProxyServerReceiverState):
    @classmethod
    def state(cls) -> str:
        return 'init'

    def update(self, proxy_server_client: 'ProxyServerClient', action: ProxyServerReceiverAction) -> Any:
        if action == ProxyServerReceiverAction.START:
            proxy_server_client.state = ProxyServerReceiverRunBusyState()
            return proxy_server_client.start()
        elif action == ProxyServerReceiverAction.STATUS:
            status = proxy_server_client.status()
            proxy_server_client.state = ProxyServerReceiverRunState() if status else ProxyServerReceiverTerminatedState()
            return status
        raise NotImplementedError

class ProxyServerReceiverRunState(ProxyServerReceiverState):
    @classmethod
    def state(cls) -> str:
        return 'run'

    def update(self, proxy_server_client: 'ProxyServerClient', action: ProxyServerReceiverAction) -> Any:
        if action == ProxyServerReceiverAction.STOP:
            proxy_server_client.state = ProxyServerReceiverTerminateBusyState()
            return proxy_server_client.stop()
        elif action == ProxyServerReceiverAction.STATUS:
            status = proxy_server_client.status()
            proxy_server_client.state = ProxyServerReceiverRunState() if status else ProxyServerReceiverTerminatedState()
            return status
        raise NotImplementedError

class ProxyServerReceiverRunBusyState(ProxyServerReceiverState):
    @classmethod
    def state(cls) -> str:
        return 'run_busy'

    def update(self, proxy_server_client: 'ProxyServerClient', action: ProxyServerReceiverAction) -> Any:
        if action == ProxyServerReceiverAction.STATUS:
            status: bool = proxy_server_client.status()
            proxy_server_client.state = ProxyServerReceiverRunState() if status else ProxyServerReceiverRunBusyState()
            return status
        raise NotImplementedError

class ProxyServerReceiverTerminateBusyState(ProxyServerReceiverState):
    @classmethod
    def state(cls) -> str:
        return 'terminate_busy'

    def update(self, proxy_server_client: 'ProxyServerClient', action: ProxyServerReceiverAction) -> Any:
        if action == ProxyServerReceiverAction.STATUS:
            status: bool = proxy_server_client.status()
            proxy_server_client.state = ProxyServerReceiverTerminateBusyState() if status else ProxyServerReceiverTerminatedState()
            return status
        raise NotImplementedError


class ProxyServerReceiverTerminatedState(ProxyServerReceiverState):
    @classmethod
    def state(cls) -> str:
        return 'terminated'

    def update(self, proxy_server_client: 'ProxyServerClient', action: ProxyServerReceiverAction) -> Any:
        if action == ProxyServerReceiverAction.STATUS:
            status = proxy_server_client.status()
            proxy_server_client.state = ProxyServerReceiverRunState() if status else ProxyServerReceiverTerminatedState()
            return status
        elif action == ProxyServerReceiverAction.START:
            proxy_server_client.state = ProxyServerReceiverRunBusyState()
            return proxy_server_client.start()
        raise NotImplementedError



class ProxyServerClient(Subject, abc.ABC):

    def __init__(self):
        super().__init__()
        self.state: ProxyServerReceiverState = ProxyServerReceiverInitState()


    @property
    @abc.abstractmethod
    def receiver(self) -> ProxyServerReceiver: raise NotImplementedError

    @property
    @abc.abstractmethod
    def invoker(self) -> ProxyServerInvoker: raise NotImplementedError

    @property
    @abc.abstractmethod
    def start_cmd(self) -> ProxyServerCommand: raise NotImplementedError

    @property
    @abc.abstractmethod
    def stop_cmd(self) -> ProxyServerCommand: raise NotImplementedError

    @property
    @abc.abstractmethod
    def status_cmd(self) -> ProxyServerCommand: raise NotImplementedError

    def status(self) -> bool:
        self.invoker.command = self.status_cmd
        return self.invoker.run()

    def start(self) -> subprocess.Popen:
        self.invoker.command = self.start_cmd
        return self.invoker.run()

    def stop(self) -> None:
        self.invoker.command = self.stop_cmd
        return self.invoker.run()

    def update_state(
            self,
            action: ProxyServerReceiverAction,
            modifier: Observer | None = None,
            *args,
            **kwargs
    ) -> Any:
        old_state = self.state
        self.state.update(self, action)
        if old_state != self.state: self.notify(modifier, *args, **kwargs)
        return self.state