import pytest

from modflow_devtools import (
    MFTestContext,
)

@pytest.fixture(scope="session")
def mf6testctx(request):
    return MFTestContext(testbin="../bin")
