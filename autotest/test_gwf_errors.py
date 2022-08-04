"""
MODFLOW 6 Autotest
Test to make sure that mf6 is failing with the correct error messages.  This
test script is set up to be extensible so that simple models can be created
very easily and tested with different options to succeed or fail correctly.

"""

import os
import shutil
import subprocess

import numpy as np
import pytest

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


def run_mf6(argv, ws):
    buff = []
    proc = subprocess.Popen(
        argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=ws
    )
    result, error = proc.communicate()
    if result is not None:
        c = result.decode("utf-8")
        c = c.rstrip("\r\n")
        print(f"{c}")
        buff.append(c)

    return proc.returncode, buff


def run_mf6_error(ws, err_str_list, mf6_exe):
    returncode, buff = run_mf6([mf6_exe], ws)
    msg = "mf terminated with error"
    if teardown_test:
        shutil.rmtree(ws, ignore_errors=True)
    if returncode != 0:
        if not isinstance(err_str_list, list):
            err_str_list = list(err_str_list)
        for err_str in err_str_list:
            err = any(err_str in s for s in buff)
            if err:
                raise RuntimeError(msg)
            else:
                msg += " but did not print correct error message."
                msg += f'  Correct message should have been "{err_str}"'
                raise ValueError(msg)


def get_minimal_gwf_simulation(
    ws,
    name="test",
    simkwargs=None,
    simnamefilekwargs=None,
    tdiskwargs=None,
    gwfkwargs=None,
    imskwargs=None,
    diskwargs=None,
    disukwargs=None,
    ickwargs=None,
    npfkwargs=None,
    chdkwargs=None,
    mf6_exe=None,
):
    if simkwargs is None:
        simkwargs = {}
    if tdiskwargs is None:
        tdiskwargs = {}
    if gwfkwargs is None:
        gwfkwargs = {}
        gwfkwargs["modelname"] = name
    if imskwargs is None:
        imskwargs = {
            "print_option": "SUMMARY",
        }
    if diskwargs is None and disukwargs is None:
        diskwargs = {}
        diskwargs["nlay"] = 5
        diskwargs["nrow"] = 5
        diskwargs["ncol"] = 5
        diskwargs["top"] = 0
        diskwargs["botm"] = [-1, -2, -3, -4, -5]
    if ickwargs is None:
        ickwargs = {}
    if npfkwargs is None:
        npfkwargs = {}
    if chdkwargs is None:
        chdkwargs = {}
        nl = diskwargs["nlay"]
        nr = diskwargs["nrow"]
        nc = diskwargs["ncol"]
        chdkwargs["stress_period_data"] = {
            0: [[(0, 0, 0), 0], [(0, nr - 1, nc - 1), 1]]
        }
    sim = flopy.mf6.MFSimulation(
        sim_name=name, version="mf6", exe_name=mf6_exe, sim_ws=ws, **simkwargs
    )
    if simnamefilekwargs is not None:
        for k in simnamefilekwargs:
            sim.name_file.__setattr__(k, simnamefilekwargs[k])
    tdis = flopy.mf6.ModflowTdis(sim, **tdiskwargs)
    gwf = flopy.mf6.ModflowGwf(sim, **gwfkwargs)
    ims = flopy.mf6.ModflowIms(sim, **imskwargs)
    if diskwargs is not None:
        dis = flopy.mf6.ModflowGwfdis(gwf, **diskwargs)
    elif disukwargs is not None:
        disu = flopy.mf6.ModflowGwfdisu(gwf, **disukwargs)
    ic = flopy.mf6.ModflowGwfic(gwf, **ickwargs)
    npf = flopy.mf6.ModflowGwfnpf(gwf, **npfkwargs)
    chd = flopy.mf6.modflow.mfgwfchd.ModflowGwfchd(gwf, **chdkwargs)
    return sim


def simple_model_success(testdir, mf6_exe):
    # test a simple model to make sure it runs and terminates correctly
    ws = testdir
    sim = get_minimal_gwf_simulation(ws, mf6_exe=mf6_exe)
    sim.write_simulation()
    returncode, buff = run_mf6([mf6_exe], ws)
    assert returncode == 0, "mf6 failed for simple model."

    final_message = "Normal termination of simulation."
    failure_message = f'mf6 did not terminate with "{final_message}"'
    assert final_message in buff[-1], failure_message
    if teardown_test:
        shutil.rmtree(ws, ignore_errors=True)
    return


def empty_folder(testdir, mf6_exe):
    with pytest.raises(RuntimeError):
        # make sure mf6 fails when there is no simulation name file
        err_str = "mf6: mfsim.nam is not present in working directory."
        run_mf6_error(testdir, err_str, mf6_exe)


def sim_errors(testdir, mf6_exe):
    with pytest.raises(RuntimeError):
        # verify that the correct number of errors are reported
        ws = testdir
        chdkwargs = {}
        chdkwargs["stress_period_data"] = {
            0: [[(0, 0, 0), 0.0] for i in range(10)]
        }
        sim = get_minimal_gwf_simulation(ws, chdkwargs=chdkwargs, mf6_exe=mf6_exe)
        sim.write_simulation()
        err_str = ["1. Cell is already a constant head ((1,1,1))."]
        run_mf6_error(ws, err_str, mf6_exe)


def sim_maxerrors(testdir, mf6_exe):
    with pytest.raises(RuntimeError):
        # verify that the maxerrors keyword gives the correct error output
        ws = testdir
        simnamefilekwargs = {}
        simnamefilekwargs["maxerrors"] = 5
        chdkwargs = {}
        chdkwargs["stress_period_data"] = {
            0: [[(0, 0, 0), 0.0] for i in range(10)]
        }
        sim = get_minimal_gwf_simulation(
            ws, simnamefilekwargs=simnamefilekwargs, chdkwargs=chdkwargs, mf6_exe=mf6_exe
        )
        sim.write_simulation()
        err_str = [
            "5. Cell is already a constant head ((1,1,1)).",
            "5 additional errors detected but not printed.",
            "UNIT ERROR REPORT:",
            "1. ERROR OCCURRED WHILE READING FILE 'test.chd'",
        ]
        run_mf6_error(ws, err_str, mf6_exe)


def disu_errors(testdir, mf6_exe):
    with pytest.raises(RuntimeError):
        ws = testdir
        disukwargs = get_disu_kwargs(
            3, 3, 3, np.ones(3), np.ones(3), 0, [-1, -2, -3]
        )
        top = disukwargs["top"]
        bot = disukwargs["bot"]
        top[9] = 2.0
        bot[9] = 1.0
        sim = get_minimal_gwf_simulation(
            ws, disukwargs=disukwargs, chdkwargs={"stress_period_data": [[]],}, mf6_exe=mf6_exe
        )
        sim.write_simulation()
        err_str = [
            "1. Top elevation (    2.00000    ) for cell 10 is above bottom elevation (",
            "-1.00000    ) for cell 1. Based on node numbering rules cell 10 must be",
            "below cell 1.",
            "UNIT ERROR REPORT:"
            "1. ERROR OCCURRED WHILE READING FILE './test.disu'",
        ]
        run_mf6_error(ws, err_str, mf6_exe)


def solver_fail(testdir, mf6_exe):
    with pytest.raises(RuntimeError):
        # test failed to converge
        ws = testdir
        imskwargs = {"inner_maximum": 1, "outer_maximum": 2}
        sim = get_minimal_gwf_simulation(ws, imskwargs=imskwargs, mf6_exe=mf6_exe)
        sim.write_simulation()
        err_str = [
            "Simulation convergence failure occurred 1 time(s).",
            "Premature termination of simulation.",
        ]
        run_mf6_error(ws, err_str, mf6_exe)


def fail_continue_success(testdir, mf6_exe):
    # test continue but failed to converge
    ws = testdir
    tdiskwargs = {"nper": 1, "perioddata": [(10.0, 10, 1.0)]}
    imskwargs = {"inner_maximum": 1, "outer_maximum": 2}
    sim = get_minimal_gwf_simulation(
        ws, imskwargs=imskwargs, tdiskwargs=tdiskwargs, mf6_exe=mf6_exe
    )
    sim.name_file.continue_ = True
    sim.write_simulation()
    returncode, buff = run_mf6([mf6_exe], ws)
    assert returncode == 0, "mf6 failed for simple model."

    final_message = "Simulation convergence failure occurred 10 time(s)."
    failure_message = f'mf6 did not terminate with "{final_message}"'
    assert final_message in buff[0], failure_message

    final_message = "Normal termination of simulation."
    failure_message = f'mf6 did not terminate with "{final_message}"'
    assert final_message in buff[0], failure_message

    if teardown_test:
        shutil.rmtree(ws, ignore_errors=True)

    return


tests = [
    empty_folder,
    simple_model_success,
    sim_errors,
    sim_maxerrors,
    disu_errors,
    solver_fail,
    fail_continue_success,
]


@pytest.mark.gwf
@pytest.mark.sys
@pytest.mark.disu
@pytest.mark.parametrize(
    "idx, test",
    list(enumerate(tests)),
)
def test_gwf_errors(idx, test, tmpdir, mf6testctx):
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
        os.makedirs(testdir, exist_ok=True)
        test(testdir, ctx.get_target_dictionary()["mf6"])
