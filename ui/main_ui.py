import json
import threading
import time
import tkinter as tk
from tkinter import font, Frame
import tkinter.filedialog
from pathlib import Path
from tkinter import Event
from typing import Dict, Any, Literal, List
from core.base import V2FLY_BIN_FILE_PATH, NGINX_BIN_FILE_PATH, NGINX_CONFIG_PATH, NGINX_CWD, V2FLY_CWD, V2FLY_CONFIG_PATH
from core.client import V2flyProxyServerClient, NginxProxyServerClient, \
    ProxyServerReceiverInitState, ProxyServerReceiverRunState, ProxyServerReceiverTerminatedState, \
    ProxyServerReceiverAction
import win32api, win32con, win32gui_struct, win32gui
import os

from core.client.base import ProxyServerReceiverRunBusyState, ProxyServerReceiverState, \
    ProxyServerReceiverTerminateBusyState, ProxyServerClient
from ui import CallbackUiViewer


class SysTrayIcon(object):
    '''SysTrayIcon类用于显示任务栏图标'''
    QUIT = 'QUIT'
    SPECIAL_ACTIONS = [QUIT]
    FIRST_ID = 5320

    def __init__(s, icon, hover_text, menu_options, on_quit, tk_window=None, default_menu_index=None,
                 window_class_name=None):
        '''
        icon         需要显示的图标文件路径
        hover_text   鼠标停留在图标上方时显示的文字
        menu_options 右键菜单，格式: (('a', None, callback), ('b', None, (('b1', None, callback),)))
        on_quit      传递退出函数，在执行退出时一并运行
        tk_window    传递Tk窗口，s.root，用于单击图标显示窗口
        default_menu_index 不显示的右键菜单序号
        window_class_name  窗口类名
        '''
        s.icon = icon
        s.hover_text = hover_text
        s.on_quit = on_quit
        s.root = tk_window

        menu_options = menu_options + (('退出', None, s.QUIT),)
        s._next_action_id = s.FIRST_ID
        s.menu_actions_by_id = set()
        s.menu_options = s._add_ids_to_menu_options(list(menu_options))
        s.menu_actions_by_id = dict(s.menu_actions_by_id)
        del s._next_action_id

        s.default_menu_index = (default_menu_index or 0)
        s.window_class_name = window_class_name or "SysTrayIconPy"

        message_map = {win32gui.RegisterWindowMessage("TaskbarCreated"): s.restart,
                       win32con.WM_DESTROY: s.destroy,
                       win32con.WM_COMMAND: s.command,
                       win32con.WM_USER + 20: s.notify, }
        # 注册窗口类。
        wc = win32gui.WNDCLASS()
        wc.hInstance = win32gui.GetModuleHandle(None)
        wc.lpszClassName = s.window_class_name
        wc.style = win32con.CS_VREDRAW | win32con.CS_HREDRAW;
        wc.hCursor = win32gui.LoadCursor(0, win32con.IDC_ARROW)
        wc.hbrBackground = win32con.COLOR_WINDOW
        wc.lpfnWndProc = message_map  # 也可以指定wndproc.
        s.classAtom = win32gui.RegisterClass(wc)

    def activation(s):
        '''激活任务栏图标，不用每次都重新创建新的托盘图标'''
        hinst = win32gui.GetModuleHandle(None)  # 创建窗口。
        style = win32con.WS_OVERLAPPED | win32con.WS_SYSMENU
        s.hwnd = win32gui.CreateWindow(s.classAtom,
                                       s.window_class_name,
                                       style,
                                       0, 0,
                                       win32con.CW_USEDEFAULT,
                                       win32con.CW_USEDEFAULT,
                                       0, 0, hinst, None)
        win32gui.UpdateWindow(s.hwnd)
        s.notify_id = None
        s.refresh(title='软件已后台！', msg='点击重新打开', time=500)

        win32gui.PumpMessages()

    def refresh(s, title='', msg='', time=500):
        '''刷新托盘图标
           title 标题
           msg   内容，为空的话就不显示提示
           time  提示显示时间'''
        hinst = win32gui.GetModuleHandle(None)
        if os.path.isfile(s.icon):
            icon_flags = win32con.LR_LOADFROMFILE | win32con.LR_DEFAULTSIZE
            hicon = win32gui.LoadImage(hinst, s.icon, win32con.IMAGE_ICON,
                                       0, 0, icon_flags)
        else:  # 找不到图标文件 - 使用默认值
            hicon = win32gui.LoadIcon(0, win32con.IDI_APPLICATION)

        if s.notify_id:
            message = win32gui.NIM_MODIFY
        else:
            message = win32gui.NIM_ADD

        s.notify_id = (s.hwnd, 0,  # 句柄、托盘图标ID
                       win32gui.NIF_ICON | win32gui.NIF_MESSAGE | win32gui.NIF_TIP | win32gui.NIF_INFO,
                       # 托盘图标可以使用的功能的标识
                       win32con.WM_USER + 20, hicon, s.hover_text,  # 回调消息ID、托盘图标句柄、图标字符串
                       msg, time, title,  # 提示内容、提示显示时间、提示标题
                       win32gui.NIIF_INFO  # 提示用到的图标
                       )
        win32gui.Shell_NotifyIcon(message, s.notify_id)

    def show_menu(s):
        '''显示右键菜单'''
        menu = win32gui.CreatePopupMenu()
        s.create_menu(menu, s.menu_options)

        pos = win32gui.GetCursorPos()
        win32gui.SetForegroundWindow(s.hwnd)
        win32gui.TrackPopupMenu(menu,
                                win32con.TPM_LEFTALIGN,
                                pos[0],
                                pos[1],
                                0,
                                s.hwnd,
                                None)
        win32gui.PostMessage(s.hwnd, win32con.WM_NULL, 0, 0)

    def _add_ids_to_menu_options(s, menu_options):
        result = []
        for menu_option in menu_options:
            option_text, option_icon, option_action = menu_option
            if callable(option_action) or option_action in s.SPECIAL_ACTIONS:
                s.menu_actions_by_id.add((s._next_action_id, option_action))
                result.append(menu_option + (s._next_action_id,))
            else:
                result.append((option_text,
                               option_icon,
                               s._add_ids_to_menu_options(option_action),
                               s._next_action_id))
            s._next_action_id += 1
        return result

    def restart(s, hwnd, msg, wparam, lparam):
        s.refresh()

    def destroy(s, hwnd=None, msg=None, wparam=None, lparam=None, exit=1):
        nid = (s.hwnd, 0)
        win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, nid)
        win32gui.PostQuitMessage(0)  # 终止应用程序。
        if exit and s.on_quit:
            s.on_quit()  # 需要传递自身过去时用 s.on_quit(s)
        else:
            s.root.deiconify()  # 显示tk窗口

    def notify(s, hwnd, msg, wparam, lparam):
        '''鼠标事件'''
        if lparam == win32con.WM_LBUTTONDBLCLK:  # 双击左键
            pass
        elif lparam == win32con.WM_RBUTTONUP:  # 右键弹起
            s.show_menu()
        elif lparam == win32con.WM_LBUTTONUP:  # 左键弹起
            s.destroy(exit=0)
        return True
        """
        可能的鼠标事件：
          WM_MOUSEMOVE      #光标经过图标
          WM_LBUTTONDOWN    #左键按下
          WM_LBUTTONUP      #左键弹起
          WM_LBUTTONDBLCLK  #双击左键
          WM_RBUTTONDOWN    #右键按下
          WM_RBUTTONUP      #右键弹起
          WM_RBUTTONDBLCLK  #双击右键
          WM_MBUTTONDOWN    #滚轮按下
          WM_MBUTTONUP      #滚轮弹起
          WM_MBUTTONDBLCLK  #双击滚轮
        """

    def create_menu(s, menu, menu_options):
        for option_text, option_icon, option_action, option_id in menu_options[::-1]:
            if option_icon:
                option_icon = s.prep_menu_icon(option_icon)

            if option_id in s.menu_actions_by_id:
                item, extras = win32gui_struct.PackMENUITEMINFO(text=option_text,
                                                                hbmpItem=option_icon,
                                                                wID=option_id)
                win32gui.InsertMenuItem(menu, 0, 1, item)
            else:
                submenu = win32gui.CreatePopupMenu()
                s.create_menu(submenu, option_action)
                item, extras = win32gui_struct.PackMENUITEMINFO(text=option_text,
                                                                hbmpItem=option_icon,
                                                                hSubMenu=submenu)
                win32gui.InsertMenuItem(menu, 0, 1, item)

    def prep_menu_icon(s, icon):
        # 加载图标。
        ico_x = win32api.GetSystemMetrics(win32con.SM_CXSMICON)
        ico_y = win32api.GetSystemMetrics(win32con.SM_CYSMICON)
        hicon = win32gui.LoadImage(0, icon, win32con.IMAGE_ICON, ico_x, ico_y, win32con.LR_LOADFROMFILE)

        hdcBitmap = win32gui.CreateCompatibleDC(0)
        hdcScreen = win32gui.GetDC(0)
        hbm = win32gui.CreateCompatibleBitmap(hdcScreen, ico_x, ico_y)
        hbmOld = win32gui.SelectObject(hdcBitmap, hbm)
        brush = win32gui.GetSysColorBrush(win32con.COLOR_MENU)
        win32gui.FillRect(hdcBitmap, (0, 0, 16, 16), brush)
        win32gui.DrawIconEx(hdcBitmap, 0, 0, hicon, ico_x, ico_y, 0, 0, win32con.DI_NORMAL)
        win32gui.SelectObject(hdcBitmap, hbmOld)
        win32gui.DeleteDC(hdcBitmap)

        return hbm

    def command(s, hwnd, msg, wparam, lparam):
        id = win32gui.LOWORD(wparam)
        s.execute_menu_option(id)

    def execute_menu_option(s, id):
        menu_action = s.menu_actions_by_id[id]
        if menu_action == s.QUIT:
            win32gui.DestroyWindow(s.hwnd)
        else:
            menu_action(s)


