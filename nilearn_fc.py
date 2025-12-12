import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import os
import gc
from pathlib import Path
import numpy as np
import pandas as pd

from nilearn import image, plotting
from nilearn.maskers import NiftiMasker
from nilearn.interfaces.fmriprep import load_confounds_strategy
from nilearn.connectome import ConnectivityMeasure


# ===============================
# CONFIG
# ===============================

BASE_DIR = Path('/media/lillianchang/MOUSnew/fmriprep_fresh')
ROI_DIR = Path('/home/lillianchang/Documents/MOUS_hierarchical-representations/figures/ROI_masks/auditory')
OUTPUT_DIR = Path("./results")
TR = 2.0


# ===============================
# UTILITIES
# ===============================

def get_roi_paths(roi_dir):
    roi_dir = Path(roi_dir)
    rois = sorted(list(roi_dir.glob('*.nii')) + list(roi_dir.glob('*.nii.gz')))
    if not rois:
        raise FileNotFoundError(
            "No ROI masks (.nii/.nii.gz) found in {}".format(roi_dir)
        )
    print("Found {} ROI masks.".format(len(rois)))
    return rois


def clean_confounds_fallback(confounds_path):
    df = pd.read_csv(confounds_path, sep='\t', na_values=['n/a', 'N/A'])

    keep_cols = [
        'trans_x', 'trans_y', 'trans_z',
        'rot_x', 'rot_y', 'rot_z',
        'csf', 'white_matter'
    ]
    available = [c for c in keep_cols if c in df.columns]

    if len(available) < len(keep_cols):
        print("Warning: missing confound columns. Using: {}".format(available))

    conf = df[available].fillna(0).astype('float32')
    print("Fallback: {} regressors selected (float32).".format(len(available)))
    return conf


# ===============================
# MAIN SUBJECT PIPELINE
# ===============================

def run_subject(subject_label, bold_file, confounds_file, roi_paths, output_dir):
    """
    Memory-safe FC pipeline.
    Returns DataFrame correlation matrix or None.
    """

    print("\n===== {} =====".format(subject_label))
    subj_dir = Path(output_dir) / subject_label
    subj_dir.mkdir(exist_ok=True, parents=True)

    # ------------------------------------------
    # Load confounds
    # ------------------------------------------
    print("Loading confounds...")

    confounds = None
    sample_mask = None

    try:
        confounds, sample_mask = load_confounds_strategy(
            str(bold_file),
            denoise_strategy='simple',
            motion='basic',
            wm_csf='basic',
            global_signal=None,
            return_use_sample_mask=True
        )
        confounds = confounds.astype('float32')

    except Exception as e:
        print("load_confounds_strategy failed: {}".format(e))
        if confounds_file.exists():
            confounds = clean_confounds_fallback(confounds_file)
            sample_mask = None
        else:
            print("ERROR: confound file missing. Skipping subject.")
            return None

    # ------------------------------------------
    # Load BOLD as memory-mapped image
    # ------------------------------------------
    print("Memory-mapping BOLD...")

    try:
        bold_img = image.load_img(str(bold_file))
        bold_img = image.index_img(bold_img, slice(None))   # enforce memmap
    except Exception as e:
        print("ERROR loading BOLD: {}".format(e))
        return None

    # ------------------------------------------
    # Extract ROI time series
    # ------------------------------------------
    print("Extracting ROI signals...")

    roi_ts_list = []
    roi_names = []

    for roi_path in roi_paths:
        roi_name = roi_path.name.replace('.nii.gz', '').replace('.nii', '')
        roi_names.append(roi_name)

        masker = NiftiMasker(
            mask_img=str(roi_path),
            standardize="zscore_sample",
            detrend=False,           # fMRIPrep already provides high-pass regressors
            high_pass=None,
            t_r=TR,
            dtype='float32',
            memory='nilearn_cache',
            memory_level=1,
            verbose=0
        )

        try:
            ts = masker.fit_transform(
                bold_img,
                confounds=confounds,
                sample_mask=sample_mask
            )
            mean_ts = ts.mean(axis=1).astype('float32')
            roi_ts_list.append(mean_ts)
            del ts
        except Exception as e:
            print("ROI {} failed: {}".format(roi_name, e))
            return None

    # Convert to (T × N_ROI)
    roi_ts_mat = np.vstack(roi_ts_list).T

    # ------------------------------------------
    # Compute FC
    # ------------------------------------------
    corr = ConnectivityMeasure(
        kind='correlation',
        discard_diagonal=False,
        vectorize=False
    ).fit_transform([roi_ts_mat])[0]

    df_corr = pd.DataFrame(corr, index=roi_names, columns=roi_names)
    out_csv = subj_dir / f"{subject_label}_correlation_matrix.csv"
    df_corr.to_csv(out_csv)
    print("Saved:", out_csv)

    # ------------------------------------------
    # Plot
    # ------------------------------------------
    plt.figure(figsize=(10, 8))
    plotting.plot_matrix(
        corr,
        labels=roi_names,
        colorbar=True,
        vmin=-1,
        vmax=1,
        title=f"FC Matrix: {subject_label}"
    )
    plt.savefig(subj_dir / f"{subject_label}_matrix_plot.png")
    plt.close('all')

    # ------------------------------------------
    # Cleanup
    # ------------------------------------------
    del bold_img
    del roi_ts_mat
    gc.collect()

    return df_corr


# ===============================
# DRIVER
# ===============================

if __name__ == "__main__":

    OUTPUT_DIR.mkdir(exist_ok=True)

    roi_paths = get_roi_paths(ROI_DIR)
    subjects = sorted([p for p in BASE_DIR.glob('sub-A2*') if p.is_dir()])
    print("Found {} subjects.".format(len(subjects)))

    for subj_path in subjects:
        subject_label = subj_path.name

        bold_file = subj_path / "func" / f"{subject_label}_task-auditory_space-MNI152NLin6Asym_res-2_desc-preproc_bold.nii"
        conf_file = subj_path / "func" / f"{subject_label}_task-auditory_desc-confounds_regressors.tsv"

        if bold_file.exists():
            run_subject(subject_label, bold_file, conf_file, roi_paths, OUTPUT_DIR)
        else:
            print("Missing BOLD for {} — skipped.".format(subject_label))