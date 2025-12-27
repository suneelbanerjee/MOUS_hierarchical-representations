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
matplotlib.use("Agg") 
import matplotlib.pyplot as plt
import matplotlib.patheffects as PathEffects 
import matplotlib.colors as mcolors 

import numpy as np
import pandas as pd
import re
import json
from pathlib import Path
from nilearn import image, plotting, datasets
from collections import OrderedDict

# ===============================
# OPTIONAL DEPENDENCY: adjustText
# ===============================
try:
    from adjustText import adjust_text
    HAS_ADJUST_TEXT = True
except ImportError:
    HAS_ADJUST_TEXT = False
    print("\n[Tip] Run 'pip install adjustText' for smart label placement!\n")

# ===============================
# CONFIG
# ===============================

OUTPUT_ROOT = Path("./results")
ROI_ROOT_DIR = Path("/home/lillianchang/Documents/MOUS_hierarchical-representations/figures/ROI_masks")

# ===============================
# HELPER FUNCTIONS
# ===============================

def prompt_task():
    while True:
        task = input("Analyze which task? Type 'auditory' or 'visual': ").strip().lower()
        if task in {"auditory", "visual"}: return task
        print("Invalid. Type 'auditory' or 'visual'.")

def _normalize_network_name(rel_dir: Path) -> str:
    name = "_".join(rel_dir.parts) if rel_dir.parts else "roi"
    if not name.endswith("clusters"): 
        name = f"{name}_clusters"
    return name

def get_nested_roi_entries(roi_root_dir: Path):
    roi_root_dir = Path(roi_root_dir)
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

def get_roi_coordinates_from_entries(roi_entries):
    print("Loading ROI coordinates for plotting...")
    coords, labels, networks = [], [], []
    for e in roi_entries:
        coords.append(plotting.find_xyz_cut_coords(image.load_img(str(e["path"]))))
        labels.append(e["roi_label"])
        networks.append(e["network"])
    return np.asarray(coords), labels, networks

def make_network_colors(network_names):
    network_names = list(OrderedDict.fromkeys(network_names))
    cmap = plt.get_cmap("tab20")
    return {n: cmap(i % 20) for i, n in enumerate(network_names)}

def fisher_z_mean(corr_stack):
    eps = 1e-7
    z = np.arctanh(np.clip(corr_stack, -1 + eps, 1 - eps))
    return np.tanh(np.mean(z, axis=0))

# ===============================
# AAL & LABEL GENERATION
# ===============================

def get_aal_labels_for_coords(coords):
    print("Fetching AAL Atlas for automatic labeling...")
    aal = datasets.fetch_atlas_aal(version='SPM12') 
    atlas_img = image.load_img(aal.maps)
    atlas_data = atlas_img.get_fdata()
    inv_affine = np.linalg.inv(atlas_img.affine)
    
    aal_labels = []
    for x, y, z in coords:
        vox = image.coord_transform(x, y, z, inv_affine)
        i, j, k = int(round(vox[0])), int(round(vox[1])), int(round(vox[2]))
        
        found_label = "Unknown"
        if (0 <= i < atlas_data.shape[0]) and (0 <= j < atlas_data.shape[1]) and (0 <= k < atlas_data.shape[2]):
            val = int(atlas_data[i, j, k])
            if val > 0 and val < len(aal.labels):
                found_label = aal.labels[val]
            elif val == 0:
                found_label = "WM/CSF"
        else:
            found_label = "Out of Bounds"
        aal_labels.append(found_label)
    return aal_labels

def clean_aal_label(label):
    clean = label.replace("_", " ")
    clean = re.sub(r'\s+[LlRr]$', '', clean) 
    return clean

def generate_display_labels(coords, aal_names):
    display_labels = []
    print("\n" + "="*50)
    print(f"{'INDEX':<6} {'AAL REGION':<25} {'COORDS (X,Y,Z)':<20}")
    print("="*50)
    
    for i, ((x, y, z), aal) in enumerate(zip(coords, aal_names)):
        clean_name = clean_aal_label(aal)
        coord_str = f"({int(x)}, {int(y)}, {int(z)})"
        label_text = f"{clean_name}\n{coord_str}"
        display_labels.append(label_text)
        print(f"{i+1:<6} {clean_name:<25} {coord_str:<20}")
        
    print("="*50 + "\n")
    return display_labels

