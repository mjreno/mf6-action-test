import os
import pathlib
import shutil
import sys
import time

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
        get_example_basedir,
        get_example_dirs,
        get_home_dir,
        get_select_dirs,
        get_select_packages,
        is_directory_available,
        set_mf6_regression,
        get_namefiles,
        model_setup,
        set_teardown_test,
        Simulation,
        MFTestContext,
    )
except:
    msg = "modflow-devtools not in PYTHONPATH"
    raise Exception(msg)

# find path to examples directory
home = get_home_dir()


def get_mf5to6_models():
    """
    Get a list of test models
    """

    # determine if test directory exists
    dir_available = is_directory_available(example_basedir)
    if not dir_available:
        return []

    # list of example files to exclude
    exclude = (None,)

    # write a summary of the files to exclude
    print("list of tests to exclude:")
    for idx, ex in enumerate(exclude):
        print(f"    {idx + 1}: {ex}")

    # build list of directories with valid example files
    if example_basedir is not None:
        example_dirs = get_example_dirs(
            example_basedir,
            exclude,
            prefix="test",
            find_sim=False,
        )
    else:
        example_dirs = []

    # determine if only a selection of models should be run
    select_dirs = None
    select_packages = None
    for idx, arg in enumerate(sys.argv):
        if arg.lower() == "--sim":
            if len(sys.argv) > idx + 1:
                select_dirs = sys.argv[idx + 1 :]
                break
        elif arg.lower() == "--pak":
            if len(sys.argv) > idx + 1:
                select_packages = sys.argv[idx + 1 :]
                select_packages = [item.upper() for item in select_packages]
                break

    # determine if the selection of model is in the test models to evaluate
    if select_dirs is not None:
        example_dirs = get_select_dirs(select_dirs, example_dirs)
        if len(example_dirs) < 1:
            msg = "Selected models not available in test"
            print(msg)

    # determine if the specified package(s) is in the test models to evaluate
    if select_packages is not None:
        example_dirs = get_select_packages(
            select_packages, example_basedir, example_dirs
        )
        if len(example_dirs) < 1:
            msg = "Selected packages not available ["
            for idx, pak in enumerate(select_packages):
                msg += f"{pak}"
                if idx + 1 < len(select_packages):
                    msg += ", "
            msg += "]"
            print(msg)

    return example_dirs


find_dir = "modflow6-testmodels"
example_basedir = get_example_basedir(home, find_dir, subdir="mf5to6")

if example_basedir is not None:
    assert os.path.isdir(example_basedir)


sfmt = "{:25s} - {}"


def run_mf5to6(sim, testdir):
    """
    Run the MODFLOW 6 simulation and compare to existing head file or
    appropriate MODFLOW-2005, MODFLOW-NWT, MODFLOW-USG, or MODFLOW-LGR run.

    """
    src = os.path.join(example_basedir, sim.name)

    # set lgrpth to None
    lgrpth = None

    # determine if compare directory exists in directory or if mflgr control
    # file is in directory
    listdir = os.listdir(src)
    for value in listdir:
        fpth = os.path.join(src, value)
        if os.path.isfile(fpth):
            ext = os.path.splitext(fpth)[1]
            if ".lgr" in ext.lower():
                lgrpth = fpth

    print("Copying files to working directory")
    # copy lgr files to working directory
    if lgrpth is not None:
        npth = lgrpth
        model_setup(lgrpth, testdir)
    # copy MODFLOW-2005, MODFLOW-NWT, or MODFLOW-USG files to working directory
    else:
        npths = get_namefiles(src)
        if len(npths) < 1:
            msg = f"No name files in {src}"
            print(msg)
            assert False
        npth = npths[0]
        model_setup(npth, testdir)

    # run the mf5to6 converter
    print(sfmt.format("using executable", exe))
    nmsg = "Program terminated normally"
    try:
        nam = os.path.basename(npth)
        success, buff = flopy.run_model(
            exe,
            nam,
            model_ws=testdir,
            silent=False,
            report=True,
            normal_msg=nmsg,
            cargs="mf6",
        )
        msg = sfmt.format("MODFLOW 5 to 6 run", nam)
        if success:
            print(msg)
        else:
            print("ERROR: " + msg)
    except:
        msg = sfmt.format("MODFLOW 5 to 6 run", nam)
        print("ERROR: " + msg)
        success = False

    assert success, msg

    # standard setup
    src = testdir
    dst = os.path.join(testdir, "compare")
    sim.setup(src, dst)

    # standard comparison run
    sim.run()
    sim.compare()
    sim.teardown()


def set_make_comparison(test, ctx):
    compare_tests = {
        "testPr2": ("6.2.1",),
        "testUzfLakSfr": ("6.2.1",),
        "testUzfLakSfr_laketable": ("6.2.1",),
        "testWetDry": ("6.2.1",),
    }
    make_comparison = True
    if test in compare_tests.keys():
        version = ctx.get_mf6_version()
        print(f"MODFLOW version='{version}'")
        version = ctx.get_mf6_version(version="mf6-regression")
        print(f"MODFLOW regression version='{version}'")
        if version in compare_tests[test]:
            make_comparison = False
    return make_comparison

@pytest.mark.gwt
@pytest.mark.gwf
@pytest.mark.slow
@pytest.mark.parametrize(
    "test",
    get_mf5to6_models(),
)
def test_z02_testmodels_mf5to6(test, tmpdir, testbin, mf6testctx):
    global exe
    exe = mf6testctx.get_target_dictionary()["mf5to6"]

    # run the test model
    print(f"test={test}")
    run_mf5to6(
        Simulation(
            test,
            testbin=testbin,
            mf6_regression=set_mf6_regression(),
            cmp_verbose=False,
            make_comparison=set_make_comparison(test, mf6testctx),
        ),
        str(tmpdir)
    )


def main():
    from conftest import mf6_testbin

    # write message
    tnam = os.path.splitext(os.path.basename(__file__))[0]
    msg = f"Running {tnam} test"
    print(msg)

    ctx = MFTestContext(testbin=mf6_testbin)

    # run the test models
    for test in get_mf5to6_models():
        simdir = os.path.join(
            "autotest-keep", "standalone",
            os.path.splitext(os.path.basename(__file__))[0],
            test,
        )
        test_z01_testmodels_mf6(test, simdir, mf6_testbin, ctx)
        if set_teardown_test():
            shutil.rmtree(simdir, ignore_errors=True)


if __name__ == "__main__":

    print(f"standalone run of {os.path.basename(__file__)}")

    # run main routine
    main()
