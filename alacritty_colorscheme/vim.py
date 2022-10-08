from ctypes import c_long, pythonapi, py_object
from os import listdir, environ
from os import stat
from os.path import isdir, join
from pynvim import attach
import queue
from stat import S_ISSOCK
import sys
import threading


class NvimCommand(threading.Thread):
    def __init__(self, instance: str, colorscheme: str, timeout=2):
        self.timeout = timeout
        self.exc: queue.Queue = queue.Queue(maxsize=1)
        super().__init__(
            target=self._reload,
            args=(self.exc, instance, colorscheme),
            daemon=True,
        )
        self.start()
        self.wait_or_kill()

    @staticmethod
    def _reload(exc: queue.Queue, instance: str, colorscheme_file: str):
        try:
            nvim = attach("socket", path=instance)
            nvim.command(f"source {colorscheme_file}")
        except:
            exc.put(sys.exc_info())

    def wait_or_kill(self):
        self.join(self.timeout)
        if self.is_alive():
            self.raise_exception()
        else:
            try:
                exc_type, exc_obj, exc_trace = self.exc.get(False)
                raise exc_obj.with_traceback(exc_trace)
            except queue.Empty:
                pass

    def raise_exception(self):
        res = pythonapi.PyThreadState_SetAsyncExc(
            c_long(self.ident), py_object(SystemExit)
        )
        if res == 0:
            raise RuntimeError("Non existent thread id")
        elif res > 1:
            pythonapi.PyThreadState_SetAsyncExc(thread_id, 0)
            raise RuntimeError("Exception raise failure")
        else:
            raise RuntimeError("Nvim command timeout")


def template_vimrc_background(colorscheme: str) -> str:
    colorscheme = colorscheme.strip("-256")
    command = (
        f"if !exists('g:colors_name') || g:colors_name != '{colorscheme}'\n"
        f"  colorscheme {colorscheme}\n"
        "  call Base16hi('Comment', g:base16_gui09, '', g:base16_cterm09, '', '', '')\n"
        "  call Base16hi('LspSignatureActiveParameter', g:base16_gui05, g:base16_gui03, g:base16_cterm05, g:base16_cterm03, 'bold', '')\n"
        "endif"
    )
    return command


def _get_all_instances():
    instances = []

    tmpdir = environ.get("TMPDIR", "/tmp")

    entries = [f for f in listdir(tmpdir) if f.startswith("nvim")]
    for entry in entries:
        path = join(tmpdir, entry)
        if not isdir(path) and S_ISSOCK(stat(path).st_mode):
            instances.append(path)
        else:
            dc = listdir(path)
            if "0" in dc:
                instance = join(path, "0")
                if not isdir(instance) and S_ISSOCK(stat(instance).st_mode):
                    instances.append(instance)

    return instances


def reload_neovim_sessions(colorscheme_file):
    instances = _get_all_instances()
    for instance in instances:
        try:
            NvimCommand(instance, colorscheme_file)
        except Exception as e:
            print(
                f"Failed loading colorscheme `{colorscheme_file}` to nvim session `{instance}`"
            )
            print(f"Error: {e}")
