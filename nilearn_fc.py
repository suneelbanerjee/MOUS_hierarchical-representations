import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from nilearn import plotting
from nilearn.maskers import NiftiMasker
from nilearn.interfaces.fmriprep import load_confounds_strategy
from nilearn.connectome import ConnectivityMeasure
import os
from pathlib import Path

# ==========================================
# 1. CONFIGURATION & PATHS
# ==========================================

# Base directory containing all subject folders
BASE_DIR = Path('/media/neel/MOUS1/MOUS/MOUS/fmriprep_fresh/')
ROI_DIR = Path('/home/neel/Desktop/MOUS_hierarchical-representations/figures/ROI_masks/auditory')
OUTPUT_DIR = "./results"
TR = 2.0 

def get_roi_paths(roi_dir):
    """
    Scans the ROI directory for .nii or .nii.gz files.
    Excludes .csv or other non-image files.
    """
    roi_dir = Path(roi_dir)
    rois = list(roi_dir.glob('*.nii')) + list(roi_dir.glob('*.nii.gz'))
    rois.sort()
    
    if not rois:
        raise FileNotFoundError(f"No .nii or .nii.gz files found in {roi_dir}")
        
    print(f"Found {len(rois)} ROI masks.")
    return rois

def clean_confounds_fallback(confounds_path):
    """
    Manual implementation of 'simple' strategy when automatic loading fails.
    Selects: Motion (6 params), CSF, White Matter.
    Handles 'n/a' values.
    """
    # Load TSV, treating 'n/a' as NaN
    df = pd.read_csv(confounds_path, sep='\t', na_values=['n/a', 'N/A'])
    
    # Define the columns we want for a "Simple" strategy
    # 6 motion parameters + WM + CSF
    # Note: fMRIPrep column names are standard
    keep_cols = [
        'trans_x', 'trans_y', 'trans_z', 
        'rot_x', 'rot_y', 'rot_z', 
        'csf', 'white_matter'
    ]
    
    # Check which columns actually exist in the file
    available_cols = [c for c in keep_cols if c in df.columns]
    
    if len(available_cols) < len(keep_cols):
        print(f"Warning: Some expected confound columns were missing. Found: {available_cols}")
    
    # Select only these columns
    confounds_clean = df[available_cols].copy()
    
    # Fill NaNs (usually the first row) with 0
    confounds_clean = confounds_clean.fillna(0)
    
    print(f"Fallback: Selected {len(available_cols)} confound columns (Motion + Physio).")
    return confounds_clean

def run_subject_pipeline(subject_label, bold_path, confounds_path, roi_paths, output_dir):
    """
    Runs the FC pipeline for a single subject.
    """
    print(f"\n--- Processing {subject_label} ---")
    
    # Create subject-specific output directory
    subj_out_dir = os.path.join(output_dir, subject_label)
    if not os.path.exists(subj_out_dir):
        os.makedirs(subj_out_dir)

    # ==========================================
    # 2. CONFOUNDS & DENOISING STRATEGY
    # ==========================================
    print(f"Loading confounds for {subject_label}...")
    
    confounds = None
    sample_mask = None

    # Try automatic strategy first
    try:
        # Note: removed 'return_use_sample_mask' to fix warning, as 'simple' strategy doesn't support it
        # 'simple' implies no scrubbing, so no sample_mask needed
        confounds = load_confounds_strategy(
            str(bold_path),
            denoise_strategy='simple',
            motion='basic',
            wm_csf='basic',
            global_signal='basic'
        )
        # If load_confounds_strategy returns a tuple (depending on version), handle it
        if isinstance(confounds, tuple):
            confounds = confounds[0]
            
    except Exception as e:
        print(f"Strategy loading failed (likely filename mismatch): {e}")
        print("Attempting manual fallback...")
        
        if confounds_path.exists():
            confounds = clean_confounds_fallback(confounds_path)
            sample_mask = None 
        else:
            print(f"CRITICAL: Confounds file not found at {confounds_path}")
            return None

    # ==========================================
    # 3. EXTRACT TIME SERIES FROM ROIS
    # ==========================================
    print("Extracting time series...")
    
    roi_time_series = []
    roi_names = []

    for roi_path in roi_paths:
        roi_name = roi_path.name.replace('.nii.gz', '').replace('.nii', '')
        roi_names.append(roi_name)
        
        masker = NiftiMasker(
            mask_img=str(roi_path), 
            standardize="zscore_sample",
            detrend=True,
            t_r=TR,
            verbose=0
        )

        try:
            # fit_transform extracts signals and cleans them using the confounds
            ts = masker.fit_transform(
                str(bold_path), 
                confounds=confounds, 
                sample_mask=sample_mask
            )
            
            # Average voxel signals within the ROI
            mean_ts = np.mean(ts, axis=1)
            roi_time_series.append(mean_ts)
            
        except Exception as e:
            print(f"Error extracting ROI {roi_name}: {e}")
            return None

    roi_time_series = np.array(roi_time_series).T
    
    # ==========================================
    # 4. COMPUTE CONNECTIVITY
    # ==========================================
    correlation_measure = ConnectivityMeasure(
        kind='correlation', 
        vectorize=False, 
        discard_diagonal=False
    )
    
    # fit_transform expects list of subjects
    correlation_matrix = correlation_measure.fit_transform([roi_time_series])[0]

    # ==========================================
    # 5. VISUALIZATION & SAVING
    # ==========================================
    
    # Save Matrix to subject sub-folder
    out_csv = os.path.join(subj_out_dir, f"{subject_label}_correlation_matrix.csv")
    df_corr = pd.DataFrame(correlation_matrix, index=roi_names, columns=roi_names)
    df_corr.to_csv(out_csv)
    print(f"Saved matrix to {out_csv}")

    # Save Plot to subject sub-folder
    plt.figure(figsize=(10, 8))
    plotting.plot_matrix(
        correlation_matrix, 
        labels=roi_names, 
        colorbar=True,
        vmax=1.0, 
        vmin=-1.0,
        title=f"FC Matrix: {subject_label}"
    )
    out_plot = os.path.join(subj_out_dir, f"{subject_label}_matrix_plot.png")
    plt.savefig(out_plot)
    plt.close() 
    
    return df_corr

if __name__ == "__main__":
    # 1. Setup Output
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # 2. Get ROIs once
    try:
        roi_paths = get_roi_paths(ROI_DIR)
    except FileNotFoundError as e:
        print(e)
        exit()

    # 3. Find Subjects
    subjects = sorted(list(BASE_DIR.glob('sub-A2*')))
    print(f"Found {len(subjects)} subject directories in {BASE_DIR}")

    for subj_dir in subjects:
        if not subj_dir.is_dir():
            continue
            
        subject_label = subj_dir.name
        
        bold_file = subj_dir / 'func' / f'{subject_label}_task-auditory_space-MNI152NLin6Asym_res-2_desc-preproc_bold.nii'
        confounds_file = subj_dir / 'func' / f'{subject_label}_task-auditory_desc-confounds_regressors.tsv'
        
        if bold_file.exists():
            run_subject_pipeline(subject_label, bold_file, confounds_file, roi_paths, OUTPUT_DIR)
        else:
            print(f"Skipping {subject_label}: BOLD file not found at {bold_file}")