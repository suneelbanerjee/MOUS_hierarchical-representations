import os
import ssl

# ===============================
# SSL BYPASS
# ===============================
os.environ['CURL_CA_BUNDLE'] = ""
os.environ['REQUESTS_CA_BUNDLE'] = ""
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

import matplotlib
matplotlib.use("Agg") # No GUI backend
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches 
import matplotlib.patheffects as PathEffects 
import matplotlib.colors as mcolors 

import numpy as np
import pandas as pd
from pathlib import Path
from nilearn import image, plotting, datasets
import nibabel as nib 
from collections import OrderedDict
from scipy import stats 

# ===============================
# OPTIONAL DEPENDENCIES
# ===============================
try:
    from adjustText import adjust_text
    HAS_ADJUST_TEXT = True
except ImportError:
    HAS_ADJUST_TEXT = False
    print("\n[Tip] Run 'pip install adjustText' for smart label placement!\n")

try:
    from statsmodels.stats import multitest
    HAS_STATSMODELS = True
except ImportError:
    HAS_STATSMODELS = False
    print("\n[Tip] Run 'pip install statsmodels' for FDR correction support!\n")

# ===============================
# CONFIGURATION
# ===============================

# ROI Masks Directory
ROI_ROOT_DIR = Path("/home/lillianchang/Documents/MOUS_hierarchical-representations/figures/ROI_masks")

# Results Directory
DEFAULT_OUTPUT_ROOT = Path("/home/lillianchang/Documents/MOUS_hierarchical-representations/functional_connectivity/results")

# ===============================
# HELPER FUNCTIONS
# ===============================

def find_results_directory(task_name):
    candidates = [
        DEFAULT_OUTPUT_ROOT,
        Path("./results"),
        Path("../results"),
        Path.cwd() / "results"
    ]
    for root in candidates:
        task_dir = root / task_name
        if task_dir.exists() and task_dir.is_dir():
            print(f"[Info] Found results directory: {task_dir}")
            return task_dir
    return None

def prompt_task():
    while True:
        task = input("Analyze which task? Type 'auditory' or 'visual': ").strip().lower()
        if task: return task 
        print("Invalid input.")

def _normalize_network_name(rel_dir: Path) -> str:
    name = "_".join(rel_dir.parts) if rel_dir.parts else "roi"
    if not name.endswith("clusters"): 
        name = f"{name}_clusters"
    return name

def get_nested_roi_entries(roi_root_dir: Path):
    roi_root_dir = Path(roi_root_dir)
    if not roi_root_dir.exists():
        print(f"[Error] ROI Directory not found: {roi_root_dir}")
        return []
    candidate_dirs = sorted([d for d in roi_root_dir.rglob("*") if d.is_dir() and list(d.glob("*.nii*"))])
    entries = []
    for d in candidate_dirs:
        rel = d.relative_to(roi_root_dir)
        network = _normalize_network_name(rel)
        for rp in sorted(list(d.glob("*.nii")) + list(d.glob("*.nii.gz"))):
            roi_name = rp.name.replace(".nii.gz", "").replace(".nii", "")
            entries.append({"network": network, "roi_name": roi_name, "roi_label": f"{network}:{roi_name}", "path": rp})
    return sorted(entries, key=lambda x: (x["network"], x["roi_name"]))

def list_available_roi_sets(roi_entries):
    nets = sorted(set(e["network"] for e in roi_entries))
    print("\nAvailable ROI sets (Contrasts):")
    for i, n in enumerate(nets, start=1): print(f"  [{i}] {n}")
    return nets

def prompt_roi_set_selection(available_sets):
    available_sets = list(available_sets)
    available_lc = {s.lower(): s for s in available_sets}
    while True:
        s = input("\nSelect ROI set(s) (type 'all' or '1,3'): ").strip()
        if s.lower() == "all": return set(available_sets)
        tokens = [t.strip() for t in s.split(",") if t.strip()]
        chosen = set()
        for t in tokens:
            if t.isdigit() and 1 <= int(t) <= len(available_sets): chosen.add(available_sets[int(t)-1])
            elif t.lower() in available_lc: chosen.add(available_lc[t.lower()])
        if chosen: return chosen
        print("Invalid selection.")

