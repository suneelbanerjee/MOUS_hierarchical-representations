import matplotlib
matplotlib.use('Agg') # Non-interactive backend
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
    """Pearson r -> Fisher z (clipped to avoid infinity)"""
    eps = 1e-5
    r_clipped = np.clip(r, -1 + eps, 1 - eps)
    return np.arctanh(r_clipped)

def inverse_fisher_transform(z):
    """Fisher z -> Pearson r"""
    return np.tanh(z)

def compute_stats(matrix_stack, alpha=0.01):
    """
    1. Fisher Z-transform all subject matrices.
    2. Perform 1-sample t-test against 0 for each edge.
    3. Apply FDR correction (Benjamini-Hochberg).
    Returns: group_avg_r, p_values, significant_mask
    """
    # 1. Transform to Z-scores
    z_stack = fisher_transform(matrix_stack)
    
    # 2. Group Average
    group_avg_z = np.mean(z_stack, axis=0)
    group_avg_r = inverse_fisher_transform(group_avg_z)
    np.fill_diagonal(group_avg_r, 1.0) 

    # 3. T-test (suppressing diagonal variance warnings)
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=RuntimeWarning, message="Precision loss occurred")
        t_stats, raw_p = stats.ttest_1samp(z_stack, 0, axis=0, nan_policy='omit')
    
    np.fill_diagonal(raw_p, 1.0) # Diagonal not significant
    
    # 4. FDR Correction
    n_rois = matrix_stack.shape[1]
    p_adj = raw_p.copy()
    sig_mask = raw_p < alpha

    if HAS_STATSMODELS:
        triu_idx = np.triu_indices(n_rois, k=1)
        p_flat = raw_p[triu_idx]
        
        reject, p_corrected, _, _ = multitest.multipletests(p_flat, alpha=alpha, method='fdr_bh')
        
        # --- FIXED BLOCK START ---
        # Initialize with ZEROS, not ones, so we can add the transpose safely
        p_adj = np.zeros((n_rois, n_rois))
        sig_mask = np.zeros((n_rois, n_rois), dtype=bool)
        
        # Fill Upper Triangle
        p_adj[triu_idx] = p_corrected
        sig_mask[triu_idx] = reject
        
        # Symmetrize by adding the Transpose
        # (Since lower triangle is 0, adding T(upper) moves values to lower)
        p_adj = p_adj + p_adj.T 
        sig_mask = sig_mask + sig_mask.T
        
        # Reset Diagonal (it was 0+0=0, which is significant! We must force it to 1.0)
        np.fill_diagonal(p_adj, 1.0)
        np.fill_diagonal(sig_mask, False)
        # --- FIXED BLOCK END ---

    return group_avg_r, p_adj, sig_mask

def plot_annotated_heatmap(matrix, p_values, labels, output_path, title):
    """
    Plots a heatmap with Red-Blue colormap.
    Uses Asterisks (*) for significance instead of bold text.
    """
    # Large figure size to prevent crowding
    fig, ax = plt.subplots(figsize=(14, 12))
    
    # Red-Blue Colormap
    im = ax.imshow(matrix, cmap='RdBu_r', vmin=-1, vmax=1)
    
    # Add Colorbar
    cbar = ax.figure.colorbar(im, ax=ax, shrink=0.8)
    cbar.ax.set_ylabel("Pearson's r", rotation=-90, va="bottom", fontsize=14)
    cbar.ax.tick_params(labelsize=12)
    
    # Axis ticks
    ax.set_xticks(np.arange(len(labels)))
    ax.set_yticks(np.arange(len(labels)))
    ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=14, fontweight='bold')
    ax.set_yticklabels(labels, fontsize=14, fontweight='bold')
    
    # Annotate Cells
    rows, cols = matrix.shape
    for i in range(rows):
        for j in range(cols):
            val = matrix[i, j]
            p = p_values[i, j]
            
            # 1. Format the Number
            text_str = f"{val:.2f}"
            
            # 2. Add Significance Asterisks (New Line)
            if i != j: # Skip diagonal
                if p < 0.001:
                    text_str += "\n***"
                elif p < 0.01:
                    text_str += "\n**"
                elif p < 0.05:
                    text_str += "\n*"
            
            # 3. Determine Text Color (White on dark, Black on light)
            text_color = "white" if abs(val) > 0.5 else "black"
            
            # 4. Draw Text
            text = ax.text(j, i, text_str,
                           ha="center", va="center", color=text_color,
                           fontsize=14, fontweight='normal') 
            
            # Add subtle outline for readability
            text.set_path_effects([PathEffects.withStroke(linewidth=1.5, foreground='gray' if text_color=='white' else 'white')])

    ax.set_title(title, fontsize=18, pad=20, fontweight='bold')
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()

def main():
    print("\n" + "="*50)
    print("   SECOND-LEVEL ANALYSIS (Stats & Heatmap)")
    print("="*50)

    # 1. Input/Output Setup
    print("\n1. Input Directory (Subjects)")
    input_dir_str = input("   Path: ").strip()
    input_dir = Path(input_dir_str)
    
    if not input_dir.exists():
        print("[Error] Directory not found.")
        sys.exit(1)

    print("\n2. Output Directory")
    output_dir_str = input("   Path: ").strip()
    output_dir = Path(output_dir_str)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 2. Load Data
    print(f"\nSearching for matrices in: {input_dir}")
    matrix_files = sorted(list(input_dir.rglob("*_correlation_matrix.csv")))
    
    if not matrix_files:
        print("[Error] No matrix files found.")
        sys.exit(1)
    
    matrices = []
    roi_names = None
    filenames = []
    
    for f in matrix_files:
        try:
            df = pd.read_csv(f, index_col=0)
            matrices.append(df.values)
            filenames.append(f.name)
            if roi_names is None:
                roi_names = df.index.tolist()
        except Exception:
            pass
            
    matrix_stack = np.array(matrices)
    print(f"   Loaded {len(matrices)} subjects.")

    # 3. Automatic Title Generation
    has_auditory = any("sub-A" in name for name in filenames)
    has_visual = any("sub-V" in name for name in filenames)

    if has_auditory and not has_visual:
        plot_title = "Auditory Group Functional Connectivity"
    elif has_visual and not has_auditory:
        plot_title = "Visual Group Functional Connectivity"
    else:
        plot_title = "Resting State Group Functional Connectivity (All Subjects)"
    
    print(f"   Detected Group: {plot_title}")

    # 4. Compute Stats
    print("\nComputing statistics (One-sample T-test + FDR)...")
    avg_r, p_adj, sig_mask = compute_stats(matrix_stack, alpha=0.01)

    # 5. Save Results
    csv_path = output_dir / "group_stats_matrix.csv"
    pd.DataFrame(avg_r, index=roi_names, columns=roi_names).to_csv(csv_path)
    print(f"   Saved Data: {csv_path}")

    # 6. Plot Annotated Heatmap
    plot_path = output_dir / "group_stats_heatmap.png"
    print(f"   Generating Heatmap: {plot_path}")
    
    plot_annotated_heatmap(
        avg_r, 
        p_adj, 
        roi_names, 
        plot_path, 
        title=plot_title
    )

    print("\nDone!")

if __name__ == "__main__":
    main()