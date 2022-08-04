import os
import sys
import shutil

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
        set_teardown_test,
        Simulation,
        MFTestContext,
    )
except:
    msg = "modflow-devtools not in PYTHONPATH"
    raise Exception(msg)

# find path to modflow6-examples directory
home = get_home_dir()

# get example_basedir
find_dir = "modflow6-examples"
example_basedir = get_example_basedir(home, find_dir, subdir="examples")


def get_mf6_models():
    """
    Get a list of test models
    """

    # determine if examples directory exists
    dir_available = is_directory_available(example_basedir)
    if not dir_available:
        return []

    # determine if running on travis
    is_CI = "CI" in os.environ

    # tuple of example files to exclude
    exclude = ("ex-gwf-csub-p02c",)

    # update exclude
    if is_CI:
        exclude_CI = (None,)
        exclude = exclude + exclude_CI
    exclude = list(exclude)

    # write a summary of the files to exclude
    print("list of tests to exclude:")
    for idx, ex in enumerate(exclude):
        print(f"    {idx + 1}: {ex}")

    # build list of directories with valid example files
    if example_basedir is not None:
        example_dirs = get_example_dirs(example_basedir, exclude, prefix="ex-")
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
            for pak in select_packages:
                msg += f" {pak}"
            msg += "]"
            print(msg)

    return example_dirs


def run_mf6(sim, testdir):
    """
    Run the MODFLOW 6 simulation and compare to existing head file or
    appropriate MODFLOW-2005, MODFLOW-NWT, MODFLOW-USG, or MODFLOW-LGR run.

    """
    print(os.getcwd())
    src = os.path.join(example_basedir, sim.name)
    sim.setup(src, testdir)
    sim.run()
    sim.compare()
    sim.teardown()


def set_make_comparison(test, ctx):
    compare_tests = {
        "ex-gwf-capture": ("6.2.1",),
        "ex-gwf-sagehen": ("6.2.1",),
        "ex-gwf-sfr-p01b": ("6.2.1",),
        "ex-gwf-nwt-p02a": ("6.2.1",),
        "ex-gwf-lak-p01": ("6.2.1",),
        "ex-gwf-lak-p02": ("6.2.1",),
        "ex-gwf-nwt-p02b": ("6.2.1",),
        "ex-gwf-advtidal": ("6.2.1",),
        "ex-gwf-sfr-p01": ("6.2.1",),
        "ex-gwf-lgr": ("6.2.2",),
        "ex-gwt-rotate": ("6.2.2",),
        "ex-gwtgwt-mt3dms-p10": ("6.2.2",),
    }
    make_comparison = True
    if test in compare_tests.keys():
        version = ctx.get_mf6_version()
        print(f"MODFLOW version='{version}'")
        version = ctx.get_mf6_version(version="mf6-regression")
        print(f"MODFLOW regression version='{version}'")
        if version in compare_tests[test]:
            print(
                f"Test {test} does not run with versions {compare_tests[test]}"
            )
            print(
                f"Skipping regression test of sim {test} because the version is {version}"
            )
            make_comparison = False
    return make_comparison


@pytest.mark.gwt
@pytest.mark.gwf
@pytest.mark.slow
@pytest.mark.parametrize(
    "test",
    get_mf6_models(),
)
def test_z03_examples(test, tmpdir, testbin, mf6testctx):
    # run the test model
    print(f"test={test}")
    run_mf6(
        Simulation(
            test,
            testbin=testbin,
            mf6_regression=True,
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
    for test in get_mf6_models():
        simdir = os.path.join(
            "autotest-keep", "standalone",
            os.path.splitext(os.path.basename(__file__))[0],
            test,
        )
        test_z03_examples(test, simdir, mf6_testbin, ctx)
        if set_teardown_test():
            shutil.rmtree(simdir, ignore_errors=True)


if __name__ == "__main__":

    print(f"standalone run of {os.path.basename(__file__)}")

    # run main routine
    main()