class _Main:  # 调用SysTrayIcon的Demo窗口
    def __init__(
            self,
    ):
        self.SysTrayIcon = None  # 判断是否打开系统托盘图标
        self.root = MainWindow()

    def main(s):
        s.root.bind("<Unmap>", lambda event: s.Hidden_window(icon=s.root.WINDOW_ICON_PATH, hover_text=s.root.SYS_TRAY_ICO_HOVER_TIP) if s.root.state() == 'iconic' else False)  # 窗口最小化判断，可以说是调用最重要的一步
        s.root.protocol('WM_DELETE_WINDOW', s.exit)  # 点击Tk窗口关闭时直接调用s.exit，不使用默认关闭
        s.root.mainloop()

    def switch_icon(s, _sysTrayIcon, icon='D:\\2.ico'):
        # 点击右键菜单项目会传递SysTrayIcon自身给引用的函数，所以这里的_sysTrayIcon = s.sysTrayIcon
        # 只是一个改图标的例子，不需要的可以删除此函数
        _sysTrayIcon.icon = icon
        _sysTrayIcon.refresh()

        # 气泡提示的例子
        s.show_msg(title='图标更换', msg='图标更换成功！', time=500)

    def show_msg(s, title='标题', msg='内容', time=500):
        s.SysTrayIcon.refresh(title=title, msg=msg, time=time)

    def Hidden_window(s, icon='D:\\1.ico', hover_text="SysTrayIcon.py Demo"):
        '''隐藏窗口至托盘区，调用SysTrayIcon的重要函数'''

        # 托盘图标右键菜单, 格式: ('name', None, callback),下面也是二级菜单的例子
        # 24行有自动添加‘退出’，不需要的可删除
        menu_options = (('一级 菜单', None, s.switch_icon),
                        ('二级 菜单', None, (('更改 图标', None, s.switch_icon),)))

        s.root.withdraw()  # 隐藏tk窗口
        if not s.SysTrayIcon: s.SysTrayIcon = SysTrayIcon(
            icon,  # 图标
            hover_text,  # 光标停留显示文字
            menu_options,  # 右键菜单
            on_quit=s.exit,  # 退出调用
            tk_window=s.root,  # Tk窗口
        )
        s.SysTrayIcon.activation()

    def exit(s, _sysTrayIcon=None):
        s.root.destroy()
        print('exit...')

