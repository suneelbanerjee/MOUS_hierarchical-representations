import matplotlib
matplotlib.use('Agg') 
import matplotlib.pyplot as plt
import matplotlib.patheffects as PathEffects

import numpy as np
import pandas as pd
from pathlib import Path
import sys
import warnings
from scipy import stats

# Try to import statsmodels for FDR correction
try:
    from statsmodels.stats import multitest
    HAS_STATSMODELS = True
except ImportError:
    HAS_STATSMODELS = False
    print("[Warning] 'statsmodels' not found. FDR correction will be skipped.")

def fisher_transform(r):
    """Pearson r -> Fisher z"""
    eps = 1e-5
    r_clipped = np.clip(r, -1 + eps, 1 - eps)
    return np.arctanh(r_clipped)

def inverse_fisher_transform(z):
    """Fisher z -> Pearson r"""
    return np.tanh(z)

def detect_label_from_filenames(filenames, folder_name):
    """
    Determines if a group is Auditory, Visual, or Rest based on filenames.
    Fallback: Uses the folder name.
    """
    has_auditory = any("sub-A" in name for name in filenames)
    has_visual = any("sub-V" in name for name in filenames)
    
    if has_auditory and not has_visual:
        return "Auditory"
    elif has_visual and not has_auditory:
        return "Visual"
    elif has_auditory and has_visual:
        return "Rest (Combined)"
    else:
        # Fallback to the folder name if filenames are ambiguous
        return f"Group ({folder_name})"

def load_group_matrices(directory):
    """
    Loads all correlation matrices from a directory.
    Returns: 
      - stack: 3D array (Subjects x ROIs x ROIs)
      - label: Detected Group Name (e.g. "Auditory")
      - roi_names: List of ROIs
    """
    directory = Path(directory)
    files = sorted(list(directory.rglob("*_correlation_matrix.csv")))
    
    if not files:
        print(f"[Error] No correlation matrices found in {directory}")
        return None, None, None
        
    matrices = []
    roi_names = None
    filenames = []
    
    print(f"   Loading {len(files)} subjects from: {directory.name}")
    
    for f in files:
        try:
            df = pd.read_csv(f, index_col=0)
            matrices.append(df.values)
            filenames.append(f.name)
            
            if roi_names is None:
                roi_names = df.index.tolist()
        except Exception as e:
            print(f"   [!] Error loading {f.name}: {e}")
            
    # Auto-detect label
    label = detect_label_from_filenames(filenames, directory.name)
    
    return np.array(matrices), label, roi_names

def compute_group_comparison(group1_stack, group2_stack, alpha=0.01):
    """
    Compares two groups using Independent Samples T-test on Fisher-Z data.
    """
    n_rois = group1_stack.shape[1]
    
    # 1. Fisher Z-transform inputs
    g1_z = fisher_transform(group1_stack)
    g2_z = fisher_transform(group2_stack)
    
    # 2. Calculate Mean Difference (in r space for readability)
    g1_mean_z = np.mean(g1_z, axis=0)
    g2_mean_z = np.mean(g2_z, axis=0)
    
    g1_mean_r = inverse_fisher_transform(g1_mean_z)
    g2_mean_r = inverse_fisher_transform(g2_mean_z)
    
    # Difference = Group 1 - Group 2
    diff_matrix_r = g1_mean_r - g2_mean_r
    np.fill_diagonal(diff_matrix_r, 0) 

    # 3. Independent T-test (Welch's t-test: equal_var=False)
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=RuntimeWarning)
        t_stats, raw_p = stats.ttest_ind(g1_z, g2_z, axis=0, equal_var=False, nan_policy='omit')
    
    np.fill_diagonal(raw_p, 1.0)
    
    # 4. FDR Correction
    if HAS_STATSMODELS:
        triu_idx = np.triu_indices(n_rois, k=1)
        p_flat = raw_p[triu_idx]
        
        reject, p_corrected, _, _ = multitest.multipletests(p_flat, alpha=alpha, method='fdr_bh')
        
        # Reconstruct Matrix
        p_adj = np.zeros((n_rois, n_rois))
        sig_mask = np.zeros((n_rois, n_rois), dtype=bool)
        
        p_adj[triu_idx] = p_corrected
        sig_mask[triu_idx] = reject
        
        # Symmetrize
        p_adj = p_adj + p_adj.T 
        sig_mask = sig_mask + sig_mask.T
        
        np.fill_diagonal(p_adj, 1.0)
        np.fill_diagonal(sig_mask, False)
    else:
        p_adj = raw_p
        sig_mask = raw_p < alpha

    return diff_matrix_r, p_adj, sig_mask

