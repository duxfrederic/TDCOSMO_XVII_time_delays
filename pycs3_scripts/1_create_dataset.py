"""
Setup the config file and organise the lens folder.
If you have more than 4 images, you might need to modify the config file and rerun this script.
"""
import argparse as ap
import logging
import os
import sys
from shutil import copyfile
from pathlib import Path

here = Path(__file__).parent

loggerformat = '%(levelname)s: %(message)s'
logging.basicConfig(format=loggerformat, level=logging.INFO)


def replace_line(filename, linetobereplaced, newline):
    with open(filename, 'r') as file:
        lines = file.readlines()

    replaced = False
    for i, line in enumerate(lines):
        if line.strip() == linetobereplaced:
            lines[i] = newline + '\n'
            replaced = True
            break

    if replaced:
        with open(filename, 'w') as file:
            file.writelines(lines)
    else:
        raise RuntimeError("No replacement was made!!! pattern:", linetobereplaced,
                           "file:", filename )


def generate_string_pairs(strings):
    import itertools
    pairs = []
    for pair in itertools.combinations(strings, 2):
        pairs.append(''.join(pair))
    return pairs


def create_dataset(dataname, lclabels, MLlist, knotlist, timeshifts_ini, tsrand, work_dir='./', TEST=False):
    """

        dataname:
           lensname_telescope kind of string
        initial_guess:
            dictionary of timeshifts:
                {'lcname': timeshift (float)}

        workdir:
           Path or string, where are we working?

    """
    scriptsdir = Path(__file__).parent
    work_dir = Path(work_dir)
    data_directory = work_dir / "data"
    pickle_directory = work_dir / "pkl"   # lcs will already be there
    config_directory = work_dir / "config"
    simu_directory = work_dir / "Simulation"
    lens_directory = simu_directory / dataname
    figure_directory = lens_directory / "figure"
    report_directory = lens_directory / "report"

    for dd in [work_dir, data_directory,
               pickle_directory, config_directory,
               simu_directory, lens_directory,
               figure_directory, report_directory]:
        dd.mkdir(exist_ok=True)

    configfile = config_directory / f'config_{dataname}.py'

    # if the config file does not exist, we will write these paths
    # into the new config file.
    linestowrite = {
                "work_dir": work_dir,
                "data_directory": data_directory,
                "pickle_directory": pickle_directory,
                "simu_directory": simu_directory,
                "config_directory": config_directory,
                "lens_directory": lens_directory,
                "figure_directory": figure_directory,
                "report_directory": report_directory,
                "data": pickle_directory / f'{dataname}.pkl'
    }

    # using this little helper:
    def write_config(cfile, paths):
        cfile.write("# Automatically generated paths:\n")
        for key, path in paths.items():

            end = '/' if not '.pkl' in str(path) else ''
            cfile.write(f"{key} = '{path}{end}'\n")

    # classic scenarios:
    n_curve = len(lclabels)
    if 2 <= n_curve <= 4:
        copyfile(here / 'default_configs' / f"config_default_{['double', 'triple', 'quads'][n_curve - 2]}.py",
                 configfile)
        with configfile.open('a') as cfile:
            write_config(cfile, linestowrite)
        print("Default config file created! You might want to change the default parameters.")
    else:  # not classic
        print("Warning: do you have a quad, a triple or a double?")
        print("Make sure you update lcs_label in the config file! I'll copy the double template for this time!")
        new_config_path = config_directory / f"config_{dataname}.py"
        copyfile("config_default_double.py", new_config_path)
        with new_config_path.open('a') as cfile:
            write_config(cfile, linestowrite)
        print("Please change the default parameters according to your object and rerun this script.")
        sys.exit()

    # NOW TWEAKING THE CONFIG FILES
    # start with the names
    tdlabels = generate_string_pairs(lclabels)
    replace_line(configfile,
                 "#PLACEHOLDERLCLABELS",
                 f"lcs_label = {lclabels}")
    replace_line(configfile,
                 "#PLACEHOLDERDELAYLABELS",
                 f"delay_labels = {tdlabels}")
    # now our initial guess, already embedded in the timeshift of the LCs
    # from the jupyter notebook:
    maxtd = max([abs(td) for td in timeshifts_ini])
    if tsrand is None:
        truetsr = max(0.2 * maxtd, 10.0)
    else:
        truetsr = tsrand
    replace_line(configfile,
                 "truetsr = 10.0  # Range of true time delay shifts when drawing the mock curves",
                 f"truetsr = {truetsr:.02f}")
    replace_line(
       configfile,
       "tsrand = 10.0  # Random shift of initial condition for each simulated lc in [initcond-tsrand, initcond+tsrand]",
       f"tsrand = {truetsr:.02f}"
    )
    if TEST:
        replace_line(configfile,
                     "ncopy = 20 #number of copy per pickle",
                     "ncopy=2")
        replace_line(configfile,
                     "ncopypkls = 25 #number of pickle",
                     "ncopypkls=3")
        replace_line(configfile,
                     "nsimpkls = 40 #number of pickle",
                     "nsimpkls=5")
        replace_line(configfile,
                     "nsim = 20 #number of copy per pickle",
                     "nsim=5")

    # use the right ML and knot steps:
    # MLlist, knotlist
    replace_line(configfile,
                 "nmlspl = [0,1,2,3]  #nb_knot - 1, used only if forcen == True, 0, means no microlensing",
                 f"nmlspl = {MLlist}")

    replace_line(configfile,
                 "knotstep = [15,25,35,45] #give a list of the parameter you want",
                 f"knotstep = {knotlist}")

    replace_line(configfile,
                 "#PLACEHOLDERTIMESHIFTS",
                 f"timeshifts = {timeshifts_ini}")
