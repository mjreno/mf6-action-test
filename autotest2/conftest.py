import pytest

from modflow_devtools import (
    MFTestContext,
)

modflow6_testbin = "../bin"

def pytest_sessionstart(session):
    MFTestContext(testbin=modflow6_testbin)

@pytest.fixture(scope="session")
def mf6testctx(request):
    return MFTestContext(testbin=modflow6_testbin)
