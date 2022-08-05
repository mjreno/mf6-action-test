import os
import sys
import json

from argparse import ArgumentParser

try:
    from modflow_devtools import (
        MFTestContext,
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
        description="replaces former get_exes.py: create bin directory "
        + "of downloaded mf executables and official mf6 release built "
        + "from source"
    )
    parser.add_argument(
        "-b",
        "--bin",
        required=False,
        help="bin path for executables",
    )
    parser.add_argument(
        "-i",
        "--iconic",
        action="store_true",
        required=False,
        help="when used with -b option, create iconic bin directory structure",
    )
    parser.add_argument(
        "-c",
        "--cleanup",
        action="store_true",
        required=False,
        help="remove existing bin dirs before update",
    )
    parser.add_argument(
        "-t",
        "--testbin",
        nargs="?",
        required=False,
        const=bindir,
        help="modflow6 built dev bin, use to setup devtools for testing, "
        + "e.g. \'python get_releases.py -t ../../bin\'",
    )

    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    if args.testbin:
        ctx = MFTestContext(testbin=args.testbin)
        json.dump(ctx.get_target_dictionary(), sys.stdout, indent=2)

    elif args.bin:
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
