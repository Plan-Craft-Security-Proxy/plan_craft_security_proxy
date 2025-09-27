import abc
import time
from typing import Dict, Iterable, Any, List
from command import Command
from common import ECoreCommand, ECoreStatus, EServerState, EServerAction, IllegalActionException, ECore, \
    ServerTimeoutException
from core import PCore
from factory import ICoreFactory, ICommandFactory
from typing import Protocol
from concurrent.futures import ThreadPoolExecutor

class PServerState(Protocol):
    def state(self) -> EServerState: raise NotImplementedError

class Server(abc.ABC):
# class Server:
    def __init__(
            self,
            core: PCore,
            commands: Iterable[ECoreCommand],
            time_wait: int = 5
    ):
        self.__slots: Dict[ECoreCommand, Command] = {
            command: ICommandFactory().create(command, core=core)
            for command in commands
        }
        self.time_wait = time_wait
        self.__state: ServerState = IServerInitState()

    @property
    def state(self) -> EServerState:
        match self.__state:
            case IServerInitState(): return EServerState.INIT
            case IServerSemiRunState(): return EServerState.SEMI_RUN
            case IServerRunState(): return EServerState.RUN
            case IServerSemiStopState(): return EServerState.SEMI_STOP
            case IServerStopState(): return EServerState.STOP
            case IServerChaosState(): return EServerState.CHAOS
            case _: raise NotImplementedError

    @state.setter
    def state(self, value: PServerState):
        self.__state = value

    def execute(self, command: ECoreCommand) -> Any:
        return self.__slots[command].execute()

    @abc.abstractmethod
    def update(self, action: EServerAction) -> EServerState:
        return self.__state.update(self, action)

class Cluster(Server):

    def __init__(
            self
    ):
        super().__init__(ICoreFactory().create(ECore.EMPTY), [], 0)
        self.__servers: Dict[str, Server] = {}

    @property
    def servers(self) -> Dict[str, Server]: return self.__servers

    def execute(self, command: ECoreCommand) -> Any: raise NotImplementedError

    def update(self, action: EServerAction) -> EServerState:
        executor: ThreadPoolExecutor = ThreadPoolExecutor()
        for _, server in self.__servers.items():
            executor.submit(server.update, action)
        executor.shutdown(wait=True)

        state: EServerState | None = None
        for _, server in self.__servers.items():
            if state and state != server.state:
                self.state = IServerChaosState()
                return self.state
            state = server.state

        if state is None:
            self.state = IServerInitState()
        else:
            match state:
                case EServerState.INIT: self.state = IServerInitState()
                case EServerState.SEMI_RUN: self.state = IServerSemiRunState()
                case EServerState.RUN: self.state = IServerRunState()
                case EServerState.SEMI_STOP: self.state = IServerSemiStopState()
                case EServerState.STOP: self.state = IServerStopState()
                case _: raise NotImplementedError
        return self.state

    def register(self, key: str, value: Server):
        self.__servers[key] = value

    def unregister(self, key: str) -> Server:
        server: Server = self.__servers.get(key)
        if server: del self.__servers[key]
        return server

class ServerState(abc.ABC):
    _pool: Dict = {}

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
    def state(cls) -> EServerState: raise NotImplementedError

    @abc.abstractmethod
    def update(self, server: Server, action: EServerAction) -> EServerState: raise NotImplementedError

class IServerInitState(ServerState):

    __state: EServerState = EServerState.INIT

    @classmethod
    def state(cls) -> EServerState: return cls.__state

    def update(self, server: Server, action: EServerAction) -> EServerState:
        """
        支持的动作：
            EServerAction.STARTUP
            EServerAction.SHUTDOWN
            EServerAction.REBOOT
            EServerAction.EMPTY
        """
        core_status: ECoreStatus = server.execute(ECoreCommand.STATUS)
        match action:
            case EServerAction.STARTUP:
                if core_status == ECoreStatus.STOP:
                    server.execute(ECoreCommand.START)
                    server.state = IServerSemiRunState()
                    return server.update(EServerAction.EMPTY)
            case EServerAction.SHUTDOWN:
                if core_status == ECoreStatus.STOP:
                    server.state = IServerStopState()
                    return server.update(EServerAction.EMPTY)
                else:
                    server.state = IServerSemiRunState()
                    return server.update(action)
            case EServerAction.REBOOT:
                server.state = IServerSemiRunState()
                return server.update(action)
            case EServerAction.EMPTY:
                match core_status:
                    case ECoreStatus.STOP: server.state = IServerInitState()
                    case ECoreStatus.RUN: server.state = IServerRunState()
                    case ECoreStatus.SEMI: server.state = IServerSemiRunState()
                return server.state
            case _: raise NotImplementedError

        match core_status:
            case ECoreStatus.STOP:
                server.state = IServerInitState()
                return server.update(action)
            case ECoreStatus.RUN:
                server.state = IServerRunState()
                return server.update(action)
            case ECoreStatus.SEMI:
                server.state = IServerSemiRunState()
                return server.update(action)

class IServerSemiRunState(ServerState):

    __state: EServerState = EServerState.SEMI_RUN

    @classmethod
    def state(cls) -> EServerState: return cls.__state

    def update(self, server: Server, action: EServerAction) -> EServerState:
        """
        支持的动作：
            EServerAction.SHUTDOWN
            EServerAction.REBOOT
            EServerAction.EMPTY
        """
        match action:
            case EServerAction.SHUTDOWN:
                server.execute(ECoreCommand.STOP)
                server.state = IServerSemiStopState()
                return server.update(EServerAction.EMPTY)
            case EServerAction.REBOOT:
                if server.update(EServerAction.SHUTDOWN) == EServerState.STOP:
                    server.execute(ECoreCommand.START)
            case EServerAction.EMPTY:
                pass

        t = time.time()
        while server.time_wait is None or server.time_wait <= 0 or time.time() - t < server.time_wait:
            if server.execute(ECoreCommand.STATUS) == ECoreStatus.RUN:
                server.state = IServerRunState()
                break
        else:
            server.state = IServerStopState() if server.execute(ECoreCommand.STATUS) == ECoreStatus.STOP else self

        time_waited: int = int(time.time() - t)
        if time_waited > server.time_wait:
            raise ServerTimeoutException(server.time_wait, time_waited)

        return server.state

class IServerRunState(ServerState):

    __state: EServerState = EServerState.RUN

    @classmethod
    def state(cls) -> EServerState: return cls.__state

    def update(self, server: Server, action: EServerAction) -> EServerState:
        """
        支持的动作：
            EServerAction.SHUTDOWN
            EServerAction.REBOOT
            EServerAction.EMPTY
        """
        match action:
            case EServerAction.SHUTDOWN:
                server.execute(ECoreCommand.STOP)
                server.state = IServerSemiStopState()
                return server.update(EServerAction.EMPTY)
            case EServerAction.REBOOT:
                if server.update(EServerAction.SHUTDOWN) == EServerState.STOP:
                    server.execute(ECoreCommand.START)
                    server.state = IServerSemiRunState()
                    return server.update(EServerAction.EMPTY)
            case EServerAction.EMPTY:
                return self.state()

        raise IllegalActionException(server.state, action)


class IServerSemiStopState(ServerState):

    __state: EServerState = EServerState.SEMI_STOP

    @classmethod
    def state(cls) -> EServerState: return cls.__state

    def update(self, server: Server, action: EServerAction) -> EServerState:
        """
        支持的动作：
            EServerAction.SHUTDOWN
            EServerAction.REBOOT
            EServerAction.EMPTY
        """
        match action:
            case EServerAction.SHUTDOWN:
                server.execute(ECoreCommand.STOP)
                return server.update(EServerAction.EMPTY)
            case EServerAction.REBOOT:
                if server.update(EServerAction.SHUTDOWN) == EServerState.STOP:
                    server.execute(ECoreCommand.START)
            case EServerAction.EMPTY:
                pass

        t = time.time()
        while server.time_wait is None or server.time_wait <= 0 or time.time() - t < server.time_wait:
            if server.execute(ECoreCommand.STATUS) == ECoreStatus.STOP:
                server.state = IServerStopState()
                break
        else:
            server.state = IServerRunState() if server.execute(ECoreCommand.STATUS) == ECoreStatus.RUN else self

        time_waited: int = int(time.time() - t)
        if time_waited > server.time_wait:
            raise ServerTimeoutException(server.time_wait, time_waited)

        return server.state

class IServerStopState(ServerState):

    __state: EServerState = EServerState.STOP

    @classmethod
    def state(cls) -> EServerState: return cls.__state

    def update(self, server: Server, action: EServerAction) -> EServerState:
        """
        支持的动作：
            EServerAction.STARTUP
            EServerAction.SHUTDOWN
            EServerAction.REBOOT
            EServerAction.EMPTY
        """
        if action == EServerAction.EMPTY: return self.state()
        server.state = IServerInitState()
        return server.update(action)

class IServerChaosState(ServerState):

    __state: EServerState = EServerState.CHAOS

    @classmethod
    def state(cls) -> EServerState: return cls.__state

    def update(self, server: Server, action: EServerAction) -> EServerState:
        """
        支持的动作：
            EServerAction.SHUTDOWN
            EServerAction.REBOOT
            EServerAction.EMPTY
        """
        if action == EServerAction.EMPTY: return self.state()
        elif action in (EServerAction.SHUTDOWN, EServerAction.REBOOT):
            server.state = IServerInitState()
            return server.update(action)
        raise IllegalActionException(server.state, action)