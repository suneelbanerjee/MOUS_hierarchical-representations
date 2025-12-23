import matplotlib
matplotlib.use("Agg") 
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.colors as mcolors 

import numpy as np
import pandas as pd
import re
import json
import time
from pathlib import Path
from nilearn import image, plotting
from collections import OrderedDict

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
    if not name.endswith("clusters"): name = f"{name}_clusters"
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
    print("\nAvailable ROI sets:")
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
# DATA LOADING (FIXED SUBSETTING)
# ===============================

def load_existing_matrices(task_name, target_labels):
    """
    Loads CSVs and filters them to match the target_labels.
    Allows visualizing a subset of ROIs even if the file contains more.
    """
    task_dir = OUTPUT_ROOT / task_name
    if not task_dir.exists():
        raise FileNotFoundError(f"No results found at {task_dir}. Run the processing script first.")
        
    matrices = []
    subjects = sorted([d for d in task_dir.iterdir() if d.is_dir()])
    print(f"\nLooking for existing CSVs in {task_dir}...")
    
    # Pre-check target labels exist
    target_set = set(target_labels)
    
    for subj_dir in subjects:
        subj_label = subj_dir.name
        csv_path = subj_dir / f"{subj_label}_correlation_matrix.csv"
        
        if csv_path.exists():
            # Load full matrix
            df = pd.read_csv(csv_path, index_col=0)
            
            # CHECK: Do we have all the ROIs we need?
            missing = [l for l in target_labels if l not in df.index]
            
            if missing:
                # If missing, we can't use this subject (or the matrix is wrong)
                print(f"  [Skip] {subj_label}: Missing ROIs {missing[:3]}...")
                continue
            
            # SUBSET: Keep only the rows/cols the user asked for
            df_subset = df.loc[target_labels, target_labels]
            matrices.append(df_subset.values)

    print(f"Loaded {len(matrices)} matrices.")
    return np.array(matrices) if matrices else None

def load_roi_metadata(roi_entries):
    metadata_map = {}
    dir_to_rois = {}
    for entry in roi_entries:
        parent = entry["path"].parent
        if parent not in dir_to_rois: dir_to_rois[parent] = []
        dir_to_rois[parent].append(entry)
    for folder, entries in dir_to_rois.items():
        csv_path = folder / "cluster_centroids.csv"
        if csv_path.exists():
            try:
                df = pd.read_csv(csv_path)
                df.columns = [c.strip() for c in df.columns]
                if "Cluster #" in df.columns and "Centroid" in df.columns and "Extent" in df.columns:
                    for entry in entries:
                        match = re.search(r'(\d+)', entry["roi_name"])
                        if match:
                            c_num = int(match.group(1))
                            row = df[df["Cluster #"] == c_num]
                            if not row.empty:
                                c_str = str(row.iloc[0]["Centroid"]).replace('"', '').strip()
                                e_str = str(row.iloc[0]["Extent"]).strip()
                                metadata_map[entry["roi_label"]] = {"centroid": c_str, "extent": e_str}
            except Exception as e:
                print(f"  [Warning] Metadata read error {csv_path.name}: {e}")
    return metadata_map

# ===============================
# HTML INJECTION
# ===============================

