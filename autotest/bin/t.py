import importlib
import os
import shutil
import subprocess
from contextlib import contextmanager

import flopy

flopypth = flopy.__path__[0]
print(f"flopy is installed in {flopypth}")

def main():
    # write message
    tnam = os.path.splitext(os.path.basename(__file__))[0]
    msg = f"Running {tnam} test"
    print(msg)

    print("deleting existing MODFLOW 6 FloPy files")
    print("deleting existing MODFLOW 6 dfn files")
    print("copying MODFLOW 6 repo dfn files")
    print("creating MODFLOW 6 packages from repo dfn files")

    return


if __name__ == "__main__":
    print(f"standalone run of {os.path.basename(__file__)}")

    # run main routine
    main()
