"""Qt4's FreeType plugin is unusable on Windows, so use this hack. MacType will hook
Windows text rendering functions and use FreeType to render them."""
import ctypes
from hazama import config
from os import path


dllPath = path.join(config.appPath, r'lib\MacType.dll')
configPath = path.join(config.appPath, r'lib\mactype.ini')
_handle = _dll = None


def isUsable():
    return config.isWin and path.isfile(dllPath)


def enable():
    global _handle, _dll
    if not isUsable():
        return False
    # it will hook windows rendering functions on loading
    _handle = ctypes.windll.kernel32.LoadLibraryW(dllPath)
    if _handle == 0:
        return False
    _dll = ctypes.WinDLL(None, handle=_handle)
    return True


def isEnabled():
    return bool(_dll)


def fromConfig(s):
    # Qt will cache many glyphs, I don't know how to clear the cache.
    # So this function is actually useless
    try:
        _dll.ReloadConfigStr(s)
    except AttributeError:  # this function is unofficial
        pass


def disable():
    global _handle, _dll
    if _dll is None:
        return
    ctypes.windll.kernel32.FreeLibrary(_handle)
    _handle = _dll = None
