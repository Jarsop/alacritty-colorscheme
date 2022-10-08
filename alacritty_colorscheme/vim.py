from os import listdir, environ
from os import stat
from os.path import isdir, join
from pynvim import attach
from stat import S_ISSOCK


def template_vimrc_background(colorscheme: str) -> str:
    colorscheme = colorscheme.strip("-256")
    command = (
        f"if !exists('g:colors_name') || g:colors_name != '{colorscheme}'\n"
        f"  colorscheme {colorscheme}\n"
        "endif")
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


def _reload(instance, colorscheme_file):
    nvim = attach('socket', path=instance)
    nvim.command(f'source {colorscheme_file}')


def reload_neovim_sessions(colorscheme_file):
    instances = _get_all_instances()
    try:
        for instance in instances:
            _reload(instance, colorscheme_file)
    except Exception:
        print('Failed loading colorscheme to nvim')