def filter_roi_entries_by_sets(roi_entries, selected_sets):
    return [e for e in roi_entries if e["network"] in selected_sets]

def make_network_colors(network_names):
    network_names = list(OrderedDict.fromkeys(network_names))
    cmap = plt.get_cmap("tab20")
    return {n: cmap(i % 20) for i, n in enumerate(network_names)}

def fisher_z_mean(corr_stack):
    eps = 1e-7
    z = np.arctanh(np.clip(corr_stack, -1 + eps, 1 - eps))
    return np.tanh(np.mean(z, axis=0))

def get_short_prefix(network_name):
    clean = network_name.replace("_clusters", "").upper()
    return clean[:3]

# ===============================
# STATISTICAL TESTING
# ===============================

def compute_significance(corr_stack, alpha=0.05, fdr=True):
    if corr_stack is None:
        print("  [Warning] No subject data available for significance testing.")
        return None, None
    print(f"  Performing T-test (N={corr_stack.shape[0]})...")
    with np.errstate(invalid='ignore'):
        eps = 1e-7
        z_stack = np.arctanh(np.clip(corr_stack, -1 + eps, 1 - eps))
        t_vals, raw_p = stats.ttest_1samp(z_stack, 0, axis=0, nan_policy='omit')
    np.fill_diagonal(raw_p, 1.0) 
    
    n_rois = corr_stack.shape[1]
    mask = np.zeros((n_rois, n_rois), dtype=bool)
    final_p = raw_p.copy()

    if fdr and HAS_STATSMODELS:
        print(f"  Applying FDR correction (Benjamini-Hochberg, alpha={alpha})...")
        triu_indices = np.triu_indices(n_rois, k=1)
        p_flat = raw_p[triu_indices]
        reject, p_adjusted, _, _ = multitest.multipletests(p_flat, alpha=alpha, method='fdr_bh')
        mask[triu_indices] = reject
        mask = mask + mask.T
        p_adj_matrix = np.ones((n_rois, n_rois))
        p_adj_matrix[triu_indices] = p_adjusted
        p_adj_matrix = np.minimum(p_adj_matrix, p_adj_matrix.T)
        final_p = p_adj_matrix
        np.fill_diagonal(mask, True) 
    else:
        if fdr and not HAS_STATSMODELS:
            print("  [Warning] statsmodels not found. Falling back to uncorrected p.")
        mask = raw_p < alpha
        final_p = raw_p
    return mask, final_p

def get_star_string(p_val):
    if p_val < 0.001: return "***"
    if p_val < 0.01: return "**"
    if p_val < 0.05: return "*"
    return ""

def annotate_heatmap(ax, data_matrix, p_matrix=None):
    rows, cols = data_matrix.shape
    for i in range(rows):
        for j in range(cols):
            val = data_matrix[i, j]
            label = f"{val:.2f}"
            if p_matrix is not None and i != j:
                stars = get_star_string(p_matrix[i, j])
                if stars: label += f"\n{stars}"
            text_color = 'white' if abs(val) > 0.4 else 'black'
            txt = ax.text(j, i, label, ha="center", va="center", color=text_color, fontsize=8, fontweight='bold')
            txt.set_path_effects([PathEffects.withStroke(linewidth=2, foreground='gray' if text_color=='white' else 'white')])

# ===============================
# COORDINATE CALCULATION
# ===============================

def calculate_weighted_centroid(roi_img, tmap_img):
    """Calculates Center of Mass weighted by T-values"""
    roi_res = image.resample_to_img(roi_img, tmap_img, interpolation='nearest')
    roi_data = roi_res.get_fdata()
    tmap_data = tmap_img.get_fdata()
    mask_bool = roi_data > 0.5
    voxel_coords = np.array(np.nonzero(mask_bool)) 
    weights = tmap_data[mask_bool] 
    weights = np.maximum(weights, 0)
    
    if weights.sum() > 0:
        weighted_voxel_centroid = np.average(voxel_coords, axis=1, weights=weights)
        centroid_mni = nib.affines.apply_affine(tmap_img.affine, weighted_voxel_centroid)
        return centroid_mni
    return None

