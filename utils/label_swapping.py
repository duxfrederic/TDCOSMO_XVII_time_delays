import pandas as pd
"""
swaps delays:
- ASSUMES SINGLE LETTER LABELLING FOR LIGHT CURVES.
- assumes input delay pairs are ordered

to use: load delays and covariance as pandas data frames.
delays: delay pair names as index
covariance: delay pair names both as index and column names.

call remap_delays_and_covariance on the dataframes, with a dictionary defining the remapping, e.g.:
{'A':'B', 'B':'A'} to exchange A and B.
"""

def validate_remapping(remap_dict):
    """
    Utility function: make sure the remapping is a bijection of single-character keys.
    """
    if not isinstance(remap_dict, dict):
        return False
    # check all keys and values are single characters
    for k, v in remap_dict.items():
        if not (isinstance(k, str) and len(k) == 1 and isinstance(v, str) and len(v) == 1):
            return False
    # must be bijection: keys and values are unique and map 1:1
    keys = list(remap_dict.keys())
    values = list(remap_dict.values())
    if len(set(keys)) != len(keys) or len(set(values)) != len(values):
        return False
    if set(keys) != set(values):
        return False
    return True

def remap_delays_and_covariance(delays_df, cov_df, remap_dict):
    """
    Re-map delays and covariance matrix when changing the labelling of the
    lensed images. (e.g. swapping A and B)
    Only works for lensed images labelled with a unique letter.
    Assumption: all delay labels are initially ordered! E.g. AB, AC, BC ... NOT BA, CA, CB

    Args:
        delays_df (pd.DataFrame): Delays with labels as index (e.g., 'AB', 'BC').
        cov_df (pd.DataFrame): Covariance matrix with matching labels for rows/columns.
        remap_dict (dict): Mapping from original to new labels (e.g., {'B': 'C', 'C': 'B'}).

    Returns:
        (pd.DataFrame, pd.DataFrame): Adjusted delays and covariance matrix.
    """
    if not validate_remapping(remap_dict):
        raise ValueError("Invalid remapping dictionary.")


    def get_original_pair_and_sign(label):
        # utility to compute original pair and sign for a given label
        c1, c2 = list(label)
        # of course, remap_dict is bijective so we can also
        # transform a new label into an original label.
        # but we'll use this function to do the opposite.
        nc1 = remap_dict.get(c1, c1)
        nc2 = remap_dict.get(c2, c2)
        reversed_order = nc1 > nc2  # because input is assumed to be ordered

        original_pair = ''.join(sorted([nc1, nc2]))
        sign = -1 if reversed_order else 1
        return original_pair, sign

    # remap delays.
    # because we were listing all possible delay pairs, the remapping
    # is indeed only a remapping, with sign chance when the order changes.
    new_delays = pd.DataFrame(index=delays_df.index, columns=delays_df.columns)
    for label in delays_df.index:
        # label is the "new label".
        original_pair, sign = get_original_pair_and_sign(label)
        new_delays.loc[label] = delays_df.loc[original_pair].values * sign

    # remap covariance matrix -- again assumed to list all possible delay pairs
    # initially, so just a remapping.
    # We iterate over label-label pairs by row and column.
    new_cov = pd.DataFrame(index=cov_df.index, columns=cov_df.columns)
    for row_label in cov_df.index:
        original_row_pair, row_sign = get_original_pair_and_sign(row_label)
        for col_label in cov_df.columns:
            original_col_pair, col_sign = get_original_pair_and_sign(col_label)
            # simply read original covariance value and apply sign
            original_cov_value = cov_df.loc[original_row_pair, original_col_pair]
            # that is, if both labels moved, no sign change
            # if twice same label (diagonal), no sign change automatically
            new_cov.loc[row_label, col_label] = original_cov_value * row_sign * col_sign

    return new_delays, new_cov