def inject_html_extras(html_path, net_color_map, display_names, final_node_labels):
    """
    Injects:
      1) The Network Legend (Top Left)
      2) JS to update Tooltips (Hover Text)
    """
    
    # --- 1. LEGEND ---
    legend_items = []
    for net, color in net_color_map.items():
        hex_color = mcolors.to_hex(color)
        clean_name = display_names.get(net, net)
        item_html = f"""
        <div style="margin-bottom: 5px; display: flex; align-items: center;">
            <span style="display:inline-block; width:15px; height:15px; background-color:{hex_color}; margin-right:8px; border-radius:3px;"></span>
            <span style="font-family: sans-serif; font-size: 14px; color: #333;">{clean_name}</span>
        </div>"""
        legend_items.append(item_html)

    legend_div = f"""
    <div style="position: absolute; top: 20px; left: 20px; z-index: 1000; background: rgba(255, 255, 255, 0.95); padding: 15px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.2); pointer-events: none;">
        <h4 style="margin-top:0; margin-bottom:10px; font-family: sans-serif; color: #333;">Networks</h4>
        {''.join(legend_items)}
    </div>"""

    # --- 2. TOOLTIP JS ---
    labels_json = json.dumps(final_node_labels)
    
    js_script = f"""
    <script>
    (function() {{
        var attempts = 0;
        var maxAttempts = 50; 
        
        var checkExist = setInterval(function() {{
            var graphs = document.getElementsByClassName("plotly-graph-div");
            
            if (graphs.length > 0 && window.Plotly) {{
                var gd = graphs[0];
                if (gd.data && gd.data.length > 0) {{
                    clearInterval(checkExist);
                    console.log("Found Plotly graph! Updating tooltips...");

                    var customLabels = {labels_json};
                    
                    var nodeTraceIndex = -1;
                    for (var i = 0; i < gd.data.length; i++) {{
                        // Nodes are 'markers' (scatter3d)
                        if (gd.data[i].mode && gd.data[i].mode.indexOf('markers') !== -1) {{
                            nodeTraceIndex = i;
                            break;
                        }}
                    }}

                    if (nodeTraceIndex !== -1) {{
                        var update = {{
                            "text": customLabels,      // The text to show
                            "hoverinfo": "text"        // Force it to show ONLY this text on hover
                        }};
                        
                        Plotly.restyle(gd, update, [nodeTraceIndex]);
                        console.log("Tooltips updated.");
                    }}
                }}
            }}
            attempts++;
            if (attempts > maxAttempts) clearInterval(checkExist);
        }}, 200);
    }})();
    </script>
    """

    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    if "<body>" in content:
        content = content.replace("<body>", f"<body>\n{legend_div}")
    else:
        content = legend_div + content

    if "</body>" in content:
        content = content.replace("</body>", f"{js_script}\n</body>")
    else:
        content = content + js_script

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    print("  [Auto] Injected Legend & Custom Tooltips.")


# ===============================
# INTERACTIVE MENU
# ===============================

