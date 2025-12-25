import os
import sys
import glob
import numpy as np
import pandas as pd
import scipy.io
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.colors as mcolors
from matplotlib.font_manager import FontProperties
from nilearn import plotting, reporting, datasets, image

# =========================================================
# HELPER FUNCTIONS
# =========================================================

def get_valid_directory(prompt_text):
    """Asks for a directory until a valid one is entered."""
    while True:
        path = input(f"{prompt_text}: ").strip().replace("'", "").replace('"', "")
        if os.path.isdir(path):
            return path
        print(f"  ! Directory not found: {path}")

def read_spm_defaults(spm_path):
    """Reads default threshold/extent from SPM.mat."""
    try:
        mat = scipy.io.loadmat(spm_path, squeeze_me=True, struct_as_record=False)
        return float(mat['SPM'].xVol.u), int(mat['SPM'].xVol.k)
    except:
        return 3.1, 0

def get_anatomical_label(x, y, z, atlas_img, labels):
    """Finds atlas label for MNI coordinate."""
    inv_affine = np.linalg.inv(atlas_img.affine)
    vx, vy, vz = image.coord_transform(x, y, z, inv_affine)
    ix, iy, iz = int(round(vx)), int(round(vy)), int(round(vz))
    if (0 <= ix < atlas_img.shape[0]) and (0 <= iy < atlas_img.shape[1]) and (0 <= iz < atlas_img.shape[2]):
        return labels[int(atlas_img.get_fdata()[ix, iy, iz])]
    return "Unknown"

# =========================================================
# MAIN SCRIPT
# =========================================================

