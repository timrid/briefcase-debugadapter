# Briefcase Debugadater
This package contains some debugadapters as helper package for debugging support of applications packed with briefcase.

## Installation
Normally you dont need to install this package, becaus it is done automatically by briefcase.

But in theory it can also be used without briefcase. Then it can be installed via:

pdb:
```
pip install git+https://github.com/timrid/briefcase-debugadapter#subdirectory=briefcase-pdb-debugadapter
```

debugpy:
```
pip install git+https://github.com/timrid/briefcase-debugadapter#subdirectory=briefcase-debugpy-debugadapter
```


## Usage
This package currently supports the following remote debuggers:

- pdb (through forwarding stdin/stdout via a socket)
- debugpy

This packages starts the remote debugger automatically at startup through an .pth file, if a `BRIEFCASE_DEBUGGER` environment variable is set.