# python version 3.8 required
# requires module tkinter

from sys import stdin as s
from sys import stdout
from sys import argv
import tkinter as tk

# from pyperclip import copy


"""
Pyperclip

A cross-platform clipboard module for Python, with copy & paste functions for plain text.
By Al Sweigart al@inventwithpython.com
"""
__version__ = '1.8.0'

import contextlib
import ctypes
import os
import platform
import subprocess
import time
import warnings

from ctypes import c_size_t, sizeof, c_wchar_p, get_errno, c_wchar

# `import PyQt4` sys.exit()s if DISPLAY is not in the environment.
# Thus, we need to detect the presence of $DISPLAY manually
# and not load PyQt4 if it is absent.
HAS_DISPLAY = os.getenv("DISPLAY", False)

EXCEPT_MSG = """
    Pyperclip could not find a copy/paste mechanism for your system.
    For more information, please visit https://pyperclip.readthedocs.io/en/latest/index.html#not-implemented-error """

ENCODING = 'utf-8'

# The "which" unix command finds where a command is.
if platform.system() == 'Windows':
    WHICH_CMD = 'where'
else:
    WHICH_CMD = 'which'


def _executable_exists(name):
    return subprocess.call([WHICH_CMD, name],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE) == 0


# Exceptions
class PyperclipException(RuntimeError):
    pass


class PyperclipWindowsException(PyperclipException):
    def __init__(self, message):
        message += " (%s)" % ctypes.WinError()
        super(PyperclipWindowsException, self).__init__(message)


class PyperclipTimeoutException(PyperclipException):
    pass


def _stringifyText(text):
    acceptedTypes = (str, int, float, bool)
    if not isinstance(text, acceptedTypes):
        raise PyperclipException(
            'only str, int, float, and bool values can be copied to the clipboard, not %s' % (text.__class__.__name__))
    return str(text)


def init_osx_pbcopy_clipboard():
    def copy_osx_pbcopy(text):
        text = _stringifyText(text)  # Converts non-str values to str.
        p = subprocess.Popen(['pbcopy', 'w'],
                             stdin=subprocess.PIPE, close_fds=True)
        p.communicate(input=text.encode(ENCODING))
    return copy_osx_pbcopy


def init_osx_pyobjc_clipboard():
    def copy_osx_pyobjc(text):
        '''Copy string argument to clipboard'''
        text = _stringifyText(text)  # Converts non-str values to str.
        newStr = Foundation.NSString.stringWithString_(text).nsstring()
        newData = newStr.dataUsingEncoding_(Foundation.NSUTF8StringEncoding)
        board = AppKit.NSPasteboard.generalPasteboard()
        board.declareTypes_owner_([AppKit.NSStringPboardType], None)
        board.setData_forType_(newData, AppKit.NSStringPboardType)

    def paste_osx_pyobjc():
        "Returns contents of clipboard"
        board = AppKit.NSPasteboard.generalPasteboard()
        content = board.stringForType_(AppKit.NSStringPboardType)
        return content

    return copy_osx_pyobjc


def init_gtk_clipboard():
    global gtk
    import gtk

    def copy_gtk(text):
        global cb
        text = _stringifyText(text)  # Converts non-str values to str.
        cb = gtk.Clipboard()
        cb.set_text(text)
        cb.store()
    return copy_gtk


def init_qt_clipboard():
    global QApplication
    # $DISPLAY should exist

    # Try to import from qtpy, but if that fails try PyQt5 then PyQt4
    try:
        from qtpy.QtWidgets import QApplication
    except:
        try:
            from PyQt5.QtWidgets import QApplication
        except:
            from PyQt4.QtGui import QApplication

    app = QApplication.instance()
    if app is None:
        app = QApplication([])

    def copy_qt(text):
        text = _stringifyText(text)  # Converts non-str values to str.
        cb = app.clipboard()
        cb.setText(text)

    return copy_qt


def init_xclip_clipboard():
    DEFAULT_SELECTION = 'c'
    PRIMARY_SELECTION = 'p'

    def copy_xclip(text, primary=False):
        text = _stringifyText(text)  # Converts non-str values to str.
        selection = DEFAULT_SELECTION
        if primary:
            selection = PRIMARY_SELECTION
        p = subprocess.Popen(['xclip', '-selection', selection],
                             stdin=subprocess.PIPE, close_fds=True)
        p.communicate(input=text.encode(ENCODING))

    return copy_xclip


