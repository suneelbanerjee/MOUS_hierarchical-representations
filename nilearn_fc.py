import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from nilearn import plotting, image
from nilearn.maskers import NiftiMasker
from nilearn.interfaces.fmriprep import load_confounds_strategy
from nilearn.connectome import ConnectivityMeasure
import os
import gc  # Garbage collection for memory safety
from pathlib import Path

# ==========================================
# 1. CONFIGURATION & PATHS
# ==========================================

BASE_DIR = Path('/media/neel/MOUS1/MOUS/MOUS/fmriprep_fresh/')
ROI_DIR = Path('/home/neel/Desktop/MOUS_hierarchical-representations/figures/ROI_masks/auditory')
OUTPUT_DIR = "./results"
TR = 2.0 

def get_roi_paths(roi_dir):
    """
    Scans the ROI directory for .nii or .nii.gz files.
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
    Manual implementation of 'simple' strategy (No Global Signal).
    Selects: Motion (6 params), CSF, White Matter.
    """
    # Load TSV, treating 'n/a' as NaN
    df = pd.read_csv(confounds_path, sep='\t', na_values=['n/a', 'N/A'])
    
    # Standard fMRIPrep column names
    keep_cols = [
        'trans_x', 'trans_y', 'trans_z', 
        'rot_x', 'rot_y', 'rot_z', 
        'csf', 'white_matter'
    ]
    
    # Check availability
    available_cols = [c for c in keep_cols if c in df.columns]
    
    if len(available_cols) < len(keep_cols):
        print(f"Warning: Missing columns. Found only: {available_cols}")
    
    confounds_clean = df[available_cols].copy()
    confounds_clean = confounds_clean.fillna(0)
    
    print(f"Fallback: Selected {len(available_cols)} regressors (No GSR).")
    return confounds_clean

def run_subject_pipeline(subject_label, bold_path, confounds_path, roi_paths, output_dir):
    """
    Runs the FC pipeline for a single subject with memory optimization.
    """
    print(f"\n--- Processing {subject_label} ---")
    
    subj_out_dir = os.path.join(output_dir, subject_label)
    if not os.path.exists(subj_out_dir):
        os.makedirs(subj_out_dir)

    # ==========================================
    # 2. CONFOUNDS LOADING
    # ==========================================
    print(f"Loading confounds for {subject_label}...")
    
    confounds = None
    sample_mask = None

    try:
        # SCIENTIFIC FIX: Removed 'global_signal' to match the fallback
        # This ensures consistent processing across all subjects.
        confounds, sample_mask = load_confounds_strategy(
            str(bold_path),
            denoise_strategy='simple',
            motion='basic',
            wm_csf='basic',
            global_signal=None, # Explicitly None to match fallback
            return_use_sample_mask=True
        )
        
        # Depending on nilearn version, load_confounds_strategy might return a tuple or just the dataframe
        # If tuple (confounds, sample_mask), it is unpacked above. 
        # If it returned just confounds (older versions), sample_mask might need handling.
        # But 'return_use_sample_mask=True' forces a tuple return in recent versions.
            
    except Exception as e:
        print(f"Strategy loading failed: {e}")
        print("Attempting manual fallback...")
        
        if confounds_path.exists():
            confounds = clean_confounds_fallback(confounds_path)
            sample_mask = None 
        else:
            print(f"CRITICAL: Confounds file not found at {confounds_path}")
            return None

    # ==========================================
    # 3. EXTRACT TIME SERIES (OPTIMIZED)
    # ==========================================
    print("Loading BOLD image into memory...")
    
    try:
        # OPTIMIZATION: Load image once, reuse for all ROIs
        # This prevents reading the file from disk N times
        bold_img = image.load_img(str(bold_path))
    except Exception as e:
        print(f"Failed to load BOLD image: {e}")
        return None

    print("Extracting ROI signals...")
    roi_time_series = []
    roi_names = []

    for roi_path in roi_paths:
        roi_name = roi_path.name.replace('.nii.gz', '').replace('.nii', '')
        roi_names.append(roi_name)
        
        # SCIENTIFIC FIX: Added high_pass=0.01 (standard for resting/task connectivity)
        # NiftiMasker will handle filtering since the fallback confounds lack cosine terms
        masker = NiftiMasker(
            mask_img=str(roi_path), 
            standardize="zscore_sample",
            detrend=True,
            high_pass=0.01, # Crucial for removing drift
            t_r=TR,
            verbose=0
        )

        try:
            # Pass the loaded image object, not the path string
            ts = masker.fit_transform(
                bold_img, 
                confounds=confounds, 
                sample_mask=sample_mask
            )
            
            mean_ts = np.mean(ts, axis=1)
            roi_time_series.append(mean_ts)
            
            # MEMORY SAFETY: Delete the voxel-wise time series immediately
            del ts
            
        except Exception as e:
            print(f"Error extracting ROI {roi_name}: {e}")
            # Clean up memory before returning
            del bold_img
            gc.collect()
            return None

    # MEMORY SAFETY: Unload the heavy BOLD image
    del bold_img
    gc.collect()

    roi_time_series = np.array(roi_time_series).T
    
    # ==========================================
    # 4. COMPUTE CONNECTIVITY
    # ==========================================
    correlation_measure = ConnectivityMeasure(
        kind='correlation', 
        vectorize=False, 
        discard_diagonal=False
    )
    
    correlation_matrix = correlation_measure.fit_transform([roi_time_series])[0]

    # ==========================================
    # 5. VISUALIZATION & SAVING
    # ==========================================
    
    out_csv = os.path.join(subj_out_dir, f"{subject_label}_correlation_matrix.csv")
    df_corr = pd.DataFrame(correlation_matrix, index=roi_names, columns=roi_names)
    df_corr.to_csv(out_csv)
    print(f"Saved matrix to {out_csv}")

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
    plt.close('all') # 'all' ensures no hidden figures remain in memory
    
    return df_corr

if __name__ == "__main__":
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    try:
        roi_paths = get_roi_paths(ROI_DIR)
    except FileNotFoundError as e:
        print(e)
        exit()

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
            
            # MEMORY SAFETY: Force garbage collection between subjects
            gc.collect() 
        else:
            print(f"Skipping {subject_label}: BOLD file not found at {bold_file}")
