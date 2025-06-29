from pathlib import Path
from subprocess import call
import numpy as np
from shutil import copy
import sys

# path stuff ...let's keep it simple albeit not optimal, relative to root of repo.
repo_path = Path(__file__).parent.parent
sys.path.append(str(repo_path))
config_file = repo_path / 'config.yaml'
initial_guess_path = repo_path / 'data' / 'initial_guess.json'

# loading initial guess db
from utils.json_db import Database
from utils.config import read_config

config = read_config(config_file)

workdir = Path(config['workdir'])
run_dir = workdir / 'run_dir'
pkl_dir = run_dir / 'pkl'
configdir = run_dir / 'config'

db = Database(initial_guess_path, pkl_dir)

# loading the modified pycs3 dataset creator
import importlib
create_dataset = importlib.import_module('1_create_dataset', package=None).create_dataset

alldb = db.get()


# create configs
for key, item in alldb.items():
    print(f"Creating directory structure for {key}")

    # okkkk fine sticking with the PyCS3 script convention,
    # dataname = obj_inst
    inst = key.split('_')[1].replace('.rdb', '').replace('.pkl', '')
    obj = key.split('_')[0]

    dataname = f"{obj}_{inst}"

    ddb = db.get([key])
    labels = sorted(list(ddb['curves'].keys()))
    timeshifts = [ddb['curves'][key]['timeshift'] for key in labels]
    magshifts = [ddb['curves'][key]['magshift'] for key in labels]
    
    if 'mltouse' not in ddb:
        print("No indication of which MLs to use!!!")
        continue
    else:
        mltouse = ddb['mltouse']

    if 'knotstouse' not in ddb:
        print("No indication of which knot steps to use!!!")
        # we do not proceed
        continue
    else:
        knotstouse = ddb['knotstouse']
    tsrand = ddb.get('tsrand', None)
    create_dataset(dataname, labels, mltouse, knotstouse, timeshifts_ini=timeshifts,
                   tsrand=tsrand, work_dir=run_dir, TEST=False)

scripts = [
    "2_fit_spline.py",
    "3a_generate_tweakml.py",
    "3b_draw_copy_mocks.py",
    "3c_optimise_copy_mocks.py",
    "3d_check_statistics.py",
    "4a_plot_results.py",
    "4b_marginalise_spline.py",
    "4c_covariance_matrices.py"
]

runscripttemplate = "#!/bin/bash\n"
for script in scripts:
    copy(script, str(run_dir))
    runscripttemplate += f"python {script} {{obj}} {{inst}}\n"

configdir.mkdir(exist_ok=True, parents=True)

# create run files
for key, item in alldb.items():
    obj = key.split('_')[0]
    inst = key.split('_')[1].replace('.rdb', '').replace('.pkl', '')
    dataname = f"{obj}_{inst}"
    cfile = configdir / f"config_{dataname}.py"
    if cfile.exists():
        scr = runscripttemplate.format(obj=obj, inst=inst)
        runf = f"run_{obj}_{inst}.sh"
        with open(run_dir / runf, 'w') as f:
            f.write(scr)
            f.write('\n')
            print('wrote, ', run_dir / runf)
        call(['chmod', '+x', str(run_dir / runf)])
    else:
        print('file', cfile, 'does not exist.')