def init_xsel_clipboard():
    DEFAULT_SELECTION = '-b'
    PRIMARY_SELECTION = '-p'

    def copy_xsel(text, primary=False):
        text = _stringifyText(text)  # Converts non-str values to str.
        selection_flag = DEFAULT_SELECTION
        if primary:
            selection_flag = PRIMARY_SELECTION
        p = subprocess.Popen(['xsel', selection_flag, '-i'],
                             stdin=subprocess.PIPE, close_fds=True)
        p.communicate(input=text.encode(ENCODING))

    return copy_xsel


def init_klipper_clipboard():
    def copy_klipper(text):
        text = _stringifyText(text)  # Converts non-str values to str.
        p = subprocess.Popen(
            ['qdbus', 'org.kde.klipper', '/klipper', 'setClipboardContents',
             text.encode(ENCODING)],
            stdin=subprocess.PIPE, close_fds=True)
        p.communicate(input=None)

    return copy_klipper


def init_dev_clipboard_clipboard():
    def copy_dev_clipboard(text):
        text = _stringifyText(text)  # Converts non-str values to str.
        if text == '':
            warnings.warn(
                'Pyperclip cannot copy a blank string to the clipboard on Cygwin. This is effectively a no-op.')
        if '\r' in text:
            warnings.warn('Pyperclip cannot handle \\r characters on Cygwin.')

        fo = open('/dev/clipboard', 'wt')
        fo.write(text)
        fo.close()

    return copy_dev_clipboard


def init_no_clipboard():
    class ClipboardUnavailable(object):

        def __call__(self, *args, **kwargs):
            raise PyperclipException(EXCEPT_MSG)

        def __bool__(self):
            return False

    return ClipboardUnavailable(), ClipboardUnavailable()


# Windows-related clipboard functions:
class CheckedCall(object):
    def __init__(self, f):
        super(CheckedCall, self).__setattr__("f", f)

    def __call__(self, *args):
        ret = self.f(*args)
        if not ret and get_errno():
            raise PyperclipWindowsException("Error calling " + self.f.__name__)
        return ret

    def __setattr__(self, key, value):
        setattr(self.f, key, value)


def init_windows_clipboard():
    global HGLOBAL, LPVOID, DWORD, LPCSTR, INT, HWND, HINSTANCE, HMENU, BOOL, UINT, HANDLE
    from ctypes.wintypes import (HGLOBAL, LPVOID, DWORD, LPCSTR, INT, HWND,
                                 HINSTANCE, HMENU, BOOL, UINT, HANDLE)

    windll = ctypes.windll
    msvcrt = ctypes.CDLL('msvcrt')

    safeCreateWindowExA = CheckedCall(windll.user32.CreateWindowExA)
    safeCreateWindowExA.argtypes = [DWORD, LPCSTR, LPCSTR, DWORD, INT, INT,
                                    INT, INT, HWND, HMENU, HINSTANCE, LPVOID]
    safeCreateWindowExA.restype = HWND

    safeDestroyWindow = CheckedCall(windll.user32.DestroyWindow)
    safeDestroyWindow.argtypes = [HWND]
    safeDestroyWindow.restype = BOOL

    OpenClipboard = windll.user32.OpenClipboard
    OpenClipboard.argtypes = [HWND]
    OpenClipboard.restype = BOOL

    safeCloseClipboard = CheckedCall(windll.user32.CloseClipboard)
    safeCloseClipboard.argtypes = []
    safeCloseClipboard.restype = BOOL

    safeEmptyClipboard = CheckedCall(windll.user32.EmptyClipboard)
    safeEmptyClipboard.argtypes = []
    safeEmptyClipboard.restype = BOOL

    safeGetClipboardData = CheckedCall(windll.user32.GetClipboardData)
    safeGetClipboardData.argtypes = [UINT]
    safeGetClipboardData.restype = HANDLE

    safeSetClipboardData = CheckedCall(windll.user32.SetClipboardData)
    safeSetClipboardData.argtypes = [UINT, HANDLE]
    safeSetClipboardData.restype = HANDLE

    safeGlobalAlloc = CheckedCall(windll.kernel32.GlobalAlloc)
    safeGlobalAlloc.argtypes = [UINT, c_size_t]
    safeGlobalAlloc.restype = HGLOBAL

    safeGlobalLock = CheckedCall(windll.kernel32.GlobalLock)
    safeGlobalLock.argtypes = [HGLOBAL]
    safeGlobalLock.restype = LPVOID

    safeGlobalUnlock = CheckedCall(windll.kernel32.GlobalUnlock)
    safeGlobalUnlock.argtypes = [HGLOBAL]
    safeGlobalUnlock.restype = BOOL

    wcslen = CheckedCall(msvcrt.wcslen)
    wcslen.argtypes = [c_wchar_p]
    wcslen.restype = UINT

    GMEM_MOVEABLE = 0x0002
    CF_UNICODETEXT = 13

    @contextlib.contextmanager
    def window():
        hwnd = safeCreateWindowExA(0, b"STATIC", None, 0, 0, 0, 0, 0,
                                   None, None, None, None)
        try:
            yield hwnd
        finally:
            safeDestroyWindow(hwnd)

    @contextlib.contextmanager
    def clipboard(hwnd):
        t = time.time() + 0.5
        success = False
        while time.time() < t:
            success = OpenClipboard(hwnd)
            if success:
                break
            time.sleep(0.01)
        if not success:
            raise PyperclipWindowsException("Error calling OpenClipboard")

        try:
            yield
        finally:
            safeCloseClipboard()

    def copy_windows(text):
        text = _stringifyText(text)  # Converts non-str values to str.

        with window() as hwnd:
            with clipboard(hwnd):
                safeEmptyClipboard()

                if text:
                    count = wcslen(text) + 1
                    handle = safeGlobalAlloc(GMEM_MOVEABLE,
                                             count * sizeof(c_wchar))
                    locked_handle = safeGlobalLock(handle)

                    ctypes.memmove(c_wchar_p(locked_handle), c_wchar_p(text), count * sizeof(c_wchar))

                    safeGlobalUnlock(handle)
                    safeSetClipboardData(CF_UNICODETEXT, handle)

    return copy_windows