def calculate_peak_coordinate(roi_img, tmap_img):
    """Finds the single voxel with the absolute MAX T-value within the ROI"""
    roi_res = image.resample_to_img(roi_img, tmap_img, interpolation='nearest')
    roi_data = roi_res.get_fdata()
    tmap_data = tmap_img.get_fdata()
    
    # Mask T-map (set outside voxels to -infinity)
    masked_tmap = np.where(roi_data > 0.5, tmap_data, -np.inf)
    
    # Check if ROI is empty
    if np.all(masked_tmap == -np.inf):
        return None
        
    # Find index of max value
    flat_idx = np.argmax(masked_tmap)
    idx_tuple = np.unravel_index(flat_idx, masked_tmap.shape)
    
    # Convert to MNI
    peak_mni = nib.affines.apply_affine(tmap_img.affine, idx_tuple)
    return peak_mni

def get_roi_coordinates(roi_entries, tmap_map=None, method="centroid"):
    coords, labels, networks = [], [], []
    loaded_tmaps = {}
    
    if tmap_map:
        print(f"\nRefining coordinates using method: {method.upper()}...")
        for net, path in tmap_map.items():
            if path and os.path.exists(path):
                try: loaded_tmaps[net] = nib.load(path) 
                except Exception: loaded_tmaps[net] = None
            else: loaded_tmaps[net] = None
    else:
        print("\nCalculating geometric coordinates (Default)...")

    for e in roi_entries:
        roi_img = nib.load(str(e["path"]))
        network = e["network"]
        tmap_img = loaded_tmaps.get(network)
        calculated_coord = None
        
        if tmap_img:
            try: 
                if method == "peak":
                    calculated_coord = calculate_peak_coordinate(roi_img, tmap_img)
                else:
                    calculated_coord = calculate_weighted_centroid(roi_img, tmap_img)
            except Exception: pass
            
        if calculated_coord is None:
            # Fallback
            calculated_coord = plotting.find_xyz_cut_coords(roi_img)
            
        coords.append(calculated_coord)
        labels.append(e["roi_label"])
        networks.append(e["network"])
    return np.asarray(coords), labels, networks

# ===============================
# PLOTTING HELPERS
# ===============================

def scale_edge_widths_by_p(display, adj_matrix, p_matrix, threshold):
    if p_matrix is None: return
    rows, cols = np.triu_indices_from(adj_matrix, k=1)
    valid_mask = np.abs(adj_matrix[rows, cols]) >= threshold
    valid_p = p_matrix[rows, cols][valid_mask]
    
    widths = 1.0 - np.log10(np.maximum(valid_p, 1e-10))
    widths = np.clip(widths, 1.0, 8.0)
    
    for ax in display.axes.values():
        mpl_ax = getattr(ax, 'ax', ax)
        for collection in mpl_ax.collections:
            if isinstance(collection, matplotlib.collections.LineCollection):
                if len(collection.get_paths()) == len(widths):
                    collection.set_linewidth(widths)

def annotate_nodes_on_display(display, coords, anatomical_names, networks, show_anat=True, show_coords=True):
    if not show_anat and not show_coords: return
    for ax_name, ax_wrapper in display.axes.items():
        ax = getattr(ax_wrapper, 'ax', ax_wrapper) 
        texts = [] 
        for i, ((x, y, z), anat, net) in enumerate(zip(coords, anatomical_names, networks)):
            clean_name = clean_label_string(anat) or "Unknown"
            coord_str = f"({int(x)}, {int(y)}, {int(z)})"
            prefix = f"[{get_short_prefix(net)}]"
            label_parts = []
            if show_anat: label_parts.append(f"{prefix} {clean_name}")
            if show_coords: label_parts.append(coord_str)
            label_text = "\n".join(label_parts)
            px, py = 0, 0
            if ax_name in ['x', 'l', 'r']: px, py = y, z
            elif ax_name == 'y': px, py = x, z
            elif ax_name == 'z': px, py = x, y
            else: continue 
            offset_y = 2.0 
            if not HAS_ADJUST_TEXT: offset_y += (i % 2) * 3 
            txt = ax.text(px, py + offset_y, label_text, fontsize=8, color='black', fontweight='bold', ha='center', va='bottom', zorder=1000)
            txt.set_path_effects([PathEffects.withStroke(linewidth=3, foreground='white')]) 
            texts.append(txt)
        if HAS_ADJUST_TEXT and texts:
            try: adjust_text(texts, ax=ax, arrowprops=dict(arrowstyle='-', color='gray', lw=0.5, zorder=999), force_text=(0.3, 0.5), expand_points=(1.5, 1.5)) 
            except Exception: pass

