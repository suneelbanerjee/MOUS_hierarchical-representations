import os
import sys
import glob
import numpy as np
import pandas as pd
import scipy.io
import scipy.ndimage as ndimage
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
    """
    Finds atlas label for MNI coordinate.
    If 'Background', searches 2-voxel radius (approx 4mm) for nearest gray matter label.
    """
    inv_affine = np.linalg.inv(atlas_img.affine)
    vx, vy, vz = image.coord_transform(x, y, z, inv_affine)
    cx, cy, cz = int(round(vx)), int(round(vy)), int(round(vz))
    
    def get_lbl_at(ix, iy, iz):
        if (0 <= ix < atlas_img.shape[0]) and (0 <= iy < atlas_img.shape[1]) and (0 <= iz < atlas_img.shape[2]):
            return labels[int(atlas_img.get_fdata()[ix, iy, iz])]
        return "Unknown"

    # 1. Check exact voxel
    label = get_lbl_at(cx, cy, cz)
    if label != "Background":
        return label
    
    # 2. If Background, search immediate neighbors (radius 2 voxels = ~4mm)
    candidates = []
    radius = 2 
    for dx in range(-radius, radius+1):
        for dy in range(-radius, radius+1):
            for dz in range(-radius, radius+1):
                if dx==0 and dy==0 and dz==0: continue
                
                curr_l = get_lbl_at(cx+dx, cy+dy, cz+dz)
                if curr_l != "Background" and curr_l != "Unknown":
                    # Calculate euclidean distance squared
                    dist_sq = dx**2 + dy**2 + dz**2
                    candidates.append((dist_sq, curr_l))
    
    # 3. Return closest valid neighbor
    if candidates:
        candidates.sort(key=lambda x: x[0]) # Sort by distance
        return candidates[0][1] # Return the name of the closest one

    return "Deep White Matter / CSF"

# =========================================================
# MAIN SCRIPT
# =========================================================

