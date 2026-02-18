import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import os
import gc
import sys
from pathlib import Path
import numpy as np
import pandas as pd

from nilearn import image, plotting
from nilearn.maskers import NiftiMasker
from nilearn.interfaces.fmriprep import load_confounds_strategy
from nilearn.connectome import ConnectivityMeasure

# ===============================
# CONFIGURATION
# ===============================

# Adjust TR if your resting state scan has a different repetition time!
TR = 2.0 
BASE_DIR = Path('/media/lillianchang/MOUSnew/fmriprep_fresh')
OUTPUT_ROOT = Path("./results")

# ===============================
# INTERACTIVE SETUP
# ===============================

def setup_analysis_params():
    print("\n" + "="*50)
    print("   FUNCTIONAL CONNECTIVITY CALCULATION MENU")
    print("="*50)
    
    config = {}

    # 1. Select Task
    while True:
        print("\n1. Select Analysis Type:")
        print("   [1] Auditory Task (sub-A*)")
        print("   [2] Visual Task   (sub-V*)")
        print("   [3] Resting State (Combined: sub-A* + sub-V*)")
        
        choice = input("   Selection: ").strip()
        
        if choice == "1":
            config["name"] = "auditory"
            config["subj_glob"] = "sub-A*"
            config["task_label"] = "task-auditory"
            print("   >> Selected: AUDITORY task.")
            break
        elif choice == "2":
            config["name"] = "visual"
            config["subj_glob"] = "sub-V*"
            config["task_label"] = "task-visual"
            print("   >> Selected: VISUAL task.")
            break
        elif choice == "3":
            config["name"] = "rest"
            # This glob will catch BOTH sub-A and sub-V folders
            config["subj_glob"] = "sub-*" 
            config["task_label"] = "task-rest"
            print("   >> Selected: RESTING STATE (Combined Group).")
            break
        else:
            print("   [!] Invalid selection.")

    # 2. Select ROI Directory
    print("\n2. ROI Directory")
    print("   Enter the full path to your ROI directory.")
    
    while True:
        roi_input = input("   ROI Path: ").strip()
        roi_path = Path(roi_input)
        
        if roi_path.exists() and roi_path.is_dir():
            niftis = list(roi_path.glob('*.nii')) + list(roi_path.glob('*.nii.gz'))
            if niftis:
                config["roi_dir"] = roi_path
                print(f"   >> Selected: {roi_path.name} ({len(niftis)} masks)")
                break
            else:
                print(f"   [!] Directory contains no .nii files.")
        else:
            print(f"   [!] Directory not found: {roi_input}")

    # 3. Output Directory
    print("\n3. Output Directory")
    print("   Where should the results be saved? (Press Enter for default: ./results)")
    
    out_input = input("   Output Path: ").strip()
    if not out_input:
        config["output_root"] = Path("./results")
        print("   >> Using default: ./results")
    else:
        config["output_root"] = Path(out_input)
        print(f"   >> Selected: {config['output_root']}")
            
    return config

# ===============================
# UTILITIES
# ===============================

def get_roi_paths(roi_dir):
    rois = sorted(list(roi_dir.glob('*.nii')) + list(roi_dir.glob('*.nii.gz')))
    return rois

