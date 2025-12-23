import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches  # Added for custom legends

import gc
import os
import shutil
from pathlib import Path
from collections import OrderedDict

import numpy as np
import pandas as pd

from nilearn import image, plotting
from nilearn.maskers import NiftiMasker
from nilearn.connectome import ConnectivityMeasure

# ===============================
# CONFIG
# ===============================

BASE_DIR = Path("/media/lillianchang/MOUSnew/fmriprep_fresh")
ROI_ROOT_DIR = Path("/home/lillianchang/Documents/MOUS_hierarchical-representations/figures/ROI_masks")
TR = 2.0


# ===============================
# TASK SELECTION
# ===============================

def prompt_task():
    while True:
        task = input("Analyze which task? Type 'auditory' or 'visual': ").strip().lower()
        if task in {"auditory", "visual"}:
            return task
        print("Invalid input. Please type exactly: auditory or visual.")


def task_config(task: str):
    if task == "auditory":
        return "sub-A2*", "auditory"
    if task == "visual":
        return "sub-V1*", "visual"
    raise ValueError(f"Unknown task: {task}")


# ===============================
# ROI DISCOVERY (NESTED) + SELECTION
# ===============================

def _normalize_network_name(rel_dir: Path) -> str:
    name = "_".join(rel_dir.parts) if rel_dir.parts else "roi"
    if not name.endswith("clusters"):
        name = f"{name}_clusters"
    return name


def get_nested_roi_entries(roi_root_dir: Path):
    roi_root_dir = Path(roi_root_dir)

    candidate_dirs = []
    for d in sorted([p for p in roi_root_dir.rglob("*") if p.is_dir()]):
        nii = list(d.glob("*.nii")) + list(d.glob("*.nii.gz"))
        if nii:
            candidate_dirs.append(d)

    if not candidate_dirs:
        raise FileNotFoundError(f"No ROI mask subdirectories found under {roi_root_dir}")

    entries = []
    for d in candidate_dirs:
        rel = d.relative_to(roi_root_dir)
        network = _normalize_network_name(rel)

        roi_paths = sorted(list(d.glob("*.nii")) + list(d.glob("*.nii.gz")))
        for rp in roi_paths:
            roi_name = rp.name.replace(".nii.gz", "").replace(".nii", "")
            roi_label = f"{network}:{roi_name}"
            entries.append({"network": network, "roi_name": roi_name, "roi_label": roi_label, "path": rp})

    entries = sorted(entries, key=lambda x: (x["network"], x["roi_name"]))
    networks = sorted(set(e["network"] for e in entries))
    print(f"Found {len(entries)} ROI masks across {len(networks)} ROI sets.")
    return entries


def list_available_roi_sets(roi_entries):
    nets = sorted(set(e["network"] for e in roi_entries))
    print("\nAvailable ROI sets:")
    for i, n in enumerate(nets, start=1):
        print(f"  [{i}] {n}")
    return nets


def prompt_roi_set_selection(available_sets):
    available_sets = list(available_sets)
    available_lc = {s.lower(): s for s in available_sets}

    while True:
        s = input("\nSelect ROI set(s) to use (type 'all' or e.g. '1,3' or names): ").strip()
        if not s:
            print("Empty input. Try again.")
            continue

        if s.lower() == "all":
            return set(available_sets)

        tokens = [t.strip() for t in s.split(",") if t.strip()]
        chosen = set()
        ok = True

        for t in tokens:
            if t.isdigit():
                idx = int(t)
                if 1 <= idx <= len(available_sets):
                    chosen.add(available_sets[idx - 1])
                else:
                    print(f"Index out of range: {t}")
                    ok = False
                    break
            else:
                key = t.lower()
                if key in available_lc:
                    chosen.add(available_lc[key])
                else:
                    print(f"Unknown ROI set name: {t}")
                    ok = False
                    break

        if ok and chosen:
            print(f"Using ROI set(s): {sorted(chosen)}")
            return chosen

        print("Invalid selection. Try again.")


def filter_roi_entries_by_sets(roi_entries, selected_sets):
    selected_sets = set(selected_sets)
    filtered = [e for e in roi_entries if e["network"] in selected_sets]
    if not filtered:
        raise ValueError("Selection yielded 0 ROI masks. Check ROI_ROOT_DIR contents and selection.")
    print(f"Selected {len(filtered)} ROI masks from {len(selected_sets)} ROI set(s).")
    return filtered