def main():
    print("\n=== SPM VIEWER: FINAL PUBLICATION EDITION (REV 2) ===\n")

    # --- 1. AUTO-DISCOVERY ---
    target_dir = get_valid_directory("Enter your SPM Results Directory")
    
    # Find SPM.mat
    spm_mat_path = os.path.join(target_dir, "SPM.mat")
    if os.path.exists(spm_mat_path):
        print("  -> Found SPM.mat")
        def_u, def_k = read_spm_defaults(spm_mat_path)
    else:
        print("  -> No SPM.mat found. Using defaults.")
        def_u, def_k = 3.1, 0

    # Find T-maps
    tmaps = sorted(glob.glob(os.path.join(target_dir, "spmT_*.nii")))
    
    if len(tmaps) == 0:
        print("  ! No spmT_*.nii files found in this directory.")
        return
    elif len(tmaps) == 1:
        tmap_path = tmaps[0]
        print(f"  -> Found T-map: {os.path.basename(tmap_path)}")
    else:
        print("  -> Multiple T-maps found:")
        for i, p in enumerate(tmaps):
            print(f"     [{i+1}] {os.path.basename(p)}")
        choice = input("     Select one (number) [1]: ").strip()
        idx = int(choice) - 1 if choice.isdigit() else 0
        tmap_path = tmaps[idx]

    # --- 2. SETTINGS ---
    print("\n--- Settings ---")
    u_str = input(f"Height Threshold T [Default {def_u:.4f}]: ").strip()
    threshold = float(u_str) if u_str else def_u
    
    k_str = input(f"Extent Threshold k [Default {def_k}]: ").strip()
    extent = int(k_str) if k_str else def_k

    # --- 3. GENERATE TABLE ---
    print("\nProcessing Data...")
    try:
        table = reporting.get_clusters_table(tmap_path, stat_threshold=threshold, cluster_threshold=extent)
    except ValueError:
        print("  ! No significant clusters found at this threshold."); return

    # Clean Data
    tmap_img = image.load_img(tmap_path)
    voxel_vol = abs(np.linalg.det(tmap_img.affine[:3, :3]))
    
    table['Cluster Size (mm3)'] = pd.to_numeric(table['Cluster Size (mm3)'], errors='coerce').fillna(0)
    table['Size (k)'] = (table['Cluster Size (mm3)'] / voxel_vol).astype(int)
    table = table[table['Size (k)'] > 0] 
    
    print("  -> Looking up anatomical labels...")
    atlas = datasets.fetch_atlas_harvard_oxford('cort-maxprob-thr25-2mm')
    atlas_img = image.load_img(atlas.maps)
    table['Region'] = table.apply(lambda row: get_anatomical_label(row['X'], row['Y'], row['Z'], atlas_img, atlas.labels), axis=1)
    
    # Format Table
    df_display = table[['X', 'Y', 'Z', 'Region', 'Size (k)', 'Peak Stat']].copy()
    df_display.rename(columns={'Peak Stat': 'Peak T'}, inplace=True)
    
    # Precise rounding
    df_display['X'] = df_display['X'].round(0).astype(int)
    df_display['Y'] = df_display['Y'].round(0).astype(int)
    df_display['Z'] = df_display['Z'].round(0).astype(int)
    
    # Format Peak T as string with exactly 2 decimal places
    df_display['Peak T'] = df_display['Peak T'].apply(lambda x: f"{x:.2f}")

    # Save CSV Automatically
    csv_path = os.path.join(target_dir, "SPM_Result_Table.csv")
    df_display.to_csv(csv_path, index=False)
    print(f"  -> Saved Table: {csv_path}")

    # --- 4. PREPARE IMAGE ---
    print("  -> Masking image...")
    dat = tmap_img.get_fdata()
    dat[dat < threshold] = np.nan # Strict masking
    clean_img = image.new_img_like(tmap_img, dat)
    vmax = np.nanmax(dat)

    # --- 5. PLOTTING ---
    print("  -> Generating Figure...")
    
    fig = plt.figure(figsize=(11, 8.5), dpi=300)
    gs = fig.add_gridspec(2, 2, height_ratios=[3, 1], width_ratios=[1, 0.05], hspace=0.1, wspace=0.02)
    
    ax_brain = fig.add_subplot(gs[0, 0])
    ax_cbar  = fig.add_subplot(gs[0, 1])
    ax_table = fig.add_subplot(gs[1, :])

    # A. Brain
    cut_coords = [df_display.iloc[0]['X'], df_display.iloc[0]['Y'], df_display.iloc[0]['Z']] if not df_display.empty else None
    
    plotting.plot_stat_map(
        clean_img, threshold=threshold, display_mode='ortho', cut_coords=cut_coords,
        colorbar=False, cmap='jet', symmetric_cbar=False, vmax=vmax, title=None, axes=ax_brain
    )
    
    # Title styling
    ax_brain.set_title(f"T > {threshold:.2f}\nk > {extent}", fontsize=12, loc='left', fontweight='bold')

    # B. Slim Elegant Colorbar
    norm = mcolors.Normalize(vmin=threshold, vmax=vmax)
    # FIX 1: Added shrink=0.75 to make the colorbar shorter vertically
    cb = plt.colorbar(cm.ScalarMappable(norm=norm, cmap='jet'), cax=ax_cbar, shrink=0.75)
    cb.ax.tick_params(labelsize=8)
    cb.outline.set_visible(True); cb.outline.set_linewidth(0.5)

    # C. Table
    ax_table.axis('off')
    if not df_display.empty:
        cell_text = [[str(x) for x in row] for row in df_display.values]
        col_widths = [0.08, 0.08, 0.08, 0.45, 0.1, 0.1]
        
        the_table = ax_table.table(
            cellText=cell_text, colLabels=df_display.columns,
            loc='center', cellLoc='left', colWidths=col_widths, bbox=[0, 0, 1, 1]
        )
        the_table.auto_set_font_size(False); the_table.set_fontsize(9)
        
        # Define Arial Fonts
        arial_header = FontProperties(family='Arial', weight='bold', size=10)
        arial_data = FontProperties(family='Arial', size=10)

        for (row, col), cell in the_table.get_celld().items():
            cell.set_edgecolor('white'); cell.set_linewidth(0)
            if row == 0:
                # FIX 2 & 3: Thinner header height (0.08) and Arial font
                cell.set_text_props(fontproperties=arial_header, color='white', ha='left')
                cell.set_facecolor('#404040')
                cell.set_height(0.08) 
            else:
                # FIX 3: Arial font for data rows
                cell.set_text_props(fontproperties=arial_data, ha='left')
                cell.set_height(0.15)
                cell.set_facecolor('#f2f2f2' if row % 2 == 0 else 'white')
    else:
        ax_table.text(0.5, 0.5, "No Significant Clusters", ha='center', fontsize=12)

    # Save Image Automatically
    img_name = "SPM_Result_Final_Rev2.png"
    img_path = os.path.join(target_dir, img_name)
    plt.savefig(img_path, bbox_inches='tight', dpi=300)
    print(f"  -> Saved Figure: {img_path}")
    
    plt.show()

if __name__ == "__main__":
    main()