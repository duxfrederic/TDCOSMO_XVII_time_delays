
# Release of time delays from VST and 2p2


[![DOI](https://img.shields.io/badge/DOI-10.1051%2F0004--6361%2F202553807-blue)](https://doi.org/10.1051/0004-6361/202553807)


This repository contains the extracted photometry, and time delay estimation scripts.

## Photometric extraction
This is the most critical part, as, especially with short monitoring baselines, different photometric extractions
can yield widely different time delays and uncertainty.
However, this part is very demanding in terms of CPU time and storage, so it is not reproduced in this repository.
However, the raw data necessary to reproduce this step are slowly becoming public in the ESO archives.  

### Data pre-reduction
We performed standard bias and subtraction, and division by a daily master-sky-flat.
For VST, additional processing was undertaken for creating mosaic images, 
but these are not relevant to the time delay estimation part.

### Light curve extraction
Performed with this software: https://github.com/duxfrederic/lightcurver. 
The extracted daily photometric values were then systematically dumped into an `sqlite3` database,
in this repository found at `data/photometry.db`.

## Time delay estimation
We use the `PyCS3` toolbox, specifically spline fits, for time delay estimation.
Sadly, we do not have a bayesian framework for delay estimation: the median values and their covariance depend
enormously on the chosen initial guess and meta-parameters. 
It's a bit of a nightmare, and I have tried a lot of different things over the past 2 years; 
having settled on what you'll find below.

### How to use: this repository
Define a working directory in `config.yaml`. I recommend some fast SSD storage if available, because 
`PyCS3` will write thousands of small files. If you intend to run _all_ the mocks, 
you will need about 60 GB of free storage.

Then, 
```bash
cd /your/clone/of/this/repository
# Make sure you have pyyaml installed before running the setup. If not, something like pip install pyyaml will do the trick.
./setup.py
```
will create a virtual environment, clone my branch of `PyCS3`, all in your working directory, and optionally run
the `initial_guess.ipynb` notebook to create pickled light curves ready for use in the next steps.

You can also play with the initial guess through jupyter lab, installed in the environment by `setup.py`:
```bash
source /your_yaml_defined_workdir/td_release_env/bin/activate
jupyter lab
```

To prepare the scene for the subsequent scripts, do
```bash
source  /your_yaml_defined_workdir/td_release_env/bin/activate
cd pycs3_scripts
python prepare_pycs3_runs.py
```
Next, head to `/your/working/directory/run_dir`.
You can run the mocks and analysis with the many `run_*.sh` files (one per lens) you will find there.

### Comments about each component
#### Light curve pre-processing and choice of spline parameters
We try spline parameters that fit the curves well in `initial_guess.ipynb`.
For each lens, this notebook saves pickle files (load-able by `PyCS3`) containing the pre-processed light curves,
and parameters/delay values at `data/initial_guess.json`.

#### PyCS3 scripts
These were adapted (mostly copied) from [here](https://gitlab.com/cosmograil/PyCS3/-/tree/master/scripts?ref_type=heads).
The main difference is the ability to add different microlensing models per curve, as it was needed sometimes.
(When only one of the curves is clearly strongly affected by microlensing).
Next, the correlation script (`4c_covariance_matrices.py`) does some sigma clipping 
(so did the original marginalisation in prior data releases), trying to clip just enough so that the standard deviation
of the resulting distribution becomes representative of its width (84 - 16 percentile values).
In most cases, this results in the clipping of 0-3% of the mocks. 

### Addressing multi-modalities
The case of `J0659` was very much split between two possibilities, such that you will find two separate runs, one per possibility.
Other cases with potential multi-modalities include:
- J0924: the C curve is somewhat compatible with 0 delay, but I do not consier it to be reasonable. Thus I only considered the shift at ~-17 days.
- J0259: There might be another solution for D at -40 days, but it requires more modulation, and I cannot really see it playing with the curves manually. Sticking to the solution at -15 days.
- DES2038: AC was multi modal, and the negative solution was chosen in TDCOSMO XVI.
- J2205: AC can be either negative or positive, but both cases are largely compatible with 0.  