def get_roi_coordinates_from_entries(roi_entries):
    coords = []
    labels = []
    networks = []
    for e in roi_entries:
        roi_img = image.load_img(str(e["path"]))
        center = plotting.find_xyz_cut_coords(roi_img)
        coords.append(center)
        labels.append(e["roi_label"])
        networks.append(e["network"])
    return np.asarray(coords), labels, networks


# ===============================
# fMRIPrep confounds
# ===============================

def _safe_symlink(src: Path, dst: Path):
    src = Path(src)
    dst = Path(dst)
    if dst.exists() or dst.is_symlink():
        return
    try:
        rel_src = os.path.relpath(src, start=dst.parent)
        dst.symlink_to(rel_src)
    except Exception as e:
        print(f"Warning: symlink failed for {dst.name} ({e}). Copying instead.")
        shutil.copyfile(src, dst)


def ensure_confounds_timeseries(func_dir: Path, subject_label: str, task_name: str):
    func_dir = Path(func_dir)
    ts_tsv = func_dir / f"{subject_label}_task-{task_name}_desc-confounds_timeseries.tsv"
    ts_json = func_dir / f"{subject_label}_task-{task_name}_desc-confounds_timeseries.json"
    reg_tsv = func_dir / f"{subject_label}_task-{task_name}_desc-confounds_regressors.tsv"
    reg_json = func_dir / f"{subject_label}_task-{task_name}_desc-confounds_regressors.json"

    if (not ts_tsv.exists()) and reg_tsv.exists():
        _safe_symlink(reg_tsv, ts_tsv)
    if (not ts_json.exists()) and reg_json.exists():
        _safe_symlink(reg_json, ts_json)
    return ts_tsv if ts_tsv.exists() else None


def load_confounds_simple_with_censoring(confounds_tsv: Path, demean: bool = True):
    df = pd.read_csv(confounds_tsv, sep="\t", na_values=["n/a", "N/A"])
    keep_cols = ["trans_x", "trans_y", "trans_z", "rot_x", "rot_y", "rot_z", "white_matter", "csf"]
    available = [c for c in keep_cols if c in df.columns]
    
    if len(available) == 0:
        raise RuntimeError(f"No expected confound columns found in {confounds_tsv.name}")

    confounds = df[available].copy().fillna(0).astype("float32")
    if demean:
        confounds = confounds - confounds.mean(axis=0)

    outlier_cols = [c for c in df.columns if c.startswith("motion_outlier") or c.startswith("non_steady_state_outlier")]
    sample_mask = None
    if len(outlier_cols) > 0:
        out = df[outlier_cols].fillna(0).to_numpy(dtype=np.float32)
        keep = (out.sum(axis=1) == 0)
        sample_mask = np.where(keep)[0].astype(int)

    return confounds, sample_mask


# ===============================
# FILE FINDING & COLORING
# ===============================

def find_bold(subj_path: Path, subject_label: str, task_name: str):
    func_dir = subj_path / "func"
    bold_gz = func_dir / f"{subject_label}_task-{task_name}_space-MNI152NLin6Asym_res-2_desc-preproc_bold.nii.gz"
    bold_nii = func_dir / f"{subject_label}_task-{task_name}_space-MNI152NLin6Asym_res-2_desc-preproc_bold.nii"
    if bold_gz.exists(): return bold_gz
    if bold_nii.exists(): return bold_nii
    return None

def make_network_colors(network_names):
    network_names = list(OrderedDict.fromkeys(network_names))
    cycle = plt.rcParams.get("axes.prop_cycle", None)
    base_colors = cycle.by_key().get("color", []) if cycle else []
    net_to_color = {}
    if base_colors and len(network_names) <= len(base_colors):
        for n, c in zip(network_names, base_colors):
            net_to_color[n] = c
    else:
        cmap = plt.get_cmap("tab20")
        for i, n in enumerate(network_names):
            net_to_color[n] = cmap(i % 20)
    return net_to_color


# ===============================
# SUBJECT PIPELINE
# ===============================