def main():
    print("\n=== SPM VIEWER: FINAL PUBLICATION EDITION (REV 12) ===\n")

    # --- 1. AUTO-DISCOVERY ---
    target_dir = get_valid_directory("Enter your SPM Results Directory")
    
    spm_mat_path = os.path.join(target_dir, "SPM.mat")
    if os.path.exists(spm_mat_path):
        print("  -> Found SPM.mat")
        def_u, def_k = read_spm_defaults(spm_mat_path)
        if def_k == 0:
            def_k = 20
    else:
        print("  -> No SPM.mat found. Using defaults.")
        def_u, def_k = 3.1, 20

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
        
    tmap_name = os.path.splitext(os.path.basename(tmap_path))[0]

    # --- 2. SETTINGS ---
    print("\n--- Settings ---")
    u_str = input(f"Height Threshold T [Default {def_u:.4f}]: ").strip()
    threshold = float(u_str) if u_str else def_u
    
    k_str = input(f"Extent Threshold k [Default {def_k}]: ").strip()
    extent = int(k_str) if k_str else def_k

    # --- 3. GENERATE TABLE (CUSTOM SPM-MATCHING) ---
    print("\nProcessing Data...")
    
    # Load data
    tmap_img = image.load_img(tmap_path)
    dat = tmap_img.get_fdata()
    voxel_vol = abs(np.linalg.det(tmap_img.affine[:3, :3]))
    
    # Threshold
    mask = dat > threshold
    
    # Cluster with 18-Connectivity (SPM Style)
    s = ndimage.generate_binary_structure(3, 2) 
    labeled_array, num_features = ndimage.label(mask, structure=s)
    
    clusters = []
    if num_features > 0:
        lbls, counts = np.unique(labeled_array, return_counts=True)
        if lbls[0] == 0: # Remove background
            lbls = lbls[1:]
            counts = counts[1:]
            
        print("  -> Looking up anatomical labels (with nearest-neighbor search)...")
        atlas = datasets.fetch_atlas_harvard_oxford('cort-maxprob-thr25-2mm')
        atlas_img = image.load_img(atlas.maps)

        for lbl, count in zip(lbls, counts):
            if count < extent: continue # Filter by k threshold
            
            # Extract cluster data
            cluster_mask = (labeled_array == lbl)
            
            # Find Peak
            inds = np.where(cluster_mask)
            cluster_vals = dat[inds]
            max_idx_local = np.argmax(cluster_vals)
            
            # Convert local index to full array coordinates
            max_val = cluster_vals[max_idx_local]
            z_idx = inds[0][max_idx_local]
            y_idx = inds[1][max_idx_local]
            x_idx = inds[2][max_idx_local]
            
            # Convert Voxel Coords -> MNI
            mni_coords = image.coord_transform(z_idx, y_idx, x_idx, tmap_img.affine)
            
            # Lookup Region
            region_name = get_anatomical_label(mni_coords[0], mni_coords[1], mni_coords[2], atlas_img, atlas.labels)
            
            clusters.append({
                'X': mni_coords[0],
                'Y': mni_coords[1],
                'Z': mni_coords[2],
                'Region': region_name,
                'Size (voxels)': count,
                'Cluster Peak T': max_val
            })

    df_display = pd.DataFrame(clusters)
    
    if df_display.empty:
        print("  ! No significant clusters found at this threshold.")
    else:
        # Sort by size for the table display
        df_display = df_display.sort_values(by='Size (voxels)', ascending=False)
        
        # Round coordinates
        df_display['X'] = df_display['X'].round(0).astype(int)
        df_display['Y'] = df_display['Y'].round(0).astype(int)
        df_display['Z'] = df_display['Z'].round(0).astype(int)
        
        # NOTE: We keep 'Cluster Peak T' as a float for now to find the global peak later.
        
    # --- 4. PREPARE IMAGE ---
    print("  -> Masking image...")
    # Reload to be safe and mask
    dat = tmap_img.get_fdata()
    vmax = np.nanmax(dat)
    dat[dat < threshold] = np.nan
    clean_img = image.new_img_like(tmap_img, dat)

    # --- 5. PLOTTING (DYNAMIC HEIGHT) ---
    print("  -> Generating Figure...")

    # Calculate Dynamic Figure Height
    brain_height_in = 6.0       
    header_height_in = 0.4      
    row_height_in = 0.3         
    
    num_rows = len(df_display)
    if num_rows == 0:
        table_height_in = 1.0 
    else:
        table_height_in = header_height_in + (num_rows * row_height_in)
    
    total_fig_height = brain_height_in + table_height_in + 0.5
    
    fig = plt.figure(figsize=(11, total_fig_height), dpi=300)
    
    gs = fig.add_gridspec(2, 2, height_ratios=[brain_height_in, table_height_in], 
                          width_ratios=[1, 0.015], hspace=0.1, wspace=0.05)
    
    ax_brain = fig.add_subplot(gs[0, 0])
    ax_cbar  = fig.add_subplot(gs[0, 1])
    ax_table = fig.add_subplot(gs[1, :])

    # Plot Brain
    # FIX: Select cut_coords based on Global Max T, not just the top row (biggest cluster)
    if not df_display.empty:
        # Find row index with maximum T
        max_t_idx = df_display['Cluster Peak T'].idxmax()
        peak_row = df_display.loc[max_t_idx]
        cut_coords = [peak_row['X'], peak_row['Y'], peak_row['Z']]
    else:
        cut_coords = None
    
    plotting.plot_stat_map(
        clean_img, threshold=threshold, display_mode='ortho', cut_coords=cut_coords,
        colorbar=False, cmap='jet', symmetric_cbar=False, vmax=vmax, title=None, axes=ax_brain
    )
    
    title_str = f"T > {threshold:.2f}\nk > {extent} voxels"
    ax_brain.set_title(title_str, fontsize=12, loc='left', fontweight='bold')

    # Plot Colorbar
    norm = mcolors.Normalize(vmin=threshold, vmax=vmax)
    mappable = cm.ScalarMappable(norm=norm, cmap='jet')
    
    cb = plt.colorbar(mappable, cax=ax_cbar)
    cb.ax.tick_params(labelsize=8)
    cb.outline.set_visible(True); cb.outline.set_linewidth(0.5)
    
    pos = ax_cbar.get_position()
    new_height = pos.height * 0.6
    new_y = pos.y0 + (pos.height - new_height) / 2
    ax_cbar.set_position([pos.x0, new_y, pos.width, new_height])

    # Plot Table
    ax_table.axis('off')
    if not df_display.empty:
        # NOW convert the T-stats to strings for display
        # We work on a copy so we don't break the float values if we needed them later
        df_table = df_display.copy()
        df_table['Cluster Peak T'] = df_table['Cluster Peak T'].apply(lambda x: f"{x:.2f}")

        # Save CSV (done here to include the string formatting)
        csv_path = os.path.join(target_dir, f"SPM_Result_Table_{tmap_name}.csv")
        df_table.to_csv(csv_path, index=False)
        print(f"  -> Saved Table: {csv_path}")

        cell_text = [[str(x) for x in row] for row in df_table.values]
        col_widths = [0.08, 0.08, 0.08, 0.45, 0.15, 0.16]
        
        the_table = ax_table.table(
            cellText=cell_text, colLabels=df_table.columns,
            loc='center', cellLoc='left', colWidths=col_widths, bbox=[0, 0, 1, 1]
        )
        the_table.auto_set_font_size(False); the_table.set_fontsize(9)
        
        try:
            arial_header = FontProperties(family='Arial', weight='bold', size=10)
            arial_data = FontProperties(family='Arial', size=10)
            arial_header.get_name() 
        except:
            arial_header = FontProperties(family='sans-serif', weight='bold', size=10)
            arial_data = FontProperties(family='sans-serif', size=10)

        total_units = header_height_in + (num_rows * row_height_in)
        header_norm = header_height_in / total_units
        row_norm = row_height_in / total_units

        for (row, col), cell in the_table.get_celld().items():
            cell.set_edgecolor('white'); cell.set_linewidth(0)
            if row == 0:
                cell.set_text_props(fontproperties=arial_header, color='white', ha='left')
                cell.set_facecolor('#404040')
                cell.set_height(header_norm) 
            else:
                cell.set_text_props(fontproperties=arial_data, ha='left')
                cell.set_height(row_norm)
                cell.set_facecolor('#f2f2f2' if row % 2 == 0 else 'white')
    else:
        ax_table.text(0.5, 0.5, "No Significant Clusters Found", ha='center', fontsize=14, color='gray')

    img_name = f"SPM_Result_{tmap_name}.png"
    img_path = os.path.join(target_dir, img_name)
    plt.savefig(img_path, bbox_inches='tight', dpi=300)
    print(f"  -> Saved Figure: {img_path}")
    
    plt.show()

if __name__ == "__main__":
    main()