def trace_roi_outlines(display, roi_entries, node_colors):
    print("  Tracing ROI outlines...")
    for entry, color in zip(roi_entries, node_colors):
        try: display.add_contours(str(entry['path']), colors=[color], linewidths=1.5, levels=[0.5])
        except Exception: pass

def get_robust_anatomical_labels(coords):
    print("Fetching Harvard-Oxford Atlas for robust labeling...")
    atlas = datasets.fetch_atlas_harvard_oxford('cort-maxprob-thr25-2mm')
    atlas_img = image.load_img(atlas.maps)
    
    def get_single_label(x, y, z):
        inv_affine = np.linalg.inv(atlas_img.affine)
        vx, vy, vz = image.coord_transform(x, y, z, inv_affine)
        cx, cy, cz = int(round(vx)), int(round(vy)), int(round(vz))
        data = atlas_img.get_fdata()
        def get_lbl(ix, iy, iz):
            if (0 <= ix < data.shape[0]) and (0 <= iy < data.shape[1]) and (0 <= iz < data.shape[2]):
                val = int(data[ix, iy, iz])
                if val < len(atlas.labels): return atlas.labels[val]
            return "Unknown"
        lbl = get_lbl(cx, cy, cz)
        if lbl not in ["Background", "Unknown", "Deep White Matter"]: return lbl
        candidates = []
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                for dz in range(-2, 3):
                    if dx==0 and dy==0 and dz==0: continue
                    cl = get_lbl(cx+dx, cy+dy, cz+dz)
                    if cl not in ["Background", "Unknown", "Deep White Matter"]:
                        candidates.append((dx**2+dy**2+dz**2, cl))
        if candidates:
            candidates.sort(key=lambda x: x[0])
            return candidates[0][1]
        return "Unknown"

    return [get_single_label(x, y, z) for x, y, z in coords]

def clean_label_string(label):
    return label.replace("Left", "").replace("Right", "").replace("Background", "").strip()

def print_label_summary(coords, anatomical_names, networks):
    print("\n" + "="*70)
    print(f"{'INDEX':<6} {'SOURCE':<10} {'ANATOMICAL REGION':<30} {'COORDS':<20}")
    print("="*70)
    for i, ((x, y, z), anat, net) in enumerate(zip(coords, anatomical_names, networks)):
        prefix = f"[{get_short_prefix(net)}]"
        print(f"{i+1:<6} {prefix:<10} {clean_label_string(anat):<30} ({int(x)}, {int(y)}, {int(z)})")
    print("="*70 + "\n")

# ===============================
# DATA LOADING (ROBUST)
# ===============================

def load_existing_matrices(task_name, target_labels):
    if not target_labels: return None
    task_dir = find_results_directory(task_name)
    if not task_dir:
        print(f"\n[Warning] Could not find subject results directory for '{task_name}'.")
        return None
    print(f"\nLoading matrices from: {task_dir}")
    matrices = []
    subjects = sorted([d for d in task_dir.iterdir() if d.is_dir()])
    
    for subj_dir in subjects:
        subj_label = subj_dir.name
        csv_path = subj_dir / f"{subj_label}_correlation_matrix.csv"
        if csv_path.exists():
            try:
                df = pd.read_csv(csv_path, index_col=0)
                df.index = df.index.astype(str)
                common = [l for l in target_labels if l in df.index]
                if len(common) != len(target_labels): continue 
                df_subset = df.loc[target_labels, target_labels]
                matrices.append(df_subset.values)
            except Exception: pass

    if not matrices:
        print("  [Warning] No valid subject matrices found.")
        return None
    print(f"Successfully loaded {len(matrices)} subject matrices.")
    return np.array(matrices)