def run_subject(subject_label, bold_file: Path, roi_entries, output_dir: Path, task_name: str):
    print(f"\n===== {subject_label} ({task_name}) =====")
    subj_dir = Path(output_dir) / subject_label
    subj_dir.mkdir(exist_ok=True, parents=True)

    func_dir = bold_file.parent
    conf_tsv = ensure_confounds_timeseries(func_dir, subject_label, task_name)
    if conf_tsv is None:
        print("ERROR: confounds TSV not found. Skipping.")
        return None

    try:
        confounds, sample_mask = load_confounds_simple_with_censoring(conf_tsv, demean=True)
    except Exception as e:
        print(f"ERROR: confounds loading failed: {e}")
        return None

    try:
        bold_img = image.load_img(str(bold_file))
        bold_img = image.index_img(bold_img, slice(None))
    except Exception as e:
        print(f"ERROR loading BOLD: {e}")
        return None

    roi_ts_list, roi_labels, roi_networks = [], [], []

    for entry in roi_entries:
        masker = NiftiMasker(mask_img=str(entry["path"]), standardize="zscore_sample", t_r=TR, verbose=0)
        try:
            ts = masker.fit_transform(bold_img, confounds=confounds, sample_mask=sample_mask)
            roi_ts_list.append(ts.mean(axis=1).astype("float32"))
            roi_labels.append(entry["roi_label"])
            roi_networks.append(entry["network"])
        except Exception as e:
            print(f"ERROR: ROI {entry['roi_label']} failed: {e}")
            return None

    roi_ts_mat = np.vstack(roi_ts_list).T
    corr = ConnectivityMeasure(kind="correlation", discard_diagonal=False).fit_transform([roi_ts_mat])[0]

    df_corr = pd.DataFrame(corr, index=roi_labels, columns=roi_labels)
    df_corr.to_csv(subj_dir / f"{subject_label}_correlation_matrix.csv")
    
    del bold_img, roi_ts_mat
    gc.collect()
    return corr


def fisher_z_mean(corr_stack: np.ndarray) -> np.ndarray:
    eps = 1e-7
    x = np.clip(corr_stack, -1 + eps, 1 - eps)
    z = np.arctanh(x)
    return np.tanh(np.mean(z, axis=0))


# ===============================
# NEW: INTERACTIVE PLOTTING MENU
# ===============================

