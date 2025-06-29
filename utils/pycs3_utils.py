import numpy as np
import matplotlib.pyplot as plt

import pycs3
import pycs3.gen
import pycs3.gen.lc_func
import pycs3.spl.topopt
import pycs3.gen.mrg
import pycs3.gen.splml
import pycs3.regdiff.multiopt
import pycs3.regdiff.rslc


def modify_lcs_based_on_jds(lcs, jd_min=None, jd_max=None, delta_mag=None, delta_jd=None):
    """
    Modify the magnitudes and Julian Dates of light curves based on specified JD ranges and deltas.

    params:
    - lcs (list): List of light curve objects. Each light curve should have numpy arrays: jds, mags, magerrs.
    - jd_min (float, optional): Minimum Julian Date to select for modification. If None, no lower bound.
    - jd_max (float, optional): Maximum Julian Date to select for modification. If None, no upper bound.
    - delta_mag (float, optional): Magnitude shift to apply. If None, no magnitude shift is applied.
    - delta_jd (float, optional): Julian Date shift to apply. If None, no JD shift is applied.

    Returns:
    - None
    """
    for lc in lcs:
        mask = np.ones_like(lc.jds, dtype=bool)  # start with all True

        if jd_min is not None and jd_max is not None:
            mask &= (lc.jds >= jd_min) & (lc.jds <= jd_max)
        elif jd_min is not None:
            mask &= (lc.jds >= jd_min)
        elif jd_max is not None:
            mask &= (lc.jds <= jd_max)
        # if both jd_min and jd_max are None, mask remains all True

        if delta_mag is not None:
            lc.mags[mask] += delta_mag

        if delta_jd is not None:
            lc.jds[mask] += delta_jd


def select_curves_from_names(lcs, names):
    selected = []
    for name in names:
        lcs_filtered = [lc for lc in lcs if lc.object == name]
        if len(lcs_filtered) != 1:
            raise AssertionError('Must have exactly one light curve per name')
        selected.append(lcs_filtered[0])
    return selected


def spl(lcs, knotstep=55, rough=1, bokeps=10., nit=5):
    # optimizing splines attached to curves.
    if rough:
        spline = pycs3.spl.topopt.opt_rough(lcs, nit=1, knotstep=knotstep, verbose=False)
    spline = pycs3.spl.topopt.opt_fine(lcs, nit=nit, knotstep=knotstep, verbose=1, bokeps=bokeps)
    return spline


def attachml_single(lc, ml, autoseasonsgap):
    """
    Our logic for ML models.

    :param lc: a single PyCS3 light curve object
    :param ml: string, in ['None', 'linear', 'quadratic', 'cubic', 'spline_3_fixed_knot', 'spline_3', 'spline_N']
               with N=4,5,6,7,8,.....
    :param autoseasonsgap: float, split ML models in gaps larger than `autoseasonsgap` days.
    :return: None
    """
    if ml == "None":  # I do nothing if there is no microlensing to attach.
        # 2022-06-09: there is a bug in PyCS, the optimization of the offset is not done properly.
        # thus add a polynomial of order 0
        pycs3.gen.polyml.addtolc(lc, nparams=1, autoseasonsgap=autoseasonsgap)
        return
    elif ml == "linear":
        pycs3.gen.polyml.addtolc(lc, nparams=2, autoseasonsgap=autoseasonsgap)
        return
    elif ml == "quadratic":
        pycs3.gen.polyml.addtolc(lc, nparams=3, autoseasonsgap=autoseasonsgap)
        return
    elif ml == "cubic":
        pycs3.gen.polyml.addtolc(lc, nparams=4, autoseasonsgap=autoseasonsgap)
        return
    elif ml == "spline_3_fixed_knot":
        # this is the case where we want a single internal knot, and also want it fixed in the middle.
        curve_length = lc.jds[-1] - lc.jds[0]
        mlbokeps = np.floor(
            curve_length / 2.) - 1  # epsilon (min distance betwen knots) set to about half the curve, i.e. forced in the middle
        pycs3.gen.splml.addtolc(lc, n=2, bokeps=mlbokeps)
    elif ml == "spline_3":
        # this is the case where we want a single internal knot, free to move
        curve_length = lc.jds[-1] - lc.jds[0]
        mlbokeps = np.floor(curve_length / 10.)  # smaller epsilon for more freedom.
        pycs3.gen.splml.addtolc(lc, n=2, bokeps=mlbokeps)
    elif ml.startswith("spline_"):
        order = int(ml.split('_')[1])
        curve_length = lc.jds[-1] - lc.jds[0]
        mlbokeps = np.floor(curve_length / (10. + order))  # smaller epsilon for more freedom.
        pycs3.gen.splml.addtolc(lc, n=order - 1, bokeps=mlbokeps)
    else:
        raise NotImplementedError(ml)


def attachml(lcs, mls, autoseasonsgap):
    """
    adds ml models to each lc in lcs.
    :param lcs: list of PyCS3 curves
    :param mls: list of strings representing ML models, see attachml_single
    :param autoseasonsgap: same as in attachml_single
    :return:
    """
    if not type(mls) is list:
        mls = len(lcs) * [mls]
    else:
        assert len(mls) == len(lcs)
    for lc, ml in zip(lcs, mls):
        attachml_single(lc, ml, autoseasonsgap)


def fit(lcs, ml, knotstep, autoseasonsgap=100, rough=1, figsize=(12, 5), bokeps=10, **kwargs_display):
    attachml(lcs, ml, autoseasonsgap)

    spline = spl(lcs, knotstep, rough=rough, bokeps=bokeps)
    # get time range:
    minn = 1e5
    maxx = 0.
    for lc in lcs:
        jds = lc.jds + lc.timeshift
        minnx = np.min(jds)
        maxxx = np.max(jds)
        # all this for loop because
        # might get different jds sizes.
        if minnx < minn:
            minn = minnx
        if maxxx > maxx:
            maxx = maxxx
    jdr = (minn - 20, maxx + 20)

    kwargs_display_to_pass = {
        'showdelays': True,
        'showlegend': False,
        'showerrorbars': True,
        'collapseref': True,
        'title': '',
        'ax': None,
        'nicefont': False,
    }
    if kwargs_display is not None:
        kwargs_display_to_pass.update(kwargs_display)

    pycs3.gen.lc_func.display(lcs, [spline], figsize=figsize, jdrange=jdr, **kwargs_display_to_pass)


def see(lcs, figsize=(12, 5), print_delays=False):
    pycs3.gen.lc_func.display(lcs, [], figsize=figsize, showdelays=False,
                              showlegend=True, title="",
                              showerrorbars=1, collapseref=1, legendloc='lower left')
    if print_delays:
        print("Time delays:")
        print(pycs3.gen.lc_func.getnicetimedelays(lcs, separator="\n", to_be_sorted=True))
