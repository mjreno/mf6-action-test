import os
import pytest
from pathlib import Path
from shutil import copytree
import re

mf6_testbin = os.path.abspath(os.path.join("..", "bin"))


from modflow_devtools import (
    MFTestContext,
)


def pytest_sessionstart(session):
    # setup devtools if not already done
    MFTestContext(testbin=mf6_testbin)


@pytest.fixture(scope="session")
def mf6testctx(request):
    return MFTestContext(testbin=mf6_testbin)


@pytest.fixture(scope="session")
def testbin(request):
    return mf6_testbin


@pytest.fixture(scope="function")
def tmpdir(tmpdir_factory, request) -> Path:
    node = (
        request.node.name.replace("/", "_")
        .replace("\\", "_")
        .replace(":", "_")
    )
    temp = Path(tmpdir_factory.mktemp(node))
    yield Path(temp)

    keep = request.config.getoption("--keep")
    if keep:
        if type(keep) == bool:
            outdir = Path(os.path.join("autotest-keep", "pytest"))
        else:
            outdir = Path(keep)
        tokens = re.split("\[|\]", temp.name)
        if len(tokens) == 1:
            copytree(temp, outdir / tokens[0][:-1], dirs_exist_ok=True)
        else:
            if str(request.node.name).startswith("test_") \
                and not str(request.node.name).startswith("test_z"):
                copytree(
                    temp,
                    outdir / tokens[0] / tokens[1].split("-", 1)[1],
                    dirs_exist_ok=True,
                )
            else:
                copytree(
                    temp,
                    outdir / tokens[0] / tokens[1],
                    dirs_exist_ok=True,
                )


def pytest_addoption(parser):
    parser.addoption(
        "--keep",
        action="store",
        default=None,
        help="Save test outputs in named directory path",
    )

def pytest_addoption(parser):
    parser.addoption(
        "--keep",
        action="store_true",
        help="Save test outputs in default directory \"autotest-keep/pytest\"",
    )
