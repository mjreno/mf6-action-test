"""
MODFLOW 6 Autotest
Test to make sure that disu is working correctly

"""

import os
import shutil
import subprocess
import pytest

import numpy as np

try:
    import flopy
except:
    msg = "Error. FloPy package is not available.\n"
    msg += "Try installing using the following command:\n"
    msg += " pip install flopy"
    raise Exception(msg)

try:
    from modflow_devtools import (
        get_disu_kwargs,
        set_teardown_test,
        MFTestContext,
    )
except:
    msg = "modflow-devtools not in PYTHONPATH"
    raise Exception(msg)


teardown_test = set_teardown_test()


def disu_simple(rundir, mf6_exe):
    name = "disu01a"
    ws = rundir
    nlay = 3
    nrow = 3
    ncol = 3
    delr = 10.0 * np.ones(ncol)
    delc = 10.0 * np.ones(nrow)
    top = 0
    botm = [-10, -20, -30]
    disukwargs = get_disu_kwargs(nlay, nrow, ncol, delr, delc, top, botm)
    sim = flopy.mf6.MFSimulation(
        sim_name=name, version="mf6", exe_name=mf6_exe, sim_ws=ws
    )
    tdis = flopy.mf6.ModflowTdis(sim)
    gwf = flopy.mf6.ModflowGwf(sim, modelname=name)
    ims = flopy.mf6.ModflowIms(sim, print_option="SUMMARY")
    disu = flopy.mf6.ModflowGwfdisu(gwf, **disukwargs)
    ic = flopy.mf6.ModflowGwfic(gwf, strt=0.0)
    npf = flopy.mf6.ModflowGwfnpf(gwf)
    spd = {0: [[(0,), 1.0], [(nrow * ncol - 1,), 0.0]]}
    chd = flopy.mf6.modflow.mfgwfchd.ModflowGwfchd(gwf, stress_period_data=spd)
    sim.write_simulation()
    sim.run_simulation()
    if teardown_test:
        shutil.rmtree(ws, ignore_errors=True)
    return


def disu_idomain_simple(rundir, mf6_exe):
    name = "disu01b"
    ws = rundir
    nlay = 3
    nrow = 3
    ncol = 3
    delr = 10.0 * np.ones(ncol)
    delc = 10.0 * np.ones(nrow)
    top = 0
    botm = [-10, -20, -30]
    idomain = np.ones(nlay * nrow * ncol, dtype=int)
    idomain[1] = 0
    disukwargs = get_disu_kwargs(nlay, nrow, ncol, delr, delc, top, botm)
    disukwargs["idomain"] = idomain
    sim = flopy.mf6.MFSimulation(
        sim_name=name, version="mf6", exe_name=mf6_exe, sim_ws=ws
    )
    tdis = flopy.mf6.ModflowTdis(sim)
    gwf = flopy.mf6.ModflowGwf(sim, modelname=name, save_flows=True)
    ims = flopy.mf6.ModflowIms(sim, print_option="SUMMARY")
    disu = flopy.mf6.ModflowGwfdisu(gwf, **disukwargs)
    ic = flopy.mf6.ModflowGwfic(gwf, strt=0.0)
    npf = flopy.mf6.ModflowGwfnpf(gwf)
    spd = {0: [[(0,), 1.0], [(nrow * ncol - 1,), 0.0]]}
    chd = flopy.mf6.modflow.ModflowGwfchd(gwf, stress_period_data=spd)
    oc = flopy.mf6.modflow.ModflowGwfoc(
        gwf,
        budget_filerecord=f"{name}.bud",
        head_filerecord=f"{name}.hds",
        saverecord=[("HEAD", "LAST"), ("BUDGET", "LAST")],
    )
    sim.write_simulation()
    sim.run_simulation()

    # check binary grid file
    fname = os.path.join(ws, name + ".disu.grb")
    grbobj = flopy.mf6.utils.MfGrdFile(fname)
    nodes = grbobj._datadict["NODES"]
    ia = grbobj._datadict["IA"]
    ja = grbobj._datadict["JA"]
    assert nodes == disukwargs["nodes"]
    assert np.array_equal(ia[0:4], np.array([1, 4, 4, 7]))
    assert np.array_equal(ja[:6], np.array([1, 4, 10, 3, 6, 12]))
    assert ia[-1] == 127
    assert ia.shape[0] == 28, "ia should have size of 28"
    assert ja.shape[0] == 126, "ja should have size of 126"

    # load head array and ensure nodata value in second cell
    fname = os.path.join(ws, name + ".hds")
    hdsobj = flopy.utils.HeadFile(fname)
    head = hdsobj.get_alldata().flatten()
    assert head[1] == 1.0e30

    # load flowja to make sure it is the right size
    fname = os.path.join(ws, name + ".bud")
    budobj = flopy.utils.CellBudgetFile(fname, precision="double")
    flowja = budobj.get_data(text="FLOW-JA-FACE")[0].flatten()
    assert flowja.shape[0] == 126
    if teardown_test:
        shutil.rmtree(ws, ignore_errors=True)
    return


tests = [disu_simple, disu_idomain_simple]


@pytest.mark.gwf
@pytest.mark.disu
@pytest.mark.parametrize(
    "idx, test",
    list(enumerate(tests)),
)
def test_gwf_disu01(idx, test, tmpdir, mf6testctx):
    test(str(tmpdir), mf6testctx.get_target_dictionary()["mf6"])


if __name__ == "__main__":
    from conftest import mf6_testbin

    # print message
    print(f"standalone run of {os.path.basename(__file__)}")

    ctx = MFTestContext(testbin=mf6_testbin)

    for idx, test in enumerate(tests):
        testdir = os.path.join(
            "autotest-keep", "standalone",
            os.path.splitext(os.path.basename(__file__))[0],
            test.__name__,
        )
        test(testdir, ctx.get_target_dictionary()["mf6"])