class MainWindow(tk.Tk):

    def __init__(self):
        super().__init__()
        self.__init_preset()
        self.__init_window_property()
        self.__init_widget()
        self.__init_bind()

    def __init_preset(self):
        # 初始化预设值

        # 初始化提示词
        self.WINDOW_TITLE: str = 'Plain Craft Security Proxy v0.1.2'
        self.HELLO_TIP: str = 'A strange joy is easy, long can tender the most rare'
        self.SYS_TRAY_ICO_HOVER_TIP: str = 'PCSP'
        self.ACT_BTN_INIT_TIP: str = '点我'
        self.ACT_BTN_START_PROXY_TIP: str = '开启代理'
        self.ACT_BTN_STOP_PROXY_TIP: str = '关闭代理'

        # 初始化一些文件读取的路径
        self.WINDOW_ICON_PATH: str = './icon.ico'

        # 初始化代理开启/停止的最长等待时间
        self.PROXY_WAIT_TIMEOUT: int = 5

        # 初始化一些控件属性常量
        self.WINDOW_INIT_SIZE: str = '580x80'
        self.HELLO_LBL_FONT_FAMILY: str = 'Roman'
        self.HELLO_LBL_FONT_SIZE: int = 18
        self.HELLO_LBL_FONT_SLANT: Literal['roman', 'italic'] = 'italic'
        self.HELLO_LBL_FONT_WEIGHT: Literal['normal', 'bold'] = 'bold'
        self.HELLO_LBL_FG: str = '#9932CD'

    def __init_widget(self):
        # 初始化控件

        # hello tip widget
        self.hello_lbl = tk.Label(self, text=self.HELLO_TIP)
        self.hello_lbl.config(font=tk.font.Font(
            family=self.HELLO_LBL_FONT_FAMILY,
            size=self.HELLO_LBL_FONT_SIZE,
            slant=self.HELLO_LBL_FONT_SLANT,
            weight=self.HELLO_LBL_FONT_WEIGHT,
        ), fg=self.HELLO_LBL_FG)
        self.hello_lbl.pack(side='top')

        # 按钮
        self.act_btn = tk.Button(self, text=self.ACT_BTN_INIT_TIP)
        self.act_btn.pack(side='top')

    def __init_window_property(self):
        # 初始化窗口属性

        self.geometry(self.WINDOW_INIT_SIZE)
        self.resizable(0, 0)
        self.title(self.WINDOW_TITLE)
        self.iconbitmap(self.WINDOW_ICON_PATH)

    def __init_bind(self):

        def bind_act_btn(event: Event):
            self.act_btn.config(state='disabled')
            self.act_btn.pack_forget()
            self.attributes('-disabled', 1)

            config = self.callback_load_config()
            self.callback_trigger_proxy_server(event, config)

            self.act_btn.config(state='normal')
            self.act_btn.pack()
            self.attributes('-disabled', 0)


        self.act_btn.bind('<Button-1>', func=lambda event: threading.Thread(target=bind_act_btn, args=(event,)).start())

    @staticmethod
    def callback_load_config() -> Dict[str, Any]:
        """
        回调函数：加载配置文件
        :return: 字典对象
        """
        file = tkinter.filedialog.askopenfilename(
            title='选择文件',
            filetypes=[
                ('config.json', ('*.json',))
            ]
        )

        with open(file, 'rt') as f:
            config: Dict[str, Any] = json.load(f)

        config['v2fly'].setdefault('cwd', V2FLY_CWD)
        config['v2fly'].setdefault('config_path', V2FLY_CONFIG_PATH)
        config['v2fly'].setdefault('bin_file_path', V2FLY_BIN_FILE_PATH)
        config['v2fly']['cwd'] = Path(config['v2fly']['cwd'])
        config['v2fly']['config_path'] = Path(config['v2fly']['cwd']) / config['v2fly']['config_path']
        config['v2fly']['bin_file_path'] = Path(config['v2fly']['cwd']) / config['v2fly']['bin_file_path']

        config['nginx'].setdefault('cwd', NGINX_CWD)
        config['nginx'].setdefault('config_path', NGINX_CONFIG_PATH)
        config['nginx'].setdefault('bin_file_path', NGINX_BIN_FILE_PATH)
        config['nginx']['cwd'] = Path(config['nginx']['cwd'])
        config['nginx']['config_path'] = Path(config['nginx']['cwd']) / config['nginx']['config_path']
        config['nginx']['bin_file_path'] = Path(config['nginx']['cwd']) / config['nginx']['bin_file_path']

        return config

    def callback_trigger_proxy_server(
            self,
            event: Event,
            config: Dict[str, Any]
    ):
        """
        回调函数：触发代理服务器
        :param event: 按钮事件对象
        :param config: 配置对象
        :return: None
        """

        v2fly_client = V2flyProxyServerClient(
            config['v2fly']['bin_file_path'],
            config['v2fly']['config_path'],
            config['v2fly']['cwd'],
        )
        nginx_client = NginxProxyServerClient(
            config['nginx']['bin_file_path'],
            config['nginx']['config_path'],
            config['nginx']['cwd'],
        )

        clients = (v2fly_client, nginx_client)

        def callback_change_tip(*clients: ProxyServerClient):
            status: bool = True
            c = None
            for index, client in enumerate(clients):
                c = client
                t = time.time()
                while client.state in (
                    ProxyServerReceiverInitState(),
                    ProxyServerReceiverRunBusyState(),
                    ProxyServerReceiverTerminateBusyState()
                ) and status:
                    client.update_state(ProxyServerReceiverAction.STATUS)
                    if (t - time.time()) >= self.PROXY_WAIT_TIMEOUT:
                        # 超时
                        status = False
                        if client.state in (
                            ProxyServerReceiverInitState(),
                            ProxyServerReceiverRunBusyState(),
                        ):
                            # 没成功启动全部代理
                            self.act_btn.config(text=self.ACT_BTN_STOP_PROXY_TIP if index > 0 else self.ACT_BTN_START_PROXY_TIP)
                        else:
                            # 没成功关闭全部代理
                            self.act_btn.config(text=self.ACT_BTN_STOP_PROXY_TIP)
                if not status: break
            else:
                if c is None:
                    pass
                elif c.state == ProxyServerReceiverRunState():
                    self.act_btn.config(text=self.ACT_BTN_STOP_PROXY_TIP)
                else:
                    self.act_btn.config(text=self.ACT_BTN_START_PROXY_TIP)

        viewer = CallbackUiViewer(
            act_btn=(
                callback_change_tip,
                [*clients],
                {}
            )
        )

        for client in clients:
            # 将每个viewer进行注册，达到client状态改变时，通知对应的viewer执行回调函数，改变按钮的标签提示
            # 优点：防止一直循环轮询判断，程序不会因为循环导致阻塞
            client.attach(viewer)

        # 如果所有的client的初始状态都处于init状态，则不通过状态检测改变按钮的标签提示
        is_all_init: bool = all([
            client.update_state(ProxyServerReceiverAction.STATUS) == ProxyServerReceiverInitState()
            for client in clients
        ])

        # 如果存在client的初始状态不为init状态，此时只可能是run或者terminated状态，通过状态检测改变按钮的标签提示
        if not is_all_init:
            # 只对初始状态不为init的client通过状态检测改变按钮的标签提示
            callback_change_tip(*[client for client in clients if client.state != ProxyServerReceiverInitState()])

        for client in clients:
            # 程序能够到达这里，说明按钮的标签提示一定是准确的
            # 此时可以根据按钮的标签提示进行相应的启停操作
            if self.act_btn.cget('text') in (self.ACT_BTN_INIT_TIP, self.ACT_BTN_START_PROXY_TIP):
                # 标签提示为：初始化提示/开始提示
                # 点击按钮后的行为应该是开启client
                t = threading.Thread(target=lambda: client.update_state(ProxyServerReceiverAction.START))
            else:
                # 标签提示为：初始化提示/停止提示
                # 点击按钮后的行为应该是关闭client
                t = threading.Thread(target=lambda: client.update_state(ProxyServerReceiverAction.STOP))
            t.start()
            t.join()
