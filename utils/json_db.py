import json
import pickle
from pathlib import Path


# this is a stupid json database to store our initial guesses and
# what knotsteps / microlensing we deem appropriate for each object.
class Database:
    def __init__(self, file_path, pickled_curves_dir):
        self.file_path = file_path
        self.pickled_curves_dir = Path(pickled_curves_dir)
        self.pickled_curves_dir.mkdir(parents=True, exist_ok=True)

    def get(self, field_path=None):
        data = self._load_data()
        if not field_path:
            return data
        current_node = data

        try:
            for subfield in field_path:
                current_node = current_node[subfield]
            return current_node
        except (KeyError, TypeError):
            return None

    def update(self, field_path, value):
        data = self._load_data()
        current_node = data

        for subfield in field_path[:-1]:
            if subfield not in current_node:
                current_node[subfield] = {}
            current_node = current_node[subfield]

        current_node[field_path[-1]] = value
        self._save_data(data)

    def _load_data(self):
        try:
            with open(self.file_path, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            print('no such file!')
            return {}

    def _save_data(self, data):
        try:
            serialized_data = json.dumps(data)
            with open(self.file_path, 'w') as file:
                file.write(serialized_data)
        except Exception as e:
            print(f"An error occurred while saving the data: {str(e)}")

    def save_for_pycs3_run(self, lens_name, dataset_name, lcs, mltouse, knotstouse, tsrand=None):
        # update when we're satisfied of our initial guess
        # we'll also save the light curves used in the estimation here to a pickle file,
        # as to not have surprises when running the PyCS3 scripts.
        # I hate pickles, but because this is only an intermediate step (with the original light curves
        # read from the photometry database), I'll allow it.
        # write into our text db our initial guess.
        set_name = f"{lens_name}_{dataset_name}"
        # save time shifts relative to first image:
        ts0 = lcs[0].timeshift
        for lc in lcs:
            lc.timeshift -= ts0
        # write down all that joyful information
        for lc in lcs:
            self.update([set_name, 'curves', lc.object, 'magshift'], lc.magshift)
            self.update([set_name, 'curves', lc.object, 'timeshift'], lc.timeshift)
        self.update([set_name, 'mltouse'], mltouse)
        self.update([set_name, 'knotstouse'], knotstouse)
        if tsrand is not None:
            # if None, taken to be max(0.2 * largest delay, 10) in downstream steps
            self.update([set_name, 'tsrand'], tsrand)

        # save the lcs into a pickle file that PyCS3 can later load.
        # before saving, resetting the lcs as the pycs3 scripts will read this info from the config file
        # (lcs not meant to have their own shifts in those scripts)
        for lc in lcs:
            lc.resetshifts()
        with open(self.pickled_curves_dir / f"{set_name}.pkl", 'wb') as f:
            pickle.dump(lcs, f)

