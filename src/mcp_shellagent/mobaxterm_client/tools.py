import os
import re
import time
import uuid
import threading
from pywinauto import Application, findwindows
from pywinauto.keyboard import send_keys
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="pywinauto.application")

class MobaXtermWindowFinder:
    def __init__(self, exe_path=None):
        self.exe_path = exe_path
        self.app = None

    def connect(self):
        if self.exe_path and os.path.exists(self.exe_path):
            self.app = Application(backend="win32").start(self.exe_path)
        else:
            hwnds = findwindows.find_windows(class_name="TMobaXtermForm")
            if not hwnds:
                raise RuntimeError("未找到 MobaXterm 窗口")
            self.app = Application(backend="win32").connect(handle=hwnds[0])

    def get_terminal_ctrl(self):
        if not self.app:
            self.connect()
        main_win = self.app.window(class_name="TMobaXtermForm")
        # 调试控件树
        # main_win.print_control_identifiers()
        return main_win


class CommandInjector:
    """使用 pywinauto 注入命令"""

    def __init__(self, window_finder=None):
        self.window_finder = window_finder or MobaXtermWindowFinder()
        self.window_finder.connect()
        self.terminal = self.window_finder.get_terminal_ctrl()

    def inject(self, cmd: str):
        # 聚焦窗口
        self.terminal.set_focus()
        time.sleep(0.01)
        # 输入命令
        send_keys(cmd, with_spaces=True, pause=0.01)  # 保证空格正常输入
        time.sleep(0.01)
        send_keys("{ENTER}")


class LogTailer:
    """持续读取最新日志文件并清洗 ANSI 转义字符。"""

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

    @staticmethod
    def _find_latest_log(log_dir: str):
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
    """对外提供 send_command 方法"""

    def __init__(self, log_dir: str,
                 injector: CommandInjector = None,
                 tailer: LogTailer = None):
        self.injector = injector or CommandInjector()
        self.tailer = tailer or LogTailer(log_dir)

    def send_command(self, cmd: str, timeout: float = 10.0) -> str:
        uid = uuid.uuid4().hex[:8]
        start_marker = f"Agent Mode Start {uid}"
        end_marker = f"Agent Mode End {uid}"

        self.tailer.clear()

        self.injector.inject(f"echo {start_marker}")
        self.injector.inject(cmd)
        self.injector.inject(f"echo {end_marker}")

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
                    output = "".join(captured)
                    clean_lines = [
                        ln for ln in output.splitlines()
                        if ln.strip()
                    ]
                    return "\n".join(clean_lines).strip()
                if started:
                    captured.append(line)

            time.sleep(0.01)

    def close(self):
        self.tailer.stop()


if __name__ == "__main__":
    shell = RemoteShell(log_dir=r"C:\Users\henry\Desktop")
    try:
        out = shell.send_command("ls -l", timeout=5)
        print("命令输出:\n", out)
    finally:
        shell.close()
