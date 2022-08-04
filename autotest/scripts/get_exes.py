import os

from argparse import ArgumentParser

try:
    from modflow_devtools import (
        MFTestExe,
    )
except:
    msg = "modflow-devtools not in PYTHONPATH"
    raise Exception(msg)

def parse_args():

    bindir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "bin")
    )

    parser = ArgumentParser(
        description="create bin directory of downloaded "
        + "mf executables and official mf6 "
        + "release built from source"
    )
    parser.add_argument(
        "-b",
        "--bin",
        required=False,
        default=bindir,
        help="bin path for executables",
    )
    parser.add_argument(
        "-i",
        "--iconic",
        action="store_true",
        required=False,
        help="iconic bin directory structure",
    )
    parser.add_argument(
        "-c",
        "--cleanup",
        action="store_true",
        required=False,
        help="remove existing bin dirs before update",
    )

    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    if args.iconic:
        releasebin = os.path.join(args.bin, "downloaded")
    else:
        releasebin = args.bin

    exe = MFTestExe(
        releasebin=releasebin, builtbin=os.path.join(args.bin, "rebuilt")
    )
    if args.cleanup:
        exe.cleanup()
    exe.download_releases()
    exe.build_mf6_release()
