import os
import re
import time
import uuid
import threading
import win32gui
import win32con
import keyboard


class MobaXtermWindowFinder:
    """负责查找 MobaXterm 主窗口和终端子窗口句柄。"""

    @staticmethod
    def find():
        hwnd_main = None

        def enum_main(hwnd, _):
            nonlocal hwnd_main
            if win32gui.GetClassName(hwnd) == "TMobaXtermForm":
                hwnd_main = hwnd
                return False
            return True

        win32gui.EnumWindows(enum_main, None)
        if not hwnd_main:
            return None, None

        term_hwnd = None

        def enum_child(hwnd, _):
            nonlocal term_hwnd
            cls = win32gui.GetClassName(hwnd)
            if any(x in cls for x in ("Xterm", "XTerm", "TX")):
                term_hwnd = hwnd
                return False
            return True

        win32gui.EnumChildWindows(hwnd_main, enum_child, None)
        return hwnd_main, term_hwnd


class CommandInjector:
    """负责把命令模拟键盘输入到 MobaXterm 窗口。"""

    def __init__(self, window_finder=None):
        self.window_finder = window_finder or MobaXtermWindowFinder()

    def inject(self, cmd: str):
        hwnd_main, term_hwnd = self.window_finder.find()
        if not hwnd_main:
            raise RuntimeError("未找到 MobaXterm 窗口句柄")

        target = term_hwnd or hwnd_main
        win32gui.ShowWindow(target, win32con.SW_RESTORE)
        win32gui.SetForegroundWindow(target)
        time.sleep(0.1)
        keyboard.write(cmd, delay=0.01)
        time.sleep(0.05)
        keyboard.press_and_release("enter")


class LogTailer:
    """负责持续读取最新日志文件并清洗 ANSI 转义字符。"""

    ANSI_ESCAPE = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')

    def __init__(self, log_dir: str):
        self.log_file = self._find_latest_log(log_dir)
        if not self.log_file:
            raise FileNotFoundError("未找到 .log 文件")
        self._lock = threading.Lock()
        self._lines = []
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._tail, daemon=True)
        self._thread.start()

    def _find_latest_log(self, log_dir: str):
        files = [
            os.path.join(log_dir, f)
            for f in os.listdir(log_dir)
            if f.lower().endswith(".log")
        ]
        return max(files, key=os.path.getmtime) if files else None

    @classmethod
    def _clean_ansi(cls, text: str) -> str:
        return cls.ANSI_ESCAPE.sub('', text)

    def _tail(self):
        with open(self.log_file, 'r', encoding='utf-8', errors='ignore') as f:
            f.seek(0, os.SEEK_END)
            while not self._stop_event.is_set():
                line = f.readline()
                if not line:
                    time.sleep(0.05)
                    continue
                clean = self._clean_ansi(line)
                with self._lock:
                    self._lines.append(clean)

    def read_all(self):
        with self._lock:
            return list(self._lines)

    def clear(self):
        with self._lock:
            self._lines.clear()

    def stop(self):
        self._stop_event.set()
        self._thread.join(timeout=1)


class RemoteShell:
    """对外提供 send_command 方法，用标记截取输出。"""

    def __init__(self, log_dir: str,
                 injector: CommandInjector = None,
                 tailer: LogTailer = None):
        self.injector = injector or CommandInjector()
        self.tailer = tailer or LogTailer(log_dir)

    def send_command(self, cmd: str, timeout: float = 10.0) -> str:
        uid = uuid.uuid4().hex[:8]
        start_marker = f"Agent Mode Start {uid}"
        end_marker = f"Agent Mode End {uid}"

        # 清空旧日志
        self.tailer.clear()

        # 注入标记与命令
        self.injector.inject(f"echo {start_marker}")
        time.sleep(0.1)
        self.injector.inject(cmd)
        time.sleep(0.1)
        self.injector.inject(f"echo {end_marker}")

        # 等待并截取输出
        start_time = time.time()
        started = False
        captured = []

        while True:
            if time.time() - start_time > timeout:
                raise TimeoutError("命令输出等待超时")

            lines = self.tailer.read_all()
            for line in lines:
                if start_marker in line:
                    started = True
                    captured.clear()
                    continue
                if end_marker in line and started:
                    # 过滤标记行并返回
                    output = "".join(captured)
                    clean_lines = [
                        ln for ln in output.splitlines()
                        if ln.strip() and not ln.endswith(start_marker) and not ln.endswith(end_marker)
                    ]
                    return "\n".join(clean_lines).strip()
                if started:
                    captured.append(line)

            time.sleep(0.05)

    def close(self):
        self.tailer.stop()


if __name__ == "__main__":
    shell = RemoteShell(log_dir=r"C:\Users\henry\Desktop")
    try:
        out = shell.send_command("ls -l", timeout=5)
        print("命令输出:\n", out)
    finally:
        shell.close()