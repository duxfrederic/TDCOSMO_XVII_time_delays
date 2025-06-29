import sqlite3
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict

from pycs3.gen.lc import LightCurve

from utils.pycs3_utils import spl


def detect_outliers(lcs, sigma_threshold=2.5, debug=False, aesthetic_sigma=5):

    outliers = []
    for lc in lcs:
        # fit a spline to the data
        sp = spl([lc], nit=1, rough=1, knotstep=20)

        # calculate the residuals of the spline fit
        residuals = (lc.mags - sp.eval(lc.jds))
        residuals_norm = residuals / lc.magerrs

        sigma = np.std(residuals)

        # find points outside the envelope around the spline
        outliers.extend(np.where(np.abs(residuals_norm) > sigma_threshold)[0])
        # this one is for aesthetics:
        outliers.extend(np.where(np.abs(residuals) > aesthetic_sigma * sigma)[0])
        if debug:
            plt.figure()
            plt.plot(lc.jds, lc.mags, '.')
            plt.plot(lc.jds, sp.eval(lc.jds), '-')
            plt.waitforbuttonpress()

    return list(set(outliers))


class CurveLoader:
    def __init__(self, photometry_db_path):
        self.photometry_db_path = photometry_db_path

    def query_db(self, query):
        """
        """
        conn = sqlite3.connect(self.photometry_db_path)
        cursor = conn.cursor()
        cursor.execute(query)
        data = cursor.fetchall()
        conn.close()
        return data

    def query_photometry_by_image(self, conditions):
        """
        Executes an SQLite query on a photometry database and returns the results grouped by 'image' column.

        Parameters:
        photometry_db_path (str): Path to the SQLite database file.
        conditions (str): Conditions to include in the WHERE clause of the SQL query.

        Returns:
        dict: A dictionary where each key is an 'image' label and each value is a tuple of three NumPy arrays (mjds, mags, mag_errs).
        """
        query = f"SELECT image, mjd, mag, mag_scatter, mag_fisher, telescope FROM photometry WHERE {conditions} order by mjd"
        data = self.query_db(query)

        grouped_data = defaultdict(list)
        for row in data:
            grouped_data[row[0]].append(row[1:])

        result = {}
        for image, values in grouped_data.items():
            values = np.array(values)
            mjds = np.array(values[:, 0], dtype=float)
            mags = np.array(values[:, 1], dtype=float)
            mag_scatter = np.array(values[:, 2], dtype=float)
            mag_fisher = np.array(values[:, 3], dtype=float)
            telescopes = values[:, 4]

            # mag_scatter can be None
            bad = np.where(np.isnan(mag_scatter))
            if len(bad[0]) > 10:
                print(f'wow, high fraction of None in mag scatter! for image {image} of query "{conditions}"')
            mag_scatter[bad] = 0.2
            mag_errs = 0.5 * (mag_scatter + mag_fisher)
            result[image] = (mjds, mags, mag_errs, telescopes)

        return result

    def get_pycs3_curves(self, lens, max_scatter=0.2, max_seeing=2.9, cutmask=True, sigma_outlier=2.5, telescope=None):
        conditions = f"lens='{lens}' and mag_scatter<{max_scatter} and seeing<{max_seeing}"
        if telescope is not None:
            if type(telescope) is str:
                conditions += f" and telescope='{telescope}'"
            elif type(telescope) is list:
                conditions += " and (" + ' or '.join([f"telescope='{tel}'" for tel in telescope]) + ')'
        print(conditions)
        res = self.query_photometry_by_image(conditions=conditions)
        telescopes = self.query_db(f"select distinct(telescope) from photometry where lens='{lens}' order by mjd")
        dataset_name = '+'.join([t[0] for t in telescopes])

        CB_color_cycle = iter(['#377eb8', '#ff7f00', '#4daf4a',
                               '#f781bf', '#a65628', '#984ea3',
                               '#999999', '#e41a1c', '#dede00'])
        lcs = []
        for key, tupl in res.items():
            lc = LightCurve(plotcolour=next(CB_color_cycle), object=key, telescopename=dataset_name)
            lc.mags = tupl[1]
            lc.jds = tupl[0]
            lc.magerrs = tupl[2]
            lc.labels = len(lc.jds) * ['']
            tel_list = list(tupl[3])
            tel_list = ['2p2' if e == 'WFI' else e for e in tel_list]
            lc.properties = tel_list
            outliers = detect_outliers([lc], sigma_threshold=sigma_outlier)
            mask = np.ones_like(lc.mags, dtype=bool)
            mask[(outliers,)] = False
            lc.mask = mask
            if cutmask:
                lc.cutmask()
            lcs.append(lc)
        lcs = sorted(lcs, key=lambda lci: lci.object)
        return lcs, dataset_name
