import json
import os
import platform
import re
import sys
import traceback
from pathlib import Path
from typing import TypedDict, List, Tuple, Optional

import debugpy

REMOTE_DEBUGGER_STARTED = False

class AppPathMappings(TypedDict):
    device_sys_path_regex: str
    device_subfolders: List[str]
    host_folders: List[str]


class AppPackagesPathMappings(TypedDict):
    sys_path_regex: str
    host_folder: str


class PathMappings(TypedDict):
    app_path_mappings: Optional[AppPathMappings]
    app_packages_path_mappings: Optional[AppPackagesPathMappings]


def _load_path_mappings(verbose: bool) -> List[Tuple[str, str]]:
    path_mappings = os.environ.get("BRIEFCASE_DEBUGGER_PATH_MAPPINGS", None)

    mappings_dict: PathMappings = json.loads(path_mappings)

    app_path_mappings = mappings_dict.get("app_path_mappings", None)
    app_packages_path_mappings = mappings_dict.get("app_packages_path_mappings", None)

    mappings_list = []
    if app_path_mappings:
        device_app_folder = next(
            (
                p
                for p in sys.path
                if re.search(app_path_mappings["device_sys_path_regex"], p)
            ),
            None,
        )
        if device_app_folder:
            for app_subfolder_device, app_subfolder_host in zip(
                app_path_mappings["device_subfolders"],
                app_path_mappings["host_folders"],
            ):
                mappings_list.append(
                    (
                        app_subfolder_host,
                        str(Path(device_app_folder) / app_subfolder_device),
                    )
                )
    if app_packages_path_mappings:
        device_app_packages_folder = next(
            (
                p
                for p in sys.path
                if re.search(app_packages_path_mappings["sys_path_regex"], p)
            ),
            None,
        )
        if device_app_packages_folder:
            mappings_list.append(
                (
                    app_packages_path_mappings["host_folder"],
                    str(Path(device_app_packages_folder)),
                )
            )

    if verbose:
        print("Extracted path mappings:")
        for idx, p in enumerate(path_mappings):
            print(f"[{idx}] host =   {p[0]}")
            print(f"[{idx}] device = {p[1]}")

    return mappings_list


def _start_debugpy(verbose: bool):
    # Parsing ip/port
    mode = os.environ.get("BRIEFCASE_DEBUGGER_MODE", "server")
    ip = os.environ.get("BRIEFCASE_DEBUGGER_IP", "localhost")
    port = os.environ.get("BRIEFCASE_DEBUGGER_PORT", "5678")
    path_mappings = _load_path_mappings()
    
    # When an app is bundled with briefcase "os.__file__" is not set at runtime
    # on some platforms (eg. windows). But debugpy accesses it internally, so it
    # has to be set or an Exception is raised from debugpy.
    if not hasattr(os, "__file__"):
        if verbose:
            print("'os.__file__' not available. Patching it...")
        os.__file__ = ""

    # Starting remote debugger...
    if mode == "client":
        print(
            f"""
Connecting to debugpy server at {ip}:{port}...
To create the debugpy server using VSCode add the following configuration to launch.json and start the debugger:
{{
    "version": "0.2.0",
    "configurations": [
        {{
            "name": "Briefcase: Attach (Listen)",
            "type": "debugpy",
            "request": "attach",
            "listen": {{
                "host": "{ip}",
                "port": {port}
            }}
        }}
    ]
}}
"""
        )
        debugpy.connect((ip, port))

    elif mode == "server":
        print(f"Starting debugpy in server mode at {ip}:{port}...")
        debugpy.listen((ip, port), in_process_debug_adapter=True)

    if len(path_mappings) > 0:
        if verbose:
            print("Adding path mappings...")

        import pydevd_file_utils

        pydevd_file_utils.setup_client_server_paths(path_mappings)

    if mode == "client":
        print("Waiting for debugger to attach...")
        debugpy.wait_for_client()
    elif mode == "server":
        print("The debugpy server started. Waiting for debugger to attach...")
        print(
            f"""
To connect to debugpy using VSCode add the following configuration to launch.json:
{{
    "version": "0.2.0",
    "configurations": [
        {{
            "name": "Briefcase: Attach (Connect)",
            "type": "debugpy",
            "request": "attach",
            "connect": {{
                "host": "{ip}",
                "port": {port}
            }}
        }}
    ]
}}
"""
        )
        debugpy.wait_for_client()

    print("Debugger attached.")


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
    _start_debugpy(verbose)


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
import briefcase_debugpy_debugadapter
briefcase_debugpy_debugadapter.start_remote_debugger()
```
"""
        )
    else:
        autostart_remote_debugger()
