"""
MODFLOW 6 Autotest
Test variable layer thicknesses with a diffusion problem and constant
concentrations on the top and bottom to make sure the resulting concentration
field is linear from top to bottom.

"""
import os

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
        testing_framework,
        Simulation,
    )
except:
    msg = "modflow-devtools not in PYTHONPATH"
    raise Exception(msg)

runs = ["dsp05a_noadv", "dsp01b_noadv"]
xt3d = [False, True]

def build_model(idx, dir):
    nlay, nrow, ncol = 5, 1, 1
    nper = 1
    perlen = [5.0]
    nstp = [200]
    tsmult = [1.0]
    steady = [True]
    delr = 1.0
    delc = 1.0
    top = 2.0
    botm = [0.0, -0.5, -1.0, -1.5, -2.0]

    nouter, ninner = 100, 300
    hclose, rclose, relax = 1e-6, 1e-6, 1.0

    tdis_rc = []
    for i in range(nper):
        tdis_rc.append((perlen[i], nstp[i], tsmult[i]))

    name = runs[idx]

    # build MODFLOW 6 files
    ws = dir
    sim = flopy.mf6.MFSimulation(
        sim_name=name, version="mf6", exe_name="mf6", sim_ws=ws
    )
    # create tdis package
    tdis = flopy.mf6.ModflowTdis(
        sim, time_units="DAYS", nper=nper, perioddata=tdis_rc
    )

    # create gwt model
    gwtname = "gwt_" + name
    gwt = flopy.mf6.MFModel(
        sim,
        model_type="gwt6",
        modelname=gwtname,
        model_nam_file=f"{gwtname}.nam",
    )
    gwt.name_file.save_flows = True

    # create iterative model solution and register the gwt model with it
    imsgwt = flopy.mf6.ModflowIms(
        sim,
        print_option="SUMMARY",
        outer_dvclose=hclose,
        outer_maximum=nouter,
        under_relaxation="NONE",
        inner_maximum=ninner,
        inner_dvclose=hclose,
        rcloserecord=rclose,
        linear_acceleration="BICGSTAB",
        scaling_method="NONE",
        reordering_method="NONE",
        relaxation_factor=relax,
        filename=f"{gwtname}.ims",
    )
    sim.register_ims_package(imsgwt, [gwt.name])

    dis = flopy.mf6.ModflowGwtdis(
        gwt,
        nlay=nlay,
        nrow=nrow,
        ncol=ncol,
        delr=delr,
        delc=delc,
        top=top,
        botm=botm,
        idomain=1,
        filename=f"{gwtname}.dis",
    )

    # initial conditions
    ic = flopy.mf6.ModflowGwtic(gwt, strt=0.0, filename=f"{gwtname}.ic")

    # dispersion
    xt3d_off = not xt3d[idx]
    dsp = flopy.mf6.ModflowGwtdsp(
        gwt,
        xt3d_off=xt3d_off,
        diffc=100.0,
        alh=0.0,
        alv=0.0,
        ath1=0.0,
        atv=0.0,
        filename=f"{gwtname}.dsp",
    )

    # constant concentration
    cncs = {0: [[(0, 0, 0), 1.0], [(nlay - 1, 0, 0), 0.0]]}
    cnc = flopy.mf6.ModflowGwtcnc(
        gwt,
        maxbound=len(cncs),
        stress_period_data=cncs,
        save_flows=False,
        pname="CNC-1",
    )

    # mass storage and transfer
    mst = flopy.mf6.ModflowGwtmst(gwt, porosity=0.1)

    # output control
    oc = flopy.mf6.ModflowGwtoc(
        gwt,
        budget_filerecord=f"{gwtname}.cbc",
        concentration_filerecord=f"{gwtname}.ucn",
        concentrationprintrecord=[
            ("COLUMNS", 10, "WIDTH", 15, "DIGITS", 6, "GENERAL")
        ],
        saverecord=[("CONCENTRATION", "LAST"), ("BUDGET", "LAST")],
        printrecord=[("CONCENTRATION", "LAST"), ("BUDGET", "LAST")],
    )
    print(gwt.modelgrid.zcellcenters)
    return sim, None


def eval_transport(sim):
    print("evaluating transport...")

    name = runs[sim.idxsim]
    gwtname = "gwt_" + name

    fpth = os.path.join(sim.simpath, f"{gwtname}.ucn")
    try:
        cobj = flopy.utils.HeadFile(
            fpth, precision="double", text="CONCENTRATION"
        )
        conc = cobj.get_data()
    except:
        assert False, f'could not load data from "{fpth}"'

    # The answer is a linear concentration gradient from 1 to zero
    x = np.array([1.0, -0.25, -0.75, -1.25, -1.75])
    x0 = x[0]
    xe = x[-1]
    c0 = 1.0
    ce = 0.0
    m = (c0 - ce) / (x0 - xe)
    b = c0 - m * x0
    cres = m * x + b
    msg = f"simulated concentrations do not match with known solution. {conc} {cres}"
    assert np.allclose(cres, conc.flatten()), msg

    return


# - No need to change any code below
@pytest.mark.gwt
@pytest.mark.dsp
@pytest.mark.parametrize(
    "idx, run",
    list(enumerate(runs)),
)
def test_gwt_dsp05_noadv(idx, run, tmpdir, testbin):
    # initialize testing framework
    test = testing_framework()

    # build the models
    test.build_mf6_models(build_model, idx, str(tmpdir))

    # run the test model
    test.run_mf6(Simulation(
        str(tmpdir),
        exfunc=eval_transport,
        testbin=testbin,
        idxsim=idx
    ))


def main():
    from conftest import mf6_testbin

    # initialize testing framework
    test = testing_framework()

    # build the models
    # run the test model
    for idx, run in enumerate(runs):
        simdir = os.path.join(
            "autotest-keep", "standalone",
            os.path.splitext(os.path.basename(__file__))[0],
            run,
        )
        test.build_mf6_models(build_model, idx, simdir)
        sim = Simulation(
            simdir,
            exfunc=eval_transport,
            testbin=mf6_testbin,
            idxsim=idx
        )
        test.run_mf6(sim)


if __name__ == "__main__":
    # print message
    print(f"standalone run of {os.path.basename(__file__)}")

    # run main routine
    main()