def interactive_plotting_menu(group_avg_matrix, coords, labels, node_colors, roi_networks, group_dir, task_name):
    """
    Offers an interactive menu to save different visualizations with custom settings.
    """
    group_dir.mkdir(parents=True, exist_ok=True)
    
    # Save raw CSV first (always useful)
    out_csv = group_dir / f"group_average_{task_name}.csv"
    pd.DataFrame(group_avg_matrix, index=labels, columns=labels).to_csv(out_csv)
    print(f"\n[Auto] Saved group average CSV to: {out_csv}")

    # Prepare data for legend
    unique_nets = sorted(list(set(roi_networks)))
    # We need to find the color corresponding to each network name
    # Since node_colors aligns with roi_networks, we can zip them
    net_color_map = {}
    for n, c in zip(roi_networks, node_colors):
        net_color_map[n] = c

    while True:
        print("\n" + "="*40)
        print(f"   PLOTTING MENU: {task_name.upper()}")
        print("="*40)
        print("1. Plot Connectome (3D Brain View)")
        print("2. Plot Correlation Matrix (Heatmap)")
        print("3. Done / Exit")
        
        choice = input("\nSelect option [1-3]: ").strip()

        if choice == "1":
            # --- 1. CONNECTOME SETTINGS ---
            
            # A. Threshold
            thresh_raw = input("  > Enter edge threshold (e.g. '80%', '0.5', '98%'): ").strip()
            if not thresh_raw:
                thresh_raw = "80%" # default
            
            # Convert to float if user typed a number like 0.5
            try:
                if "%" not in thresh_raw:
                    threshold = float(thresh_raw)
                else:
                    threshold = thresh_raw
            except ValueError:
                print("    Invalid threshold. Using '80%'.")
                threshold = "80%"

            # B. Legend
            legend_input = input("  > Add network legend? (y/n) [n]: ").strip().lower()
            add_legend = (legend_input == 'y')

            # C. Filename
            suffix = input("  > Filename suffix (default 'connectome'): ").strip()
            if not suffix: suffix = "connectome"
            
            out_name = f"group_average_{task_name}_{suffix}.png"
            out_path = group_dir / out_name

            print(f"  ... Generating plot (Threshold: {threshold})...")

            # Create Figure
            fig = plt.figure(figsize=(12, 8))
            
            # Plot
            plotting.plot_connectome(
                group_avg_matrix,
                node_coords=coords,
                edge_threshold=threshold,
                title=f"{task_name} (thresh={threshold})",
                node_size=40,
                node_color=node_colors,
                colorbar=True,
                figure=fig
            )

            # Add Custom Legend if requested
            if add_legend:
                # Create patches for the legend
                legend_handles = []
                for net_name in unique_nets:
                    col = net_color_map[net_name]
                    # mpatches.Patch creates a colored rectangle
                    patch = mpatches.Patch(color=col, label=net_name)
                    legend_handles.append(patch)
                
                # Place legend. "loc" and "bbox_to_anchor" allow placement outside the brain
                plt.legend(
                    handles=legend_handles, 
                    title="Networks",
                    loc="upper left", 
                    bbox_to_anchor=(0, 1),
                    fontsize='small'
                )

            plt.savefig(out_path)
            plt.close()
            print(f"  [Saved] {out_path}")

        elif choice == "2":
            # --- 2. MATRIX SETTINGS ---
            suffix = input("  > Filename suffix (default 'matrix'): ").strip()
            if not suffix: suffix = "matrix"
            out_path = group_dir / f"group_average_{task_name}_{suffix}.png"

            plt.figure(figsize=(10, 8))
            plotting.plot_matrix(
                group_avg_matrix,
                labels=labels,
                colorbar=True,
                vmax=1.0,
                vmin=-1.0,
                title=f"Group Average {task_name} FC",
            )
            plt.savefig(out_path)
            plt.close()
            print(f"  [Saved] {out_path}")

        elif choice == "3":
            print("Exiting.")
            break
        
        else:
            print("Invalid choice. Try again.")


# ===============================
# DRIVER
# ===============================

if __name__ == "__main__":

    task = prompt_task()
    subject_glob, task_name = task_config(task)

    OUTPUT_ROOT = Path("./results")
    SUBJECT_OUTPUT_DIR = OUTPUT_ROOT / task_name
    GROUP_DIR = OUTPUT_ROOT / f"{task_name}_group"
    SUBJECT_OUTPUT_DIR.mkdir(exist_ok=True, parents=True)

    all_roi_entries = get_nested_roi_entries(ROI_ROOT_DIR)
    available_sets = list_available_roi_sets(all_roi_entries)
    selected_sets = prompt_roi_set_selection(available_sets)
    roi_entries = filter_roi_entries_by_sets(all_roi_entries, selected_sets)

    coords, labels, roi_networks = get_roi_coordinates_from_entries(roi_entries)
    net_to_color = make_network_colors(roi_networks)
    node_colors = [net_to_color[nm] for nm in roi_networks]

    subjects = sorted([p for p in BASE_DIR.glob(subject_glob) if p.is_dir()])
    print(f"\nFound {len(subjects)} subjects for task='{task_name}'")

    corr_mats = []
    
    for subj_path in subjects:
        subject_label = subj_path.name
        bold_file = find_bold(subj_path, subject_label, task_name)
        
        if bold_file is None:
            print(f"Missing BOLD for {subject_label} — skipped.")
            continue

        corr = run_subject(subject_label, bold_file, roi_entries, SUBJECT_OUTPUT_DIR, task_name)
        if corr is not None:
            corr_mats.append(corr)

    if not corr_mats:
        raise RuntimeError("No subjects processed.")

    print("\nComputing group average...")
    corr_stack = np.stack(corr_mats, axis=0)
    group_avg_matrix = fisher_z_mean(corr_stack)

    # Call the new interactive menu instead of the static save function
    interactive_plotting_menu(
        group_avg_matrix=group_avg_matrix,
        coords=coords,
        labels=labels,
        node_colors=node_colors,
        roi_networks=roi_networks,
        group_dir=GROUP_DIR,
        task_name=task_name,
    )