def init_wsl_clipboard():
    def copy_wsl(text):
        text = _stringifyText(text)  # Converts non-str values to str.
        p = subprocess.Popen(['clip.exe'],
                             stdin=subprocess.PIPE, close_fds=True)
        p.communicate(input=text.encode(ENCODING))

    return copy_wsl


# Automatic detection of clipboard mechanisms and importing is done in deteremine_clipboard():
def determine_clipboard():
    '''
    Determine the OS/platform and set the copy() and paste() functions
    accordingly.
    '''

    global Foundation, AppKit, gtk, qtpy, PyQt4, PyQt5

    # Setup for the CYGWIN platform:
    if 'cygwin' in platform.system().lower():  # Cygwin has a variety of values returned by platform.system(), such as 'CYGWIN_NT-6.1'
        # FIXME: pyperclip currently does not support Cygwin,
        # see https://github.com/asweigart/pyperclip/issues/55
        if os.path.exists('/dev/clipboard'):
            warnings.warn(
                'Pyperclip\'s support for Cygwin is not perfect, see https://github.com/asweigart/pyperclip/issues/55')
            return init_dev_clipboard_clipboard()

    # Setup for the WINDOWS platform:
    elif os.name == 'nt' or platform.system() == 'Windows':
        return init_windows_clipboard()

    if platform.system() == 'Linux':
        with open('/proc/version', 'r') as f:
            if "Microsoft" in f.read():
                return init_wsl_clipboard()

    # Setup for the MAC OS X platform:
    if os.name == 'mac' or platform.system() == 'Darwin':
        try:
            import Foundation  # check if pyobjc is installed
            import AppKit
        except ImportError:
            return init_osx_pbcopy_clipboard()
        else:
            return init_osx_pyobjc_clipboard()

    # Setup for the LINUX platform:
    if HAS_DISPLAY:
        try:
            import gtk  # check if gtk is installed
        except ImportError:
            pass  # We want to fail fast for all non-ImportError exceptions.
        else:
            return init_gtk_clipboard()

        if _executable_exists("xsel"):
            return init_xsel_clipboard()
        if _executable_exists("xclip"):
            return init_xclip_clipboard()
        if _executable_exists("klipper") and _executable_exists("qdbus"):
            return init_klipper_clipboard()

        try:
            # qtpy is a small abstraction layer that lets you write applications using a single api call to either PyQt or PySide.
            # https://pypi.python.org/pypi/QtPy
            import qtpy  # check if qtpy is installed
        except ImportError:
            # If qtpy isn't installed, fall back on importing PyQt4.
            try:
                import PyQt5  # check if PyQt5 is installed
            except ImportError:
                try:
                    import PyQt4  # check if PyQt4 is installed
                except ImportError:
                    pass  # We want to fail fast for all non-ImportError exceptions.
                else:
                    return init_qt_clipboard()
            else:
                return init_qt_clipboard()
        else:
            return init_qt_clipboard()
    return init_no_clipboard()


