import tkinter as tk
from tkinter import scrolledtext
import win32gui
import win32con
import keyboard
import re
import os
import time
import threading

LOG_DIR = r"C:\Users\henry\Desktop"


def find_latest_log_file(log_dir):
    """在给定目录中找到最近修改的 .log 文件"""
    log_files = [os.path.join(log_dir, f) for f in os.listdir(log_dir) if f.lower().endswith(".log")]
    if not log_files:
        return None
    latest_file = max(log_files, key=os.path.getmtime)
    return latest_file


def clean_ansi(line):
    ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')
    return ansi_escape.sub('', line)


def tail_log(path, callback):
    """实时读取日志文件，每一行调用 callback"""
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        f.seek(0, os.SEEK_END)
        while True:
            line = f.readline()
            if not line:
                time.sleep(0.2)
                continue
            callback(clean_ansi(line))


# 找窗口
def find_moba_term_hwnd():
    hwnd_main = None

    def enum_windows_cb(hwnd, extra):
        nonlocal hwnd_main
        cls = win32gui.GetClassName(hwnd)
        if cls == "TMobaXtermForm":  # 主窗口类名
            hwnd_main = hwnd
            return False
        return True

    win32gui.EnumWindows(enum_windows_cb, None)
    if not hwnd_main:
        print("未找到 MobaXterm 主窗口")
        return None, None
    # 找终端控件
    term_hwnd = None

    def enum_child_cb(hwnd, extra):
        nonlocal term_hwnd
        cls = win32gui.GetClassName(hwnd)
        # 打印出来调试
        # print(f"child: {hwnd} {cls}")
        if "Xterm" in cls or "XTerm" in cls or "TX" in cls:
            term_hwnd = hwnd
            return False
        return True

    win32gui.EnumChildWindows(hwnd_main, enum_child_cb, None)
    return hwnd_main, term_hwnd


def find_xshell_hwnd():
    hwnd_main = None

    def enum_windows_cb(hwnd, extra):
        nonlocal hwnd_main
        cls = win32gui.GetClassName(hwnd)
        # 这里替换成你用工具查到的 Xshell 主窗口类名
        if cls == "Xshell8::MainFrame_0":
            hwnd_main = hwnd
            return False  # 找到后停止枚举
        return True

    win32gui.EnumWindows(enum_windows_cb, None)
    if not hwnd_main:
        print("未找到 Xshell 主窗口")
        return None, None
    term_hwnd = None

    def enum_child_cb(hwnd, extra):
        nonlocal term_hwnd
        cls = win32gui.GetClassName(hwnd)
        # 打印调试
        # print(f"child: {hwnd} {cls}")
        if "TextView" in cls or "Afx" in cls or "Xshell" in cls:
            term_hwnd = hwnd
            return False
        return True

    win32gui.EnumChildWindows(hwnd_main, enum_child_cb, None)
    return hwnd_main, term_hwnd


def inject_command_typing(cmd):
    hwnd_main, term_hwnd = find_moba_term_hwnd()
    if not hwnd_main:
        return
    # 激活窗口
    if term_hwnd:
        win32gui.ShowWindow(term_hwnd, win32con.SW_RESTORE)
        win32gui.SetForegroundWindow(term_hwnd)
    else:
        win32gui.ShowWindow(hwnd_main, win32con.SW_RESTORE)
        win32gui.SetForegroundWindow(hwnd_main)
    time.sleep(0.1)  # 等待窗口获得焦点
    # 模拟键入命令
    keyboard.write(cmd, delay=0.03)  # delay=每个字符之间的延迟
    time.sleep(0.05)
    keyboard.press_and_release("enter")


class ChatApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Chat→Shell 简化版 + 日志显示")
        self.geometry("800x600")
        # 日志显示区
        self.log_display = scrolledtext.ScrolledText(self, state="disabled", wrap="word")
        self.log_display.pack(fill="both", expand=True, padx=5, pady=5)
        # 输入区
        frm_input = tk.Frame(self)
        frm_input.pack(fill="x", padx=5, pady=5)
        self.entry_cmd = tk.Entry(frm_input)
        self.entry_cmd.pack(side="left", fill="x", expand=True)
        btn_send = tk.Button(frm_input, text="执行", command=self.on_send)
        btn_send.pack(side="left", padx=5)
        # 日志线程引用
        self.log_thread = None
        self.current_log_file = None

    def append_log_line(self, line):
        self.log_display.configure(state="normal")
        self.log_display.insert("end", line)
        self.log_display.see("end")
        self.log_display.configure(state="disabled")

    def start_log_monitor(self):
        """启动最新log文件的监视线程"""
        latest_log = find_latest_log_file(LOG_DIR)
        if not latest_log:
            self.append_log_line("[系统] 未找到 log 文件\n")
            return
        self.current_log_file = latest_log
        self.append_log_line(f"[系统] 正在监视: {latest_log}\n")

        def worker():
            tail_log(latest_log, lambda line: self.after(0, lambda: self.append_log_line(line)))

        self.log_thread = threading.Thread(target=worker, daemon=True)
        self.log_thread.start()

    def on_send(self):
        cmd = self.entry_cmd.get().strip()
        if not cmd:
            return
        self.entry_cmd.delete(0, "end")
        threading.Thread(target=self.exec_cmd, args=(cmd,), daemon=True).start()

    def exec_cmd(self, cmd):
        # 在第一次执行命令前启动日志监控
        if not self.log_thread:
            self.start_log_monitor()
        inject_command_typing(cmd)


if __name__ == "__main__":
    app = ChatApp()
    app.mainloop()
