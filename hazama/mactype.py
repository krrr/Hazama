"""Qt4 has no FreeType for Windows, so use this hack."""
import ctypes
from hazama import config
from os import path


dllPath = path.join(config.appPath, r'lib\mactype\MacType.dll')
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


def reloadConfig():
    _dll.ReloadConfig()


def disable():
    global _handle, _dll
    if _dll is None:
        return
    ctypes.windll.kernel32.FreeLibrary(_handle)
    _handle = _dll = None