# ===============================
# PLOTTING FUNCTIONS
# ===============================

def annotate_nodes_on_display(display, coords, display_labels):
    """
    Places text labels (AAL + Coords).
    """
    for ax_name, ax_wrapper in display.axes.items():
        ax = getattr(ax_wrapper, 'ax', ax_wrapper) 
        texts = [] 

        for i, ((x, y, z), label_text) in enumerate(zip(coords, display_labels)):
            px, py = 0, 0
            if ax_name in ['x', 'l', 'r']: # Sagittal
                px, py = y, z
            elif ax_name == 'y': # Coronal
                px, py = x, z
            elif ax_name == 'z': # Axial
                px, py = x, y
            else:
                continue 
            
            offset_y = 2.0 
            if not HAS_ADJUST_TEXT: offset_y += (i % 2) * 3 

            txt = ax.text(px, py + offset_y, label_text, 
                          fontsize=6, color='black', fontweight='bold', 
                          ha='center', va='bottom', zorder=1000)
            txt.set_path_effects([PathEffects.withStroke(linewidth=2.5, foreground='white')])
            texts.append(txt)

        if HAS_ADJUST_TEXT and texts:
            try:
                adjust_text(texts, ax=ax, 
                            arrowprops=dict(arrowstyle='-', color='gray', lw=0.5, zorder=999),
                            force_text=(0.3, 0.5), expand_points=(1.5, 1.5)) 
            except Exception: pass

def trace_roi_outlines(display, roi_entries, node_colors):
    """
    Overlays the actual contours of the ROI NIfTI files onto the connectome plot.
    """
    print("  Tracing ROI outlines...")
    for entry, color in zip(roi_entries, node_colors):
        try:
            # add_contours projects the 3D ROI onto the 2D glass brain axes
            display.add_contours(str(entry['path']), colors=[color], linewidths=1.5, levels=[0.5])
        except Exception as e:
            print(f"    [Warning] Failed to trace {entry['roi_name']}: {e}")

# ===============================
# MAIN MENU
# ===============================