def load_manual_group_matrix(target_labels):
    print("\n" + "!"*60)
    print("Subject matrices not found. Stats/P-values will be unavailable.")
    print("!"*60)
    path_str = input("Enter path to pre-computed Group Average CSV (or Enter to quit): ").strip()
    if not path_str: return None
    try:
        csv_path = Path(path_str.replace("'", "").replace('"', ""))
        df = pd.read_csv(csv_path, index_col=0)
        df.index = df.index.astype(str)
        df = df.loc[target_labels, target_labels]
        print("Loaded group matrix successfully.")
        return df.values
    except Exception as e:
        print(f"Failed to load file: {e}")
        return None

# ===============================
# MAIN MENU
# ===============================

def interactive_menu(corr_stack, group_avg_matrix, coords, node_colors, group_dir, task_name, anatomical_names, roi_entries, networks, labels):
    group_dir.mkdir(parents=True, exist_ok=True)
    coords_refined = False
    CAN_DO_STATS = (corr_stack is not None)
    
    def perform_refinement():
        nonlocal coords, anatomical_names, coords_refined, labels, networks
        if coords_refined: return
        
        want_refine = input("\n  > Refine coordinates using T-maps? (Recommended) (y/n) [y]: ").strip().lower() != 'n'
        if want_refine:
            unique_networks = sorted(list(set(e["network"] for e in roi_entries)))
            tmap_map = {}
            print("    For each ROI set, enter path to SPM T-map (Enter to skip):")
            for net in unique_networks:
                tmap_input = input(f"    - Path for '{net}': ").strip()
                clean_path = tmap_input.replace("'", "").replace('"', "")
                tmap_map[net] = clean_path if clean_path else None
            
            # ASK METHOD: CENTROID OR PEAK
            method_input = input("    > Method? (1=Weighted Centroid, 2=Peak Voxel) [1]: ").strip()
            method = "peak" if method_input == "2" else "centroid"

            coords, labels, networks = get_roi_coordinates(roi_entries, tmap_map, method=method)
            anatomical_names = get_robust_anatomical_labels(coords)
            print_label_summary(coords, anatomical_names, networks)
            coords_refined = True

    while True:
        print("\n" + "="*40)
        print(f"   VISUALIZATION MENU: {task_name.upper()}")
        print("="*40)
        print("1. Static Connectome (Glass Brain)")
        print("2. Interactive 3D (HTML)")
        print("3. Correlation Matrix (Heatmap)")
        print("4. Exit")
        
        choice = input("\nSelect option [1-4]: ").strip()
        
        if choice == "1":
            # OPTION 1
            perform_refinement() # Ask for coordinates now if needed
            
            v_choice = input("  > View (1=ortho, 2=panorama, 3=top) [1]: ").strip()
            display_mode = {"1":"ortho", "2":"lzry", "3":"z"}.get(v_choice, "ortho")
            thresh_raw = input("  > Threshold [80%]: ").strip()
            custom_title = input(f"  > Plot Title [Group Average {task_name}]: ").strip()
            
            hide_sig = input("  > Hide non-significant connections? (y/n) [n]: ").strip().lower() == 'y'
            opt_width = input("  > Scale line width by Significance (p-value)? (y/n) [y]: ").strip().lower() != 'n'
            
            plot_matrix = group_avg_matrix.copy()
            title_suffix = ""
            p_matrix = np.ones_like(group_avg_matrix)
            
            if (hide_sig or opt_width) and CAN_DO_STATS:
                print("    Computing statistics...")
                alpha_input = input("    > Alpha (e.g., 0.05) [0.05]: ").strip()
                alpha = float(alpha_input) if alpha_input else 0.05
                use_fdr = input("    > Apply FDR Correction? (y/n) [y]: ").strip().lower() != 'n'
                sig_mask, p_computed = compute_significance(corr_stack, alpha=alpha, fdr=use_fdr)
                p_matrix = p_computed
                if hide_sig:
                    plot_matrix[~sig_mask] = 0
                    corr_type = "FDR" if use_fdr else "Uncorrected"
                    title_suffix = f" (Masked: {corr_type} p<{alpha})"

            r_threshold = 0.5
            vmin_val, vmax_val = -1.0, 1.0
            cbar_ticks, cbar_labels = [-1, 0, 1], ["-1", "0", "1"]
            cbar_title = "Pearson's r"
            title_str = "Custom Threshold"

            if not thresh_raw: thresh_raw = "80%"
            
            if "%" in thresh_raw:
                try:
                    pct = float(thresh_raw.replace("%", ""))
                    matrix_vals = group_avg_matrix[np.triu_indices_from(group_avg_matrix, k=1)]
                    r_threshold = np.percentile(matrix_vals, pct)
                    title_str = f"Top {100-pct:.0f}% (r > {r_threshold:.2f})"
                    vmin_val = r_threshold
                    cbar_ticks = [vmin_val, vmax_val]
                    cbar_labels = [f"{pct:.0f}%", "100%"]
                    cbar_title = "Percentile Rank"
                except: r_threshold = 0.8
            else:
                try:
                    val = float(thresh_raw)
                    r_threshold = val
                    title_str = f"r > {val}"
                    vmin_val = val
                    cbar_ticks = [val, 1.0]
                    cbar_labels = [f"{val}", "1.0"]
                    cbar_title = "Connection Strength (r)"
                except: r_threshold = 0.8

            final_title = f"{custom_title}{title_suffix}" if custom_title else f"{task_name} ({title_str}){title_suffix}"
            size_raw = input("  > Node Size [30]: ").strip()
            node_size = float(size_raw) if size_raw else 30.0

            print("\n  --- Visual Options ---")
            opt_anat = input("  > Show Anatomical Labels? (y/n) [y]: ").strip().lower() != 'n'
            opt_coords = input("  > Show Coordinates? (y/n) [y]: ").strip().lower() != 'n'
            opt_outline = input("  > Trace ROI Outlines? (y/n) [y]: ").strip().lower() != 'n'

            suffix = input(f"\n  > Filename suffix [{display_mode}]: ").strip()
            if not suffix: suffix = display_mode
            out_path = group_dir / f"group_{task_name}_{suffix}.png"
            
            print(f"  Generating {out_path}...")
            fig = plt.figure(figsize=(18, 10)) 
            display = plotting.plot_connectome(plot_matrix, node_coords=coords, edge_threshold=r_threshold, edge_cmap="jet", 
                                               edge_vmin=vmin_val, edge_vmax=vmax_val, title=final_title, node_size=node_size, 
                                               node_color=node_colors, display_mode=display_mode, colorbar=False, figure=fig)
            
            if opt_width and CAN_DO_STATS:
                scale_edge_widths_by_p(display, plot_matrix, p_matrix, r_threshold)
            
            if opt_outline: trace_roi_outlines(display, roi_entries, node_colors)
            annotate_nodes_on_display(display, coords, anatomical_names, networks, show_anat=opt_anat, show_coords=opt_coords)

            cbar_ax = fig.add_axes([0.3, 0.05, 0.4, 0.02]) 
            norm = mcolors.Normalize(vmin=vmin_val, vmax=vmax_val)
            sm = plt.cm.ScalarMappable(cmap="jet", norm=norm)
            sm.set_array([]) 
            cbar = fig.colorbar(sm, cax=cbar_ax, orientation='horizontal')
            cbar.set_ticks(cbar_ticks)
            cbar.set_ticklabels(cbar_labels)
            cbar.set_label(cbar_title, labelpad=5)
            
            unique_net_map = {n: c for n, c in zip(networks, node_colors)}
            legend_handles = [mpatches.Patch(color=unique_net_map[n], label=get_short_prefix(n)) for n in sorted(unique_net_map.keys())]
            fig.legend(handles=legend_handles, title="ROI Sets", loc="lower right", bbox_to_anchor=(0.98, 0.08), fontsize='medium', frameon=True)

            plt.savefig(out_path, dpi=300, bbox_inches='tight') 
            plt.close()
            print("  Done.")
        
        elif choice == "2":
            # OPTION 2
            perform_refinement()
            thresh_raw = input("  > Threshold [80%]: ").strip()
            if not thresh_raw: thresh_raw = "80%"
            out_file = group_dir / f"group_{task_name}_interactive.html"
            print("  Generating Interactive HTML...")
            view = plotting.view_connectome(group_avg_matrix, coords, edge_threshold=thresh_raw)
            view.save_as_html(str(out_file))
            print(f"  Saved to: {out_file}")

        elif choice == "3":
            # OPTION 3: HEATMAP
            perform_refinement() # Ensure we have the latest coords (Peaks or Centroids)
            
            out_file = group_dir / f"group_{task_name}_matrix.png"
            fig, ax = plt.subplots(figsize=(14, 12))
            
            im = ax.imshow(group_avg_matrix, cmap='jet', vmin=-1, vmax=1)
            cbar = plt.colorbar(im, label="Pearson's r", shrink=0.8)
            
            ax.set_xticks(range(len(labels)))
            ax.set_yticks(range(len(labels)))
            
            # --- GENERATE COMPREHENSIVE LABELS ---
            full_axis_labels = []
            for i, (raw_label, anat_name, (x, y, z), net) in enumerate(zip(labels, anatomical_names, coords, networks)):
                prefix = get_short_prefix(net)
                clean_anat = clean_label_string(anat_name)
                coord_str = f"({int(x)},{int(y)},{int(z)})"
                full_label = f"[{prefix}] {clean_anat} {coord_str}"
                full_axis_labels.append(full_label)

            ax.set_xticklabels(full_axis_labels)
            ax.set_yticklabels(full_axis_labels)

            # --- CHANGE FONT SIZE HERE ---
            plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor", fontsize=10)
            plt.setp(ax.get_yticklabels(), fontsize=10)
            
            ax.set_title(f"Connectivity Matrix: {task_name.upper()}", fontsize=14, pad=20)
            
            if CAN_DO_STATS:
                print("  Computing stats for matrix annotation...")
                sig_mask, p_vals = compute_significance(corr_stack, alpha=0.05, fdr=True)
                annotate_heatmap(ax, group_avg_matrix, p_matrix=p_vals)
            else:
                annotate_heatmap(ax, group_avg_matrix, p_matrix=None)
                
            plt.tight_layout()
            plt.savefig(out_file, dpi=300, bbox_inches='tight')
            plt.close()
            print(f"  Saved to: {out_file}")

        elif choice == "4":
            print("Exiting...")
            break
        else:
            print("Invalid option.")

