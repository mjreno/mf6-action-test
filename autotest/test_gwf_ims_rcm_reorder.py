import os

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
        eval_bud_diff,
        testing_framework,
        Simulation,
    )
except:
    msg = "modflow-devtools not in PYTHONPATH"
    raise Exception(msg)

paktest = "ims"

runs = [
    "ims_rcm",
]

# spatial discretization data
nlay, nrow, ncol = 2, 5, 30
delr, delc = 100.0, 100.0
top = 0.0
botm = [-10.0, -20.0]
strt = 0.0
chd_left = 10.0
chd_right = 5.0

#
def build_model(idx, ws):

    # static model data
    # temporal discretization
    nper = 1
    tdis_rc = [(1.0, 1, 1.0)]

    # build MODFLOW 6 files
    name = runs[idx]
    sim = flopy.mf6.MFSimulation(
        sim_name=name,
        version="mf6",
        exe_name="mf6",
        sim_ws=ws,
    )
    # create tdis package
    tdis = flopy.mf6.ModflowTdis(
        sim,
        time_units="seconds",
        nper=nper,
        perioddata=tdis_rc,
    )

    if not ws.endswith("mf6"):
        reordering_method = "rcm"
    else:
        reordering_method = None

    # create iterative model solution and register the gwf model with it
    ims = flopy.mf6.ModflowIms(
        sim,
        print_option="ALL",
        reordering_method=reordering_method,
        preconditioner_levels=10,
        preconditioner_drop_tolerance=1e-6,
        outer_dvclose=1e-9,
        outer_maximum=100,
        inner_dvclose=1e-12,
        inner_maximum=100,
    )

    # create gwf model
    gwf = flopy.mf6.ModflowGwf(
        sim,
        modelname=name,
        save_flows=True,
    )

    dis = flopy.mf6.ModflowGwfdis(
        gwf,
        length_units="meters",
        nlay=nlay,
        nrow=nrow,
        ncol=ncol,
        delr=delr,
        delc=delc,
        top=top,
        botm=botm,
    )

    # initial conditions
    ic = flopy.mf6.ModflowGwfic(gwf, strt=strt)

    # node property flow
    npf = flopy.mf6.ModflowGwfnpf(gwf)

    # chd files
    # chd data
    spd = [[(0, i, 0), chd_left] for i in range(nrow)]
    spd += [[(0, i, ncol - 1), chd_right] for i in range(nrow)]
    chd = flopy.mf6.modflow.ModflowGwfchd(
        gwf, stress_period_data=spd, pname="chd-1"
    )

    # output control
    hdspth = f"{name}.hds"
    budpth = f"{name}.cbc"
    oc = flopy.mf6.ModflowGwfoc(
        gwf,
        head_filerecord=hdspth,
        budget_filerecord=budpth,
        printrecord=[
            ("BUDGET", "ALL"),
        ],
        saverecord=[
            ("BUDGET", "ALL"),
            ("HEAD", "ALL"),
        ],
    )

    return sim


def build_models(idx, base_ws):
    sim = build_model(idx, base_ws)

    ws = os.path.join(base_ws, "mf6")
    mc = build_model(idx, ws)

    return sim, mc


def eval_flows(sim):
    idx = sim.idxsim
    name = runs[idx]
    print("evaluating flow results..." f"({name})")

    fpth = os.path.join(sim.simpath, f"{name}.dis.grb")
    ia = flopy.mf6.utils.MfGrdFile(fpth).ia

    fpth = os.path.join(sim.simpath, f"{name}.cbc")
    b0 = flopy.utils.CellBudgetFile(fpth, precision="double")

    fpth = os.path.join(sim.simpath, "mf6", f"{name}.cbc")
    b1 = flopy.utils.CellBudgetFile(fpth, precision="double")

    fpth = os.path.join(sim.simpath, f"{name}.cbc.cmp.out")
    eval_bud_diff(fpth, b0, b1, ia=ia)

    # close the budget files
    b0.close()
    b1.close()


# - No need to change any code below
@pytest.mark.gwf
@pytest.mark.ims
@pytest.mark.parametrize(
    "idx, run",
    list(enumerate(runs)),
)
def test_gwf_ims_rcm_reorder(idx, run, tmpdir, testbin):
    # initialize testing framework
    test = testing_framework()

    # build the model
    test.build_mf6_models(build_models, idx, str(tmpdir))

    # run the test models
    test.run_mf6(
        Simulation(
            str(tmpdir),
            exfunc=eval_flows,
            testbin=testbin,
            idxsim=idx,
        )
    )


def main():
    from conftest import mf6_testbin

    # initialize testing framework
    test = testing_framework()

    # run the test models
    for idx, run in enumerate(runs):
        simdir = os.path.join(
            "autotest-keep", "standalone",
            os.path.splitext(os.path.basename(__file__))[0],
            run,
        )
        test.build_mf6_models(build_models, idx, simdir)
        sim = Simulation(
            simdir,
            exfunc=eval_flows,
            testbin=mf6_testbin,
            idxsim=idx,
        )
        test.run_mf6(sim)
    return


if __name__ == "__main__":
    # print message
    print(f"standalone run of {os.path.basename(__file__)}")

    # run main routine
    main()
