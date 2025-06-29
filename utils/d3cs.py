from pathlib import Path


def to_d3cs_csv(out_dir, lcs, lens_name, dataset_name):
    template = f"{lens_name}_{dataset_name}_{{im}}.csv"
    for lc in lcs:
        ff = Path(out_dir) / template.format(im=lc.object)
        with open(ff, 'w') as f:
            f.write('mhjd,mag,magerr\n')
            for jd, mag, mag_err in zip(lc.jds,lc.mags,lc.magerrs):
                f.write(f"{jd},{mag},{mag_err}\n")


def all_pickles_to_d3cs(pkl_dir, out_dir_csv):
    import pickle
    pkl_files = list(Path(pkl_dir).glob('*.pkl'))
    for pkl_file in pkl_files:
        data_name = pkl_file.stem
        lens_name, dataset_name = data_name.split('_')
        with open(pkl_file, 'rb') as f:
            lcs = pickle.load(f)
        to_d3cs_csv(out_dir_csv, lcs, lens_name, dataset_name)



if __name__ == "__main__":
    import sys
    all_pickles_to_d3cs(sys.argv[1], sys.argv[2])
