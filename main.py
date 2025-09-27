from bootstrap import Bootstrap
from common import EServerAction

"""
author: mortal
dt: 2025-09-24
version: 0.1.4
"""

if __name__ == '__main__':
    b = Bootstrap()
    while True:
        print('要干嘛？')
        print('1. 启动')
        print('2. 停止')
        print('3. 重启')
        print('4. 当前状态')
        print('5. 退出，会自动关闭当前已启动的代理服务器')
        try:
            choice: int = int(input('输入你的选择（序号）: '))
            match choice:
                case 1:
                    b.run(EServerAction.STARTUP)
                case 2:
                    b.run(EServerAction.SHUTDOWN)
                case 3:
                    b.run(EServerAction.REBOOT)
                case 4:
                    b.run(EServerAction.EMPTY)
                case 5:
                    b.run(EServerAction.SHUTDOWN)
                    break
        except:
            print('输序号啊！！！！！！')