def interactive_plotting_menu(group_avg_matrix, coords, labels, node_colors, roi_networks, group_dir, task_name, metadata):
    group_dir.mkdir(parents=True, exist_ok=True)
    
    unique_nets = sorted(list(set(roi_networks)))
    net_color_map = {n: c for n, c in zip(roi_networks, node_colors)}
    
    # 1. Network Renaming
    print("\n" + "="*40)
    print("   1. NETWORK LABELS")
    print("="*40)
    display_names = {n: n for n in unique_nets}
    if input("Rename Network categories? (y/n) [n]: ").strip().lower() == 'y':
        for net in unique_nets:
            new_name = input(f"  {net} -> ").strip()
            if new_name: display_names[net] = new_name

    # 2. Region/Coordinate Renaming
    print("\n" + "="*40)
    print("   2. REGION LABELS (Tooltip Names)")
    print("="*40)
    
    final_node_labels = []
    do_rename_regions = input("Review coordinates and assign custom Region names? (y/n) [y]: ").strip().lower()
    
    if do_rename_regions not in ['n', 'no']:
        print("\n(Press Enter to keep original name)")
        for i, (orig_label, net) in enumerate(zip(labels, roi_networks)):
            meta = metadata.get(orig_label)
            meta_str = f" | {meta['centroid']}" if meta else ""
            print(f"  [{i+1}] {orig_label}{meta_str}")
            new_label = input(f"      -> Name: ").strip()
            
            if new_label:
                final_node_labels.append(new_label)
            else:
                final_node_labels.append(orig_label.split(":")[-1])
    else:
        final_node_labels = [l.split(":")[-1] for l in labels]


    # 3. Main Menu
    while True:
        print("\n" + "="*40)
        print(f"   VISUALIZATION MENU: {task_name.upper()}")
        print("="*40)
        print("1. Static Connectome")
        print("2. Interactive 3D (HTML)")
        print("3. Correlation Matrix")
        print("4. Exit")
        
        choice = input("\nSelect option [1-4]: ").strip()

        if choice == "1":
            # --- STATIC PLOT ---
            view_map = {"1":"ortho", "2":"lzry", "3":"z"}
            v_choice = input("  > View (1=ortho, 2=panorama, 3=top) [1]: ").strip()
            display_mode = view_map.get(v_choice, "ortho")
            
            thresh_raw = input("  > Threshold [80%]: ").strip()
            if not thresh_raw:
                threshold = "80%"; title_str = "Top 20% Connections"
            elif "%" in thresh_raw:
                threshold = thresh_raw; title_str = f"Threshold: {thresh_raw}"
            else:
                try: threshold = float(thresh_raw); title_str = f"r > {threshold}"
                except: threshold = "80%"; title_str = "Top 20% Connections"

            size_raw = input("  > Node Size [50]: ").strip()
            node_size = float(size_raw) if size_raw else 50.0

            suffix = input(f"  > Filename suffix [{display_mode}]: ").strip()
            if not suffix: suffix = display_mode
            
            out_path = group_dir / f"group_{task_name}_{suffix}.png"
            print(f"  Generating {out_path}...")

            fig = plt.figure(figsize=(14, 10))
            plotting.plot_connectome(
                group_avg_matrix, 
                node_coords=coords, 
                edge_threshold=threshold,
                title=f"{task_name} ({title_str})", 
                node_size=node_size,
                node_color=node_colors, 
                edge_cmap="RdBu_r", 
                edge_vmin=-1.0, edge_vmax=1.0,
                display_mode=display_mode, 
                colorbar=False,
                figure=fig
            )

            cbar_ax = fig.add_axes([0.92, 0.3, 0.015, 0.4]) 
            norm = mcolors.Normalize(vmin=-1, vmax=1)
            sm = plt.cm.ScalarMappable(cmap="RdBu_r", norm=norm)
            sm.set_array([]) 
            cbar = fig.colorbar(sm, cax=cbar_ax)
            cbar.set_ticks([-1, -0.5, 0, 0.5, 1]) 
            cbar.ax.tick_params(labelsize=10)
            cbar.set_label('Correlation (r)', rotation=270, labelpad=15)

            legend_handles = [mpatches.Patch(color=net_color_map[n], label=display_names[n]) for n in unique_nets]
            fig.legend(handles=legend_handles, title="ROI Networks", loc="upper left", bbox_to_anchor=(0.05, 0.85), fontsize='medium', frameon=True)

            plt.savefig(out_path, dpi=300) 
            plt.close()
            print("  Done.")

        elif choice == "2":
            # --- INTERACTIVE 3D HTML ---
            print("\n  [Info] Creating interactive HTML...")
            thresh_raw = input("  > Threshold [80%]: ").strip()
            threshold = thresh_raw if thresh_raw else "80%"
            
            size_raw = input("  > Node Size [5]: ").strip()
            node_size = float(size_raw) if size_raw else 5.0
            
            suffix = input("  > Filename suffix [interactive]: ").strip()
            if not suffix: suffix = "interactive"
            out_path = group_dir / f"group_{task_name}_{suffix}.html"

            view = plotting.view_connectome(
                group_avg_matrix, 
                coords, 
                edge_threshold=threshold, 
                node_color=node_colors,
                node_size=node_size,
                symmetric_cmap=True,
                title=f"{task_name} 3D View"
            )
            view.save_as_html(out_path)
            
            inject_html_extras(out_path, net_color_map, display_names, final_node_labels)
            
            print(f"  Saved: {out_path}")

        elif choice == "3":
            # --- MATRIX ---
            suffix = input("  > Filename suffix [matrix]: ").strip()
            if not suffix: suffix = "matrix"
            out_path = group_dir / f"group_{task_name}_{suffix}.png"
            
            fig = plt.figure(figsize=(12, 10))
            plotting.plot_matrix(
                group_avg_matrix, 
                labels=final_node_labels,
                colorbar=True, vmax=1.0, vmin=-1.0,
                title=f"Group Average {task_name}",
                figure=fig
            )
            plt.savefig(out_path, dpi=300) 
            plt.close()
            print(f"  Saved {out_path}")

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
    
    # 1. Load basic info
    coords, labels, networks = get_roi_coordinates_from_entries(roi_entries)
    node_colors = [make_network_colors(networks)[n] for n in networks]
    
    # 2. Load Metadata
    print("Loading ROI metadata...")
    metadata = load_roi_metadata(roi_entries)

    # 3. Load Data
    corr_stack = load_existing_matrices(task_name, labels)
    
    if corr_stack is None:
        print("Could not load matrices. (Try re-running with correct ROIs?)")
    else:
        group_avg = fisher_z_mean(corr_stack)
        GROUP_DIR = OUTPUT_ROOT / f"{task_name}_group"
        interactive_plotting_menu(group_avg, coords, labels, node_colors, networks, GROUP_DIR, task_name, metadata)