# ===============================
# MAIN
# ===============================

if __name__ == "__main__":
    task_name = prompt_task()
    all_entries = get_nested_roi_entries(ROI_ROOT_DIR)
    available = list_available_roi_sets(all_entries)
    selected = prompt_roi_set_selection(available)
    roi_entries = filter_roi_entries_by_sets(all_entries, selected)
    
    unique_networks = sorted(list(set(e["network"] for e in roi_entries)))
    
    # 1. Initial Coords
    coords, labels, networks = get_roi_coordinates(roi_entries, tmap_map=None)
    node_colors = [make_network_colors(networks)[n] for n in networks]
    anatomical_names = get_robust_anatomical_labels(coords)
    print_label_summary(coords, anatomical_names, networks)

    # 2. Data
    corr_stack = load_existing_matrices(task_name, labels)
    group_avg = None
    
    if corr_stack is None:
        group_avg = load_manual_group_matrix(labels)
        if group_avg is None:
            print("No data available. Exiting.")
            exit()
    else:
        group_avg = fisher_z_mean(corr_stack)
        
    task_dir = find_results_directory(task_name)
    GROUP_DIR = (task_dir if task_dir else DEFAULT_OUTPUT_ROOT / task_name) / "group_analysis"
    
    interactive_menu(corr_stack, group_avg, coords, node_colors, GROUP_DIR, task_name, anatomical_names, roi_entries, networks, labels)