# Briefcase Remote Debugger
This package is an helper package for remote debugging of applications packed with briefcase.

## Installation
Normally you dont need to install this package, becaus it is done automatically by briefcase.

But in theory it can also be used without briefcase. Then it can be installed via:
```
pip install git+https://github.com/timrid/briefcase-remote-debugger@main
```

## Usage
This package currently supports the following remote debuggers:

- pdb (through forwarding stdin/stdout via a socket)
- debugpy

This packages starts the remote debugger automatically at startup through an .pth file, if a `BRIEFCASE_REMOTE_DEBUGGER` enviornment variable is set.