import abc

from common import EServerState, EServerAction


class ServerException(Exception, abc.ABC): 
    def __init__(self, message: str):
        super().__init__(message)
        
class IllegalActionException(ServerException):
    
    def __init__(
            self,
            server_state: EServerState,
            action: EServerAction
    ):
        msg: str = f'非法行为：当前服务器的状态为{server_state.value}，意图进行的操作为{action.value}'
        super().__init__(msg)

class ServerTimeoutException(ServerException):

    def __init__(self, time_wait: int, time_waited: int):
        msg: str = f'超时，设定等待时间为：{time_wait}s，已等待时间为：{time_waited}s'
        super().__init__(msg)