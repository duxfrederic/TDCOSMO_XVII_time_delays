import sys
import pickle
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import sigmaclip
from scipy.optimize import brentq

import pycs3.sim.run


def load_groups(directory: Path) -> list:
    """Load group information from pickle files produced during 4b"""
    groups_path = directory / 'marginalisation_spline' / 'marginalisation_spline_sigma_0.50_groups_used_in_combined.pkl'
    try:
        with open(groups_path, 'rb') as f:
            groups = pickle.load(f)
        if not groups:
            raise ValueError("Empty groups, loading all groups instead.")
    except (FileNotFoundError, ValueError):
        print('WARNING: Loading all groups')
        groups_path = directory / 'marginalisation_spline' / 'marginalisation_spline_sigma_0.50_groups.pkl'
        with open(groups_path, 'rb') as f:
            groups = pickle.load(f)
    return groups


def extract_lensed_images(groups: list) -> list:
    """Extract unique lensed images from groups."""
    labels = sorted(groups[0].labels)
    lensed_images = set()
    for label in labels:
        l1, l2 = label[:-1], label[-1:]
        lensed_images.update([l1, l2])
    return sorted(lensed_images)


def get_accepted_params(groups: list) -> list:
    """Retrieve accepted parameters from groups."""
    accepted_params = []
    for group in groups:
        if 'combined' in group.name:
            combined_group = group
            continue
        parts = group.name.split('_')
        if len(parts) < 2:
            continue  # Skip if format is unexpected
        knot = parts[1]
        if 'nmlspl_' in group.name:
            spl_part = group.name.split('nmlspl_')[1]
            spl = spl_part[:-3]  # Remove last 3 characters
        else:
            spl = ''
        print(f'Using knot: {knot}, spline: {spl}')
        accepted_params.append((knot, spl))
    return accepted_params


def load_mock_results(spls: list, accepted_params: list, directory: Path):
    """Load mock results that match the accepted parameters."""
    all_tsarray = []
    all_truetsarray = []
    all_results = []
    for spl in spls:
        if not any(param[0] in spl.name and param[1] in spl.name for param in accepted_params):
            continue
        print(f'Loading mocks from {spl}')
        possible_paths = list(spl.glob('sims_mocks*opt*'))
        if not possible_paths:
            print(f'No mocks found in {spl}, skipping.')
            continue
        path = max(possible_paths)  # there should be only one path, but max will select that with the most mocks.
        results = pycs3.sim.run.collect(directory=path)
        all_tsarray.append(results.tsarray)
        all_truetsarray.append(results.truetsarray)
        all_results.append(results)
    if not all_tsarray or not all_truetsarray:
        raise ValueError("No mock results loaded. Check your accepted parameters and mock paths.")
    combined_results = all_results[-1]  # using the last loaded result as a template
    combined_results.tsarray = np.vstack(all_tsarray)
    combined_results.truetsarray = np.vstack(all_truetsarray)
    return combined_results


def desired_std_from_percentiles(error: np.ndarray) -> float:
    """Compute desired standard deviation from 16th and 84th percentiles."""
    lower, upper = np.percentile(error, [16, 84])
    return (upper - lower) / 2.0


def find_optimal_clip_sigma(error: np.ndarray, desired_std: float, sigma_bounds=(2.0, 5.0), tol=1e-2) -> float:
    """
    Find the clip_sigma such that the standard deviation of the clipped error
    matches the desired_std.
    In other words: cutting the tails so the standard deviation matches the 84-16 percentiles interval.

    Uses a root-finding approach to solve:
        std(clipped_error) - desired_std = 0
    """
    
    def objective(clip_sigma):
        clipped, lower, upper = sigmaclip(error, low=clip_sigma, high=clip_sigma)
        if len(clipped) == 0:
            return desired_std  # no data left; return the difference as desired_std
        print('clip sigma: ', clip_sigma, 'obj: ', np.std(clipped))
        return np.std(clipped) - desired_std

    lower_bound, upper_bound = sigma_bounds
    try:
        # ensure the objective changes sign over the interval
        obj_lower = objective(lower_bound)
        obj_upper = objective(upper_bound)
        if obj_lower * obj_upper > 0:
            print(f"Warning: No root found for sigma clipping within bounds {sigma_bounds}.")
            print(f"Objective at lower bound ({lower_bound}): {obj_lower}")
            print(f"Objective at upper bound ({upper_bound}): {obj_upper}")
            return 3.5  # default if no root is found

        # Find the root using Brent's method
        optimal_sigma = brentq(objective, lower_bound, upper_bound, xtol=tol)
        return optimal_sigma
    except Exception as e:
        print(f"Error finding optimal clip_sigma: {e}")
        return 3.5  # default value in case of error


def compute_errors(labels: list, lensed_images: list, results):
    """Compute errors, determine desired std, find optimal sigma clipping, and apply clipping."""
    errors = []
    interval16_84 = []
    for label in labels:
        im_ref, im = label[:-1], label[-1:]
        im_ref_idx = lensed_images.index(im_ref)
        im_idx = lensed_images.index(im)

        measured_delays = results.tsarray[:, im_idx] - results.tsarray[:, im_ref_idx]
        true_delays = results.truetsarray[:, im_idx] - results.truetsarray[:, im_ref_idx]
        error = measured_delays - true_delays

        # desired standard deviation from 84 - 16 percentiles
        desired_std = desired_std_from_percentiles(error)
        interval16_84_width = desired_std * 2  # desired_std = (p(84) - p(16))/2
        interval16_84.append(desired_std)

        print(f'{label}: Desired 16-84 percentile interval width: {interval16_84_width:.2f}')

        # optimal clip_sigma
        optimal_clip_sigma = find_optimal_clip_sigma(error, desired_std)

        print(f'{label}: Optimal clip_sigma found: {optimal_clip_sigma:.2f}')

        # sigma clipping with optimal clip_sigma
        clipped_error, lower_clip, upper_clip = sigmaclip(error, low=optimal_clip_sigma, high=optimal_clip_sigma)
        error_clipped = error.copy()  # seems overcomplicated, but I want to keep track of excluded values in all mocks
        mask = (error > upper_clip) | (error < lower_clip)
        error_clipped[mask] = np.nan
        num_excluded = np.sum(mask)
        print(f"{label}: Excluding {num_excluded} mocks out of {error.size} (sigma={optimal_clip_sigma:.2f})")

        errors.append(error_clipped)  # here errors has NaNs for clipped values.
    return errors, interval16_84


def main():
    if len(sys.argv) != 3:
        print("Usage: script.py <lens> <dataset>")
        sys.exit(1)
    
    lens, dataset = sys.argv[1:]
    directory = Path('Simulation') / f"{lens}_{dataset}"
    
    # List all the estimators
    spls = list(directory.glob('spl1*'))
    if not spls:
        print("No estimators found matching 'spl1*' pattern.")
        sys.exit(1)
    
    # load groups from 4b
    groups = load_groups(directory)
    
    # labels and lensed images
    labels = sorted(groups[0].labels)
    lensed_images = extract_lensed_images(groups)
    
    # accepted parameters of 4b
    accepted_params = get_accepted_params(groups)
    
    # load mock results
    try:
        results = load_mock_results(spls, accepted_params, directory)
    except ValueError as e:
        print(e)
        sys.exit(1)
    
    # covariance errors with dynamic sigma clipping
    errors, interval16_84 = compute_errors(labels, lensed_images, results)
    
    # wrap in a pandas dataframe, easier
    errors_by_label = {label: error for label, error in zip(labels, errors)}
    df = pd.DataFrame(errors_by_label)
    # the systematic error, important e.g. for WGD2021 (because of the very small intersect of the LCs)
    sys_error = np.abs(df.median().values)
    
    # systemic ""variance"" diagonal matrix
    sys_variance_diagonal = np.diag(sys_error**2)
    
    # covariance matrix, with systematic added in quadrature to the diagonal.
    cov_matrix = df.cov() + sys_variance_diagonal
    
    # prep for output
    stds = np.sqrt(np.diag(cov_matrix))
    ratios = stds / np.array(interval16_84)
    med_ratio = np.median(ratios)
    
    # Display covariance matrix and statistics
    print("\nCovariance Matrix:")
    print(cov_matrix.round(1))
    print("\nLabel         16-84 err      std")
    for label, errint, std in zip(labels, interval16_84, stds):
        print(f"{label:<5}: {errint:>14.1f} {std:>10.1f}")
    
    print(f"\nMedian ratio of standard deviation over 16-84 percentile interval: {med_ratio:.2f}")
    
    # save results
    output_dir = directory / 'marginalisation_spline'
    output_dir.mkdir(parents=True, exist_ok=True)
    np.savetxt(output_dir / 'median_std_over_16-84_interval_ratio.txt', [med_ratio])
    cov_matrix.to_csv(output_dir / 'covariance_matrix.csv')
    print("Results saved successfully.")


if __name__ == "__main__":
    main()
