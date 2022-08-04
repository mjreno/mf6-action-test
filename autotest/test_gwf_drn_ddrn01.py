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
        running_on_CI,
        testing_framework,
        Simulation,
    )
except:
    msg = "modflow-devtools not in PYTHONPATH"
    raise Exception(msg)

paktest = "drn"
budtol = 1e-2

runs = ["drn_ddrn01a", "drn_ddrn01b"]

newton = [False, True]

# run all examples on Travis
continuous_integration = [True for idx in range(len(runs))]

# set replace_exe to None to use default executable
replace_exe = None

# static model data
# spatial discretization
nlay, nrow, ncol = 1, 1, 100
shape3d = (nlay, nrow, ncol)
size3d = nlay * nrow * ncol
xlen = 1000.0
delc, delr = 1.0, xlen / ncol
top, botm = 10.0, 0.0

# temporal discretization
nper = 1
nyears = 10.0
period_data = [(10.0 * nyears, 100, 1.1)]

kh, sy, ss = 10.0, 0.1, 1e-5
h0, h1 = 9.0, 1.0
obs_recarray = {
    "head_obs.csv": [
        ("h1_1_1", "HEAD", (0, 0, 0)),
        ("h1_1_100", "HEAD", (0, 0, ncol - 1)),
    ]
}
# drain data
delev, ddrn = 0.0, h1
dcond = kh * delc * ddrn / (0.5 * delr)
drn_spd = {0: [[(0, 0, ncol - 1), delev, dcond, ddrn]]}
drn_obs = {"drn_obs.csv": [("d1_1_100", "DRN", (0, 0, ncol - 1))]}


def initial_conditions():
    x = np.arange(0, xlen - delr / 2, delr)
    return np.sqrt(h0**2 + x * (h1**2 - h0**2) / (xlen - delr))


def get_model(idxsim, ws, name):
    strt = initial_conditions()
    hdsfile = f"{name}.hds"
    if newton[idxsim]:
        newtonoptions = "NEWTON"
    else:
        newtonoptions = None

    # build the model
    sim = flopy.mf6.MFSimulation(sim_name=name, exe_name="mf6", sim_ws=ws)
    tdis = flopy.mf6.ModflowTdis(sim, nper=nper, perioddata=period_data)
    ims = flopy.mf6.ModflowIms(
        sim,
        print_option="ALL",
        linear_acceleration="BICGSTAB",
        outer_maximum=200,
        inner_maximum=200,
        outer_dvclose=1e-6,
        inner_dvclose=1e-9,
        rcloserecord=[0.01, "strict"],
    )
    gwf = flopy.mf6.ModflowGwf(
        sim, modelname=name, newtonoptions=newtonoptions
    )
    dis = flopy.mf6.ModflowGwfdis(
        gwf,
        nlay=nlay,
        nrow=nrow,
        ncol=ncol,
        delr=delr,
        delc=delc,
        top=top,
        botm=botm,
    )
    npf = flopy.mf6.ModflowGwfnpf(gwf, k=kh, icelltype=1)
    sto = flopy.mf6.ModflowGwfsto(
        gwf, sy=sy, ss=ss, transient={0: True}, iconvert=1
    )
    drn = flopy.mf6.ModflowGwfdrn(
        gwf,
        auxiliary=["ddrn"],
        auxdepthname="ddrn",
        stress_period_data=drn_spd,
        print_input=True,
    )
    drn.obs.initialize(
        filename=f"{name}.drn.obs",
        digits=20,
        print_input=True,
        continuous=drn_obs,
    )
    ic = flopy.mf6.ModflowGwfic(gwf, strt=strt)
    obs_package = flopy.mf6.ModflowUtlobs(
        gwf, digits=20, print_input=True, continuous=obs_recarray
    )
    oc = flopy.mf6.ModflowGwfoc(
        gwf,
        head_filerecord=hdsfile,
        saverecord=[("HEAD", "ALL")],
        printrecord=[("BUDGET", "ALL")],
    )

    return sim


def build_model(idx, dir):
    name = runs[idx]

    # build MODFLOW 6 files
    ws = dir
    sim = get_model(idx, ws, name)

    return sim, None


def eval_disch(sim):
    print("evaluating drain discharge...")

    # MODFLOW 6 drain discharge results
    fpth = os.path.join(sim.simpath, "drn_obs.csv")
    try:
        tc = np.genfromtxt(fpth, names=True, delimiter=",")
    except:
        assert False, f'could not load data from "{fpth}"'

    # MODFLOW 6 head results
    fpth = os.path.join(sim.simpath, "head_obs.csv")
    try:
        th0 = np.genfromtxt(fpth, names=True, delimiter=",")
    except:
        assert False, f'could not load data from "{fpth}"'

    # calculate the drain flux analytically
    xdiff = th0["H1_1_100"] - delev
    f = drain_smoothing(xdiff, ddrn, newton=newton[sim.idxsim])
    tc0 = f * dcond * (delev - th0["H1_1_100"])

    # calculate maximum absolute error
    diff = tc["D1_1_100"] - tc0
    diffmax = np.abs(diff).max()
    dtol = 1e-6
    msg = f"maximum absolute discharge difference ({diffmax}) "

    # write summary
    fpth = os.path.join(
        sim.simpath, f"{runs[sim.idxsim]}.disc.cmp.out"
    )
    f = open(fpth, "w")
    line = f"{'TOTIM':>15s}"
    line += f" {'DRN':>15s}"
    line += f" {'UZF':>15s}"
    line += f" {'DIFF':>15s}"
    f.write(line + "\n")
    for i in range(diff.shape[0]):
        line = f"{tc['time'][i]:15g}"
        line += f" {tc['D1_1_100'][i]:15g}"
        line += f" {tc0[i]:15g}"
        line += f" {diff[i]:15g}"
        f.write(line + "\n")
    f.close()

    if diffmax > dtol:
        sim.success = False
        msg += f"exceeds {dtol}"
        assert diffmax < dtol, msg
    else:
        sim.success = True
        print("    " + msg)

    return


def drain_smoothing(xdiff, xrange, newton=False):
    sat = xdiff / xrange
    if not newton:
        f = sat.copy()
    else:
        cof1 = -1.0 / (xrange) ** 3
        cof2 = 2.0 / (xrange) ** 2
        f = cof1 * xdiff**3 + cof2 * xdiff**2
    f[sat < 0] = 0
    f[sat > 1] = 1
    return f


# - No need to change any code below
@pytest.mark.gwf
@pytest.mark.drn
@pytest.mark.parametrize(
    "idx, run",
    list(enumerate(runs)),
)
def test_gwf_drn_ddrn01(idx, run, tmpdir, testbin):
    # determine if running on CI infrastructure
    is_CI = running_on_CI()
    r_exe = None
    if not is_CI:
        if replace_exe is not None:
            r_exe = replace_exe

    # initialize testing framework
    test = testing_framework()

    # build the models
    test.build_mf6_models(build_model, idx, str(tmpdir))

    # run the test model
    if is_CI and not continuous_integration[idx]:
        return
    test.run_mf6(
        Simulation(
            str(tmpdir),
            exfunc=eval_disch,
            exe_dict=r_exe,
            testbin=testbin,
            idxsim=idx
        )
    )


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
            exfunc=eval_disch,
            exe_dict=replace_exe,
            testbin=mf6_testbin,
            idxsim=idx
        )
        test.run_mf6(sim)
    return


# use python testmf6_drn_ddrn01.py
if __name__ == "__main__":
    # print message
    print(f"standalone run of {os.path.basename(__file__)}")

    # run main routine
    main()
