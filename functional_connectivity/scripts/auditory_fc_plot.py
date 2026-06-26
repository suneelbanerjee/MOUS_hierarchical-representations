import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from nilearn import plotting, image

# ==========================================
# CONFIGURATION
# ==========================================

# Path to the directory containing your subject subfolders/files
# Example structure: ./auditory_fc_results_1st_level/sub-A01_correlation_matrix.csv
RESULTS_DIR = Path('auditory_fc_results_1st_level')

# Path to the directory containing ROI masks (Needed for brain coordinates)
# CRITICAL: The alphabetical order of files in this directory must match 
# the row/column order of your connectivity matrices.
ROI_DIR = Path('/home/lillianchang/Documents/MOUS_hierarchical-representations/figures/ROI_masks/auditory')

# Pattern to match Auditory subjects files inside RESULTS_DIR
SUBJECT_PATTERN = 'sub-A*.csv' 

# Output setup
OUTPUT_DIR = Path('/home/lillianchang/Documents/MOUS_hierarchical-representations/auditory_fc_results_2nd_level')
OUTPUT_FILE = OUTPUT_DIR / 'group_average_auditory.csv'
MATRIX_PLOT_FILE = OUTPUT_DIR / 'group_average_auditory_matrix.png'
NETWORK_PLOT_FILE = OUTPUT_DIR / 'group_average_auditory_connectome.png'

# Create output directory if it doesn't exist
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ==========================================
# FUNCTIONS
# ==========================================

def get_roi_coordinates(roi_dir):
    """
    Calculates the center of mass (XYZ coordinates) for each NIfTI mask in the directory.
    Returns a list of coordinates and a list of labels (filenames).
    """
    print(f"Extracting coordinates from masks in: {roi_dir}")
    mask_files = sorted(list(roi_dir.glob('*.nii*'))) # Supports .nii and .nii.gz
    
    coords = []
    labels = []
    
    for mask_file in mask_files:
        # Calculate center of mass for the ROI
        roi_img = image.load_img(str(mask_file))
        center = plotting.find_xyz_cut_coords(roi_img)
        
        coords.append(center)
        labels.append(mask_file.stem.replace('mask_', '').replace('_roi', ''))
        
    print(f"Found {len(coords)} ROIs.")
    return np.array(coords), labels

def load_subject_matrices(results_dir, pattern):
    """
    Loads all subject CSV matrices matching the pattern.
    Returns a 3D numpy array (n_subjects, n_rois, n_rois).
    """
    print(f"Searching for subjects in: {results_dir} with pattern: {pattern}")
    # This searches recursively; remove rglob and use glob if files are flat in the dir
    subject_files = sorted(list(results_dir.rglob(pattern)))
    
    if not subject_files:
        raise FileNotFoundError(f"No files found matching {pattern} in {results_dir}")

    matrices = []
    for subj_file in subject_files:
        try:
            # Assuming CSVs have no headers/index. If they do, add header=0 or index_col=0
            df = pd.read_csv(subj_file, header=None) 
            matrices.append(df.values)
        except Exception as e:
            print(f"Error loading {subj_file.name}: {e}")

    if not matrices:
        raise ValueError("No valid matrices loaded.")

    # Stack into 3D array
    return np.array(matrices)

# ==========================================
# MAIN EXECUTION
# ==========================================

def main():
    # 1. Load ROI Coordinates
    try:
        coords, labels = get_roi_coordinates(ROI_DIR)
    except Exception as e:
        print(f"Failed to load ROIs: {e}")
        return

    # 2. Load Subject Matrices
    try:
        # matrix_stack shape: (n_subjects, n_rois, n_rois)
        matrix_stack = load_subject_matrices(RESULTS_DIR, SUBJECT_PATTERN)
        print(f"Loaded {matrix_stack.shape[0]} subject matrices.")
        
        # Verify dimensions match
        if matrix_stack.shape[1] != len(coords):
            print(f"WARNING: Matrix dimension ({matrix_stack.shape[1]}) does not match number of ROIs ({len(coords)}).")
            print("Please ensure the ROI directory contains exactly the masks used to generate the matrices.")
            return

    except Exception as e:
        print(f"Failed to load subject data: {e}")
        return

    # 3. Compute Group Average (Fisher Z-transform recommended for correlation, but simple mean here)
    # Note: If your inputs are raw Pearson r, it is statistically better to:
    # r -> z -> mean -> r. If inputs are already Z-transformed, simple mean is correct.
    # Here we assume simple mean for simplicity:
    group_avg_matrix = np.mean(matrix_stack, axis=0)
    
    # Save to CSV
    pd.DataFrame(group_avg_matrix, index=labels, columns=labels).to_csv(OUTPUT_FILE)
    print(f"Saved group average to: {OUTPUT_FILE}")

    # 4. Plotting
    
    # A. Adjacency Matrix
    plt.figure(figsize=(10, 8))
    plotting.plot_matrix(group_avg_matrix, 
                         labels=labels, 
                         colorbar=True, 
                         vmax=1.0, vmin=-1.0, 
                         title='Group Average Auditory FC')
    plt.savefig(MATRIX_PLOT_FILE)
    print(f"Saved matrix plot to: {MATRIX_PLOT_FILE}")
    plt.close()

    # B. Connectome (Brain Glass/Schematic)
    # Thresholding: only show top 20% of connections or absolute values > 0.3 to reduce clutter
    plt.figure(figsize=(12, 6))
    plotting.plot_connectome(group_avg_matrix, 
                             node_coords=coords, 
                             edge_threshold='80%', # Show top 20% strongest edges
                             title='Auditory Network Topology',
                             node_size=20,
                             colorbar=True)
    plt.savefig(NETWORK_PLOT_FILE)
    print(f"Saved connectome plot to: {NETWORK_PLOT_FILE}")
    plt.close()

    print("Done.")

if __name__ == "__main__":
    main()