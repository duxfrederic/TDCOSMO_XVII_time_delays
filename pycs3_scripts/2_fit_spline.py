"""
This script fit spline and regression difference to the data. This original fit will be used to create the generative noise model.
You can tune the spline and regrediff parameters from the config file.
"""
import argparse as ap
import importlib
import logging
import os
import sys

import numpy as np

import pycs3.gen.lc_func
import pycs3.gen.mrg
import pycs3.gen.stat
import pycs3.gen.util
import pycs3.pipe.pipe_utils as ut

loggerformat='%(levelname)s: %(message)s'
logging.basicConfig(format=loggerformat,level=logging.INFO)


def main(lensname, dataname, work_dir='./'):
    sys.path.append(work_dir + "config/")
    print(sys.path)
    config = importlib.import_module("config_" + lensname + "_" + dataname)

    figure_directory = config.figure_directory + "spline_and_residuals_plots/"
    if not os.path.isdir(figure_directory):
        os.mkdir(figure_directory)

    for i, lc in enumerate(config.lcs_label):
        print("I will aplly a initial shift of : %2.4f days for %s" % (
            config.timeshifts[i], config.lcs_label[i]))

    # Do the optimisation with the splines
    if config.mltype == "splml":
        if config.forcen:
            ml_param = config.nmlspl
            string_ML = "nmlspl"
        else:
            ml_param = config.mlknotsteps
            string_ML = "knml"
    elif config.mltype == "polyml":
        ml_param = config.degree
        string_ML = "deg"
    else:
        raise RuntimeError("I don't know your microlensing type. Choose 'polyml' or 'spml'.")
    chi2 = np.zeros((len(config.knotstep), len(ml_param)))
    dof = np.zeros((len(config.knotstep), len(ml_param)))
    print(string_ML, ml_param)

    for i, kn in enumerate(config.knotstep):
        for j, ml in enumerate(ml_param):
            print("knot param:", kn)
            print(("ML param", 'no', j, ml))
            lcs = pycs3.gen.util.readpickle(config.data)
            if config.magshift is None :
                magsft = [-np.median(lc.getmags()) for lc in lcs]
            else :
                magsft = config.magshift
            pycs3.gen.lc_func.applyshifts(lcs, config.timeshifts, magsft) #remove median and set the time shift to the initial guess
            if ml != 0:
                config.attachml(lcs, ml)  # add microlensing

            for lc in lcs:
                print(lc.timeshift)
            spline = config.spl1(lcs, kn=kn)
            pycs3.gen.mrg.colourise(lcs)
            rls = pycs3.gen.stat.subtract(lcs, spline)
            dofsml = {
                'quadratic':0,
                'linear': 0,
                'None': 0,
                'cubic': 0,
                'spline_3':1,
                'spline_3_fixed_knot':1,
                'spline_4':2,
                'spline_5':3,
                'spline_6':4,
                'spline_7':5,
                'spline_8':6,
                'spline_9':7,
                'spline_10':8,
                'spline_11':9,
                'spline_12':10,
                'spline_13':11,
                'spline_14':12
                }
            if type(ml) is list:
                assert len(ml) == len(rls), 'mismatch between the provided list of MLs and curves (number of)'
            elif type(ml) is str:
                ml = len(rls) * [ml]  # same ml for every curve
            else:
                raise AssertionError('The provided ml is not what is should be:', ml, '. Should be str (e.g. "linear") or list (e.g. ["linear", "quadratic" ...])')
            dofs = sum([ pycs3.gen.stat.compute_dof_spline([rl], kn, dofsml[mltype]) for rl, mltype in zip(rls, ml)])
            chi2[i, j] = pycs3.gen.stat.compute_chi2(rls, kn, dofs)
            dof[i, j] = dofs

            if config.display:
                pycs3.gen.lc_func.display(lcs, [spline], showlegend=True, showdelays=True, filename="screen")
                pycs3.gen.stat.plotresiduals([rls])
            else:
                pycs3.gen.lc_func.display(lcs, [spline], showlegend=True, showdelays=True,
                                          filename=figure_directory +  f"spline_fit_ks{kn}_{string_ML}{ml}.png")
                pycs3.gen.stat.plotresiduals([rls], filename=figure_directory + f"residual_fit_ks{kn}_{string_ML}{ml}.png")

            # and write data, again
            if not os.path.isdir(config.lens_directory + config.combkw[i, j]):
                os.mkdir(config.lens_directory + config.combkw[i, j])

            pycs3.gen.util.writepickle((lcs, spline), config.lens_directory + f"{config.combkw[i, j]}/initopt_{dataname}_ks{kn}_{string_ML}{ml}.pkl")

    # Write the report :
    print("Report will be writen in " + config.lens_directory + 'report/report_fitting.txt')

    f = open(config.lens_directory + 'report/report_fitting.txt', 'w')
    f.write('Measured time shift after fitting the splines : \n')
    f.write('------------------------------------------------\n')

    for i, kn in enumerate(config.knotstep):
        f.write('knotstep : %i' % kn + '\n')
        f.write('\n')
        for j, ml in enumerate(ml_param):

            # same as before, could be that we applied a different ML on each curve.
            if type(ml) is list:
                assert len(ml) == len(rls), 'mismatch between the provided list of MLs and curves (number of)'
            elif type(ml) is str:
                ml = len(rls) * [ml]  # same ml for every curve
            else:
                raise AssertionError('The provided ml is not what is should be:', ml, '. Should be str (e.g. "linear") or list (e.g. ["linear", "quadratic" ...])')            

            lcs, spline = pycs3.gen.util.readpickle(config.lens_directory + f"{config.combkw[i, j]}/initopt_{dataname}_ks{kn}_{string_ML}{ml}.pkl", verbose=False)
            delay_pair, delay_name = ut.getdelays(lcs)
            f.write(f"Micro-lensing {string_ML} = {ml}" + "     Delays are " + str(delay_pair) + " for pairs " +
                    str(delay_name) + '. Chi2 Red : %2.5f ' % chi2[i, j] + ' DoF : %i \n' % dof[i, j])

        f.write('\n')


    starting_point = []
    for i in range(len(config.timeshifts)):
        for j in range(len(config.timeshifts)):
            if i >= j:
                continue
            else:
                starting_point.append(config.timeshifts[j] - config.timeshifts[i])

    f.write('Starting point used : ' + str(starting_point) + " for pairs " + str(delay_name) + '\n')
    f.close()


if __name__ == '__main__':
    parser = ap.ArgumentParser(prog="python {}".format(os.path.basename(__file__)),
                               description="Fit spline and regdiff on the data.",
                               formatter_class=ap.RawTextHelpFormatter)
    help_lensname = "name of the lens to process"
    help_dataname = "name of the data set to process (Euler, SMARTS, ... )"
    help_work_dir = "name of the working directory"
    parser.add_argument(dest='lensname', type=str,
                        metavar='lens_name', action='store',
                        help=help_lensname)
    parser.add_argument(dest='dataname', type=str,
                        metavar='dataname', action='store',
                        help=help_dataname)
    parser.add_argument('--dir', dest='work_dir', type=str,
                        metavar='', action='store', default='./',
                        help=help_work_dir)
    args = parser.parse_args()
    main(args.lensname, args.dataname, work_dir=args.work_dir)