def interactive_menu(group_avg_matrix, coords, node_colors, group_dir, task_name, display_labels, roi_entries):
    group_dir.mkdir(parents=True, exist_ok=True)
    
    while True:
        print("\n" + "="*40)
        print(f"   VISUALIZATION MENU: {task_name.upper()}")
        print("="*40)
        print("1. Static Connectome (Outlines + Labels)")
        print("2. Interactive 3D (HTML)")
        print("3. Correlation Matrix (Heatmap)")
        print("4. Exit")
        
        choice = input("\nSelect option [1-4]: ").strip()

        if choice == "1":
            # --- STATIC CONNECTOME ---
            view_map = {"1":"ortho", "2":"lzry", "3":"z"}
            v_choice = input("  > View (1=ortho, 2=panorama, 3=top) [1]: ").strip()
            display_mode = view_map.get(v_choice, "ortho")
            
            thresh_raw = input("  > Threshold [80%]: ").strip()
            colorbar_label = "Connection Strength"
            if not thresh_raw:
                threshold = "80%"
                title_str = "Top 20% Connections"
                colorbar_label = "Percentile Rank"
            elif "%" in thresh_raw:
                threshold = thresh_raw
                try:
                    val = float(thresh_raw.replace("%", ""))
                    title_str = f"Top {100-val:.0f}% Connections"
                    colorbar_label = "Percentile Rank"
                except: title_str = f"Threshold: {thresh_raw}"
            else:
                try:
                    val = float(thresh_raw)
                    threshold = val 
                    title_str = f"r > {val}"
                    if val < 1.0: colorbar_label = "Pearson's r"
                except ValueError:
                    threshold = "80%"
                    title_str = "Top 20% Connections"
                    colorbar_label = "Percentile Rank"

            size_raw = input("  > Node Size [30]: ").strip()
            node_size = float(size_raw) if size_raw else 30.0

            suffix = input(f"  > Filename suffix [{display_mode}]: ").strip()
            if not suffix: suffix = display_mode
            out_path = group_dir / f"group_{task_name}_{suffix}.png"
            
            print(f"  Generating {out_path}...")
            
            fig = plt.figure(figsize=(18, 10)) 
            display = plotting.plot_connectome(
                group_avg_matrix, node_coords=coords, edge_threshold=threshold,
                title=f"{task_name} ({title_str})", node_size=node_size,
                node_color=node_colors, 
                edge_cmap="jet", edge_vmin=-1.0, edge_vmax=1.0,
                display_mode=display_mode, colorbar=False, figure=fig
            )
            
            # 1. Trace Outlines (New Feature)
            trace_roi_outlines(display, roi_entries, node_colors)
            
            # 2. Add Text Labels
            annotate_nodes_on_display(display, coords, display_labels)

            cbar_ax = fig.add_axes([0.3, 0.05, 0.4, 0.02]) 
            norm = mcolors.Normalize(vmin=-1, vmax=1)
            sm = plt.cm.ScalarMappable(cmap="jet", norm=norm)
            sm.set_array([]) 
            cbar = fig.colorbar(sm, cax=cbar_ax, orientation='horizontal')
            cbar.set_ticks([-1, 0, 1])
            cbar.set_label(colorbar_label, labelpad=5)

            plt.savefig(out_path, dpi=300, bbox_inches='tight') 
            plt.close()
            print("  Done.")

        elif choice == "2":
            # --- INTERACTIVE HTML ---
            thresh_raw = input("  > Threshold [80%]: ").strip()
            if not thresh_raw: threshold = "80%"
            elif "%" in thresh_raw: threshold = thresh_raw
            else:
                try: threshold = float(thresh_raw) 
                except: threshold = "80%" 
            
            out_path = group_dir / f"group_{task_name}_interactive.html"
            print(f"  Generating {out_path}...")
            view = plotting.view_connectome(
                group_avg_matrix, coords, edge_threshold=threshold, 
                node_color=node_colors, node_size=6.0, symmetric_cmap=True,
                title=f"{task_name} 3D View"
            )
            view.save_as_html(out_path)
            print("  Done.")

        elif choice == "3":
            # --- HEATMAP ---
            out_path = group_dir / f"group_{task_name}_matrix.png"
            print(f"  Generating {out_path}...")
            
            fig = plt.figure(figsize=(14, 12))
            # Use spaces instead of newlines for axis labels
            matrix_labels = [l.replace("\n", " ") for l in display_labels]
            
            plotting.plot_matrix(
                group_avg_matrix, labels=matrix_labels, colorbar=True, 
                vmax=1.0, vmin=-1.0, title=f"Group Average {task_name}", figure=fig
            )
            plt.savefig(out_path, dpi=300) 
            plt.close()
            print("  Done.")

        elif choice == "4":
            print("Exiting.")
            break

# ===============================
# MAIN
# ===============================

if __name__ == "__main__":
    task_name = prompt_task()
    all_entries = get_nested_roi_entries(ROI_ROOT_DIR)
    available = list_available_roi_sets(all_entries)
    selected = prompt_roi_set_selection(available)
    roi_entries = filter_roi_entries_by_sets(all_entries, selected)
    
    # 1. Coordinates & Colors
    coords, labels, networks = get_roi_coordinates_from_entries(roi_entries)
    node_colors = [make_network_colors(networks)[n] for n in networks]
    
    # 2. Data Loading
    corr_stack = load_existing_matrices(task_name, labels)
    
    if corr_stack is None:
        print("Could not load matrices. Check ROI selection or Run processing.")
    else:
        # 3. Generate Labels
        aal_names = get_aal_labels_for_coords(coords)
        display_labels = generate_display_labels(coords, aal_names)

        group_avg = fisher_z_mean(corr_stack)
        GROUP_DIR = OUTPUT_ROOT / f"{task_name}_group"
        
        # 4. Interactive Menu
        interactive_menu(group_avg, coords, node_colors, GROUP_DIR, task_name, display_labels, roi_entries)