def clean_confounds_fallback(confounds_path):
    df = pd.read_csv(confounds_path, sep='\t', na_values=['n/a', 'N/A'])
    keep_cols = ['trans_x', 'trans_y', 'trans_z', 'rot_x', 'rot_y', 'rot_z', 'csf', 'white_matter']
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
    Memory-safe FC pipeline. Returns DataFrame correlation matrix or None.
    """
    print(f"\n===== {subject_label} =====")
    subj_dir = Path(output_dir) / subject_label
    subj_dir.mkdir(exist_ok=True, parents=True)

    # 1. Load Confounds
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

    # 2. Load BOLD
    print("Memory-mapping BOLD...")
    try:
        bold_img = image.load_img(str(bold_file))
        bold_img = image.index_img(bold_img, slice(None)) # enforce memmap
    except Exception as e:
        print(f"ERROR loading BOLD: {e}")
        return None

    # 3. Extract ROI Time Series
    print("Extracting ROI signals...")
    roi_ts_list = []
    roi_names = []

    for roi_path in roi_paths:
        roi_name = roi_path.name.replace('.nii.gz', '').replace('.nii', '')
        roi_names.append(roi_name)

        masker = NiftiMasker(
            mask_img=str(roi_path),
            standardize="zscore_sample",
            detrend=False,
            high_pass=None,
            t_r=TR,
            dtype='float32',
            memory='nilearn_cache',
            memory_level=1,
            verbose=0
        )

        try:
            ts = masker.fit_transform(bold_img, confounds=confounds, sample_mask=sample_mask)
            mean_ts = ts.mean(axis=1).astype('float32')
            roi_ts_list.append(mean_ts)
            del ts
        except Exception as e:
            print(f"ROI {roi_name} failed: {e}")
            return None

    # 4. Compute FC
    roi_ts_mat = np.vstack(roi_ts_list).T
    corr = ConnectivityMeasure(kind='correlation', discard_diagonal=False, vectorize=False).fit_transform([roi_ts_mat])[0]

    # 5. Save Results
    df_corr = pd.DataFrame(corr, index=roi_names, columns=roi_names)
    out_csv = subj_dir / f"{subject_label}_correlation_matrix.csv"
    df_corr.to_csv(out_csv)
    print(f"Saved: {out_csv}")

    # Plot for QC
    plt.figure(figsize=(10, 8))
    plotting.plot_matrix(corr, labels=roi_names, colorbar=True, vmin=-1, vmax=1, title=f"FC Matrix: {subject_label}")
    plt.savefig(subj_dir / f"{subject_label}_matrix_plot.png")
    plt.close('all')

    # Cleanup
    del bold_img
    del roi_ts_mat
    gc.collect()
    return df_corr

# ===============================
# DRIVER
# ===============================

if __name__ == "__main__":
    # 1. Interactive Setup
    params = setup_analysis_params()
    
    # 2. Prepare Final Output Path
    roi_folder_name = params["roi_dir"].name
    task_output_dir = params["output_root"] / params["name"] / roi_folder_name
    
    print(f"\n[Info] Final Output Directory: {task_output_dir}")
    task_output_dir.mkdir(parents=True, exist_ok=True)
    
    # 3. Get ROIs
    roi_paths = get_roi_paths(params["roi_dir"])

    # 4. Find Subjects
    print(f"Searching for subjects in: {BASE_DIR} matching '{params['subj_glob']}'...")
    subjects = sorted([p for p in BASE_DIR.glob(params['subj_glob']) if p.is_dir()])
    
    if not subjects:
        print(f"[Error] No subjects found matching '{params['subj_glob']}'")
        sys.exit(1)
        
    print(f"Found {len(subjects)} subjects.")
    
    # 5. Run Pipeline
    success_count = 0
    for subj_path in subjects:
        subject_label = subj_path.name
        
        # Dynamic filename construction
        # NOTE: This looks for "sub-X_task-rest_..." if Option 3 was selected
        bold_file = subj_path / "func" / f"{subject_label}_{params['task_label']}_space-MNI152NLin6Asym_res-2_desc-preproc_bold.nii"
        conf_file = subj_path / "func" / f"{subject_label}_{params['task_label']}_desc-confounds_regressors.tsv"

        if bold_file.exists():
            result = run_subject(subject_label, bold_file, conf_file, roi_paths, task_output_dir)
            if result is not None:
                success_count += 1
        else:
            # Silent skip is safer for combined groups (e.g. if some subjects are missing rest data)
            # but we print here for transparency
            print(f"Skipping {subject_label} (No {params['task_label']} data found).")
            
    print(f"\nProcessing complete. Successfully processed {success_count}/{len(subjects)} subjects.")
    print(f"Results saved to: {task_output_dir}")