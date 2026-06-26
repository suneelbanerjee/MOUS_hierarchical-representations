import matplotlib
# CRASH SAFEGUARD: Non-interactive backend
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

# Updated paths for Visual Subjects
BASE_DIR = Path('/media/lillianchang/MOUSnew/fmriprep_fresh')
ROI_DIR = Path('/home/lillianchang/Documents/MOUS_hierarchical-representations/figures/ROI_masks/visual')
OUTPUT_DIR = Path("./results")
TR = 2.0

# ===============================
# UTILITIES
# ===============================

def get_roi_paths(roi_dir):
    roi_dir = Path(roi_dir)
    if not roi_dir.exists():
        raise FileNotFoundError(f"ROI Directory not found: {roi_dir}")
        
    rois = sorted(list(roi_dir.glob('*.nii')) + list(roi_dir.glob('*.nii.gz')))
    if not rois:
        raise FileNotFoundError(f"No ROI masks (.nii/.nii.gz) found in {roi_dir}")
    
    print(f"Found {len(rois)} ROI masks.")
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
        print(f"Warning: missing confound columns. Using: {available}")

    conf = df[available].fillna(0).astype('float32')
    print(f"Fallback: {len(available)} regressors selected (float32).")
    return conf


# ===============================
# MAIN SUBJECT PIPELINE
# ===============================

def run_subject(subject_label, bold_file, confounds_file, roi_paths, output_dir):
    """
    Memory-safe FC pipeline.
    Returns DataFrame correlation matrix or None.
    """

    print(f"\n===== {subject_label} =====")
    subj_dir = Path(output_dir) / subject_label
    
    # Robust directory creation
    subj_dir.mkdir(parents=True, exist_ok=True)

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
        print(f"load_confounds_strategy failed: {e}")
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
        print(f"ERROR loading BOLD: {e}")
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
            print(f"ROI {roi_name} failed: {e}")
            return None

    # Convert to (T x N_ROI)
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
    print(f"Saved: {out_csv}")

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

    # Robust creation of output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Verify ROI directory
    try:
        roi_paths = get_roi_paths(ROI_DIR)
    except FileNotFoundError as e:
        print(e)
        exit()

    # UPDATED: Search for sub-V*
    subjects = sorted([p for p in BASE_DIR.glob('sub-V*') if p.is_dir()])
    
    print(f"Searching for subjects in: {BASE_DIR}")
    print(f"Found {len(subjects)} subjects.")

    for subj_path in subjects:
        subject_label = subj_path.name

        # UPDATED: Filenames now reflect task-visual
        bold_file = subj_path / "func" / f"{subject_label}_task-visual_space-MNI152NLin6Asym_res-2_desc-preproc_bold.nii"
        conf_file = subj_path / "func" / f"{subject_label}_task-visual_desc-confounds_regressors.tsv"

        if bold_file.exists():
            run_subject(subject_label, bold_file, conf_file, roi_paths, OUTPUT_DIR)
        else:
            print(f"Missing BOLD for {subject_label} - checked path: {bold_file}")