import os
import platform
import re
import socket
import sys
import traceback

REMOTE_DEBUGGER_STARTED = False

NEWLINE_REGEX = re.compile("\\r?\\n")

class SocketFileWrapper(object):
    def __init__(self, connection: socket.socket):
        self.connection = connection
        self.stream = connection.makefile('rw')

        self.read = self.stream.read
        self.readline = self.stream.readline
        self.readlines = self.stream.readlines
        self.close = self.stream.close
        self.isatty = self.stream.isatty
        self.flush = self.stream.flush
        self.fileno = lambda: -1
        self.__iter__ = self.stream.__iter__

    @property
    def encoding(self):
        return self.stream.encoding

    def write(self, data):
        data = NEWLINE_REGEX.sub("\\r\\n", data)
        self.connection.sendall(data.encode(self.stream.encoding))

    def writelines(self, lines):
        for line in lines:
            self.write(line)

def _start_pdb(verbose: bool):
    """Open a socket server and stream all stdio via the connection bidirectional."""
    # Parsing ip/port
    ip = os.environ.get("BRIEFCASE_DEBUGGER_IP", "localhost")
    port = os.environ.get("BRIEFCASE_DEBUGGER_PORT", "5678")

    print(
        f"""
Stdio redirector server opened at {ip}:{port}, waiting for connection...
To connect to stdio redirector use eg.:
    - telnet {ip} {port}
    - nc -C {ip} {port}
    - socat readline tcp:{ip}:{port}
"""
    )

    listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
    listen_socket.bind((ip, port))
    listen_socket.listen(1)
    connection, address = listen_socket.accept()
    print(f"Stdio redirector accepted connection from {{repr(address)}}.")

    file_wrapper = SocketFileWrapper(connection)

    sys.stderr = file_wrapper
    sys.stdout = file_wrapper
    sys.stdin = file_wrapper
    sys.__stderr__ = file_wrapper
    sys.__stdout__ = file_wrapper
    sys.__stdin__ = file_wrapper


def start_remote_debugger():
    global REMOTE_DEBUGGER_STARTED
    REMOTE_DEBUGGER_STARTED = True

    # Reading and parsing config
    config = os.environ.get("BRIEFCASE_REMOTE_DEBUGGER", None)
    if config is None:
        return  # If BRIEFCASE_REMOTE_DEBUGGER is not set, this packages does nothing...

    # check verbose output
    verbose = True if os.environ.get("BRIEFCASE_DEBUG", "0") == "1" else False

    # start debugger
    print("Starting remote debugger...")
    _start_pdb(verbose)


def autostart_remote_debugger():
    try:
        start_remote_debugger()
    except Exception:
        # Show exceiption and stop the whole application when an error occures
        print(traceback.format_exc())
        sys.exit(-1)


# only start remote debugger on the first import
if REMOTE_DEBUGGER_STARTED == False:
    if platform.system() == "Android":  # TODO: fix for Python < 3.13
        print(
            """\
On Android it is currently not possible to automatically start the debugger. This
is due to a bug in chaquopy, see https://github.com/chaquo/chaquopy/issues/1338.
          
As a workaround you can add the following lines into "__main__.py" of your app to
manually start the debugger:

```
import briefcase_pdb_debugadapter
briefcase_pdb_debugadapter.start_remote_debugger()
```
"""
        )
    else:
        autostart_remote_debugger()
