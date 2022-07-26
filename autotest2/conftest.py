import pytest

from modflow_devtools import (
    MFTestContext,
)

@pytest.fixture(scope="session")
def mf6testctx_target_paths(request):
    ctx = MFTestContext(testbin="../bin")
    return ctx.get_target_dictionary()
