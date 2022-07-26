import pytest

from modflow_devtools import (
    MFTestContext,
)

@pytest.fixture(scope="session")
def mf6testctx_target_paths(request):
    return MFTestContext(testbin="../bin")