def set_clipboard(clipboard):
    global copy
    clipboard_types = {'pbcopy': init_osx_pbcopy_clipboard,
                       'pyobjc': init_osx_pyobjc_clipboard,
                       'gtk': init_gtk_clipboard,
                       'qt': init_qt_clipboard,  # TODO - split this into 'qtpy', 'pyqt4', and 'pyqt5'
                       'xclip': init_xclip_clipboard,
                       'xsel': init_xsel_clipboard,
                       'klipper': init_klipper_clipboard,
                       'windows': init_windows_clipboard,
                       'no': init_no_clipboard}
    if clipboard not in clipboard_types:
        raise ValueError('Argument must be one of %s' % (', '.join([repr(_) for _ in clipboard_types.keys()])))

    # Sets pyperclip's copy() and paste() functions:
    copy = clipboard_types[clipboard]()


def lazy_load_stub_copy(text):
    global copy
    copy = determine_clipboard()
    return copy(text)


def is_available():
    return copy != lazy_load_stub_copy

copy = lazy_load_stub_copy

__all__ = ['copy', 'set_clipboard', 'determine_clipboard']

"""
OUR WORK BEGINS --- THANK YOU AL SWEIGERT
"""
class App(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.pack()

        print("open")
        topFrame = tk.Frame(self)
        topFrame.pack()

        rowsLbl = tk.Label(topFrame, text="Rows:")
        self.rowsEnt = tk.Entry(topFrame, width=5)
        rowsLbl.pack(side="left")
        self.rowsEnt.pack(side="left")

        colsLbl = tk.Label(topFrame, text="Columns:")
        self.colsEnt = tk.Entry(topFrame, width=5)
        colsLbl.pack(side="left")
        self.colsEnt.pack(side="left")

        enterBtn = tk.Button(text="Generate", width=22, command=self.createGrid)
        enterBtn.pack()

    def createGrid(self):
        if self.rowsEnt.get() and self.colsEnt.get():
            child = tk.Tk()

            rows = int(self.rowsEnt.get())
            cols = int(self.colsEnt.get())
            print(f"\n\n{rows}x{cols}\n\n")
            matrix = [[] for _ in range(rows)]
            for i in range(rows):
                child.rowconfigure(i, )  # minsize=50)

                for j in range(0, cols):
                    child.columnconfigure(j, weight=1, )
                    if i % 2 == 0:
                        entry = tk.Entry(master=child, justify="center", width=12, bg="gray90")  # {i} Column {j}")
                    else:
                        entry = tk.Entry(master=child, justify="center", width=12)
                    entry.grid(row=i, column=j, sticky="ew")  # pack(padx=2, pady=2)
                    matrix[i].append(entry)

            copyBtn = tk.Button(master=child, text="Copy", width=10, command=lambda: copy(entriesToTable(matrix)))
            copyBtn.grid(row=rows, column=0, columnspan=cols)
            child.mainloop()


def add_table_headers_to_list(line: str) -> list:
    headers = []
    for header in line.split("] "):
        header = header.strip().replace("]", "").replace("[", "")
        headers.append(header.center(4))
    return headers


def add_data_to_rows(data: list) -> list:
    data_by_rows = []
    for row in data:
        data_by_rows.append(row.rstrip().split(" "))
    return data_by_rows


def create_table(headers: list, data: list) -> str:
    width = len(headers)
    for word in headers:
        width += len(word)

    width_table = [len(word) for word in headers]

    top_line = '.'
    for width in width_table:
        top_line += f'{"-" * width}+'
    top_line = f'{top_line[:-1]}.'

    mid_delimiter = "|"
    for width in width_table:
        mid_delimiter += f'{"-" * width}+'
    mid_delimiter = f'{mid_delimiter[:-1]}|'

    bottom_line = '\''
    for width in width_table:
        bottom_line += f'{"-" * width}+'
    bottom_line = f'{bottom_line[:-1]}\''

    table = f'{top_line}\n'
    # add the headers
    for header in headers:
        table += f'|{header}'
    table = f'{table}|'
    table += f'\n{mid_delimiter}\n|'

    # add the data
    for row in data:
        for i in range(0, len(row)):
            table += f'{row[i].center(width_table[i])}|'
        table += f'\n{mid_delimiter}\n|'

    # clean up the bottom
    table = table[:(len(table) - len(mid_delimiter) - 2)]

    # add the bottom line
    table += f'{bottom_line}'

    return table


def entriesToTable(matrix):
    table_headers = [entry.get() for entry in matrix[0]]
    data_by_rows = [[entry.get() for entry in matrix[i + 1]] for i in range(len(matrix) - 1)]
    return create_table(table_headers, data_by_rows)


if len(argv) < 2:
    root = tk.Tk()
    app = App(root)
    app.mainloop()
else:
    data = s.read().splitlines()
    if table_headers := data.pop(0):  # need python 3.8 for walrus use :=

        table_headers = add_table_headers_to_list(table_headers)
        data_by_rows = add_data_to_rows(data)

        stdout.write(create_table(table_headers, data_by_rows))