def plot_difference_heatmap(matrix, p_values, labels, output_path, title, g1_name, g2_name):
    """
    Plots the difference (Group 1 - Group 2).
    Uses the clean, non-bold style with asterisks.
    """
    fig, ax = plt.subplots(figsize=(14, 12))
    
    # Red-Blue Colormap
    # Red = Group 1 is stronger
    # Blue = Group 2 is stronger
    im = ax.imshow(matrix, cmap='RdBu_r', vmin=-0.5, vmax=0.5) 
    
    cbar = ax.figure.colorbar(im, ax=ax, shrink=0.8)
    # Label explicitly states the direction
    cbar.ax.set_ylabel(f"Difference ({g1_name} - {g2_name})", rotation=-90, va="bottom", fontsize=14)
    cbar.ax.tick_params(labelsize=12)
    
    ax.set_xticks(np.arange(len(labels)))
    ax.set_yticks(np.arange(len(labels)))
    ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=14, fontweight='bold')
    ax.set_yticklabels(labels, fontsize=14, fontweight='bold')
    
    rows, cols = matrix.shape
    for i in range(rows):
        for j in range(cols):
            val = matrix[i, j]
            p = p_values[i, j]
            
            # Format Number
            text_str = f"{val:.2f}"
            
            # Significance Asterisks
            if i != j:
                if p < 0.001: text_str += "\n***"
                elif p < 0.01: text_str += "\n**"
                elif p < 0.05: text_str += "\n*"
            
            # Text Color
            text_color = "white" if abs(val) > 0.25 else "black"
            
            # Draw Text (Normal weight, clean outline)
            text = ax.text(j, i, text_str,
                           ha="center", va="center", color=text_color,
                           fontsize=14, fontweight='normal')
            text.set_path_effects([PathEffects.withStroke(linewidth=1.5, foreground='gray' if text_color=='white' else 'white')])

    ax.set_title(title, fontsize=18, pad=20, fontweight='bold')
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()

def main():
    print("\n" + "="*50)
    print("   GROUP COMPARISON ANALYSIS (Fisher Z-Test)")
    print("="*50)

    # 1. Get Directories
    print("\n--- Group 1 Input ---")
    g1_path_str = input("   Path: ").strip()
    
    print("\n--- Group 2 Input ---")
    g2_path_str = input("   Path: ").strip()
    
    print("\n--- Output ---")
    out_path_str = input("   Save Results To: ").strip()
    output_dir = Path(out_path_str)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 2. Load Data & Detect Labels
    g1_mat, g1_label, g1_rois = load_group_matrices(g1_path_str)
    g2_mat, g2_label, g2_rois = load_group_matrices(g2_path_str)

    if g1_mat is None or g2_mat is None:
        sys.exit(1)

    # Handle case where both are detected as same type (e.g. comparing two auditory sub-groups)
    if g1_label == g2_label:
        g1_label = f"{g1_label}_{Path(g1_path_str).name}"
        g2_label = f"{g2_label}_{Path(g2_path_str).name}"

    print(f"\n   Detected Comparison: {g1_label} vs {g2_label}")
    print(f"   Direction: ({g1_label} - {g2_label})")
    print(f"   Red = Stronger in {g1_label}")
    print(f"   Blue = Stronger in {g2_label}")

    # 3. Check Compatibility
    if g1_rois != g2_rois:
        print("[Error] ROI names do not match between groups!")
        sys.exit(1)

    # 4. Run Statistics
    print("\nRunning Independent Samples T-Test...")
    diff_matrix, p_adj, sig_mask = compute_group_comparison(g1_mat, g2_mat, alpha=0.01)

    # 5. Save Results
    # Save Diff Matrix
    csv_path = output_dir / f"diff_matrix_{g1_label}_vs_{g2_label}.csv"
    pd.DataFrame(diff_matrix, index=g1_rois, columns=g1_rois).to_csv(csv_path)
    print(f"   Saved CSV: {csv_path}")

    # 6. Plot
    plot_path = output_dir / f"heatmap_{g1_label}_vs_{g2_label}.png"
    print(f"   Generating Heatmap: {plot_path}")
    
    plot_title = f"{g1_label} - {g2_label} (FDR p<0.01)"
    plot_difference_heatmap(diff_matrix, p_adj, g1_rois, plot_path, plot_title, g1_label, g2_label)

    print("\nDone!")

if __name__ == "__main__":
    main()