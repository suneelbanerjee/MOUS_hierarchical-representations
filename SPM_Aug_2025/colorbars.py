#!/usr/bin/env python3
# make_vertical_colorbar.py
import re, argparse, os, sys
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw
import nibabel as nib
import matplotlib.ticker as mticker

def read_first_float_from_text(path):
    if not os.path.isfile(path):
        raise FileNotFoundError(f"u-threshold file not found: {path}")
    with open(path, "r") as f:
        txt = "\n".join(ln for ln in f if not ln.strip().startswith(("#", "%")))
    m = re.search(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", txt)
    if not m:
        raise ValueError(f"No numeric value found in {path}")
    return float(m.group(0))

def nifti_max(path):
    if not os.path.isfile(path):
        raise FileNotFoundError(f"NIfTI not found: {path}")
    data = nib.load(path).get_fdata(dtype=np.float64)
    finite = np.isfinite(data)
    if not np.any(finite):
        raise ValueError("No finite voxels in NIfTI.")
    return float(np.max(data[finite]))

def save_vertical_colorbar(vmin, vmax, outfile, height_px=800, n=256, ticks=5,
                           label=None, label_side="right", label_offset=0.22, dpi=300):
    if vmax <= vmin:
        vmax = vmin + 1e-6
    fig_h_in = height_px / dpi
    fig = plt.figure(figsize=(1.2, fig_h_in), dpi=dpi)
    ax = fig.add_axes([0.35, 0.05, 0.30, 0.90])

    cmap = mpl.cm.get_cmap("jet", n)
    norm = mpl.colors.Normalize(vmin=vmin, vmax=vmax)
    cb = mpl.colorbar.ColorbarBase(ax, cmap=cmap, norm=norm, orientation="vertical")

    # Keep tick numbers horizontal
    cb.ax.tick_params(axis='y', which='both', labelrotation=0,labelsize=14)

    # Custom ticks (if requested)
    if isinstance(ticks, int) and ticks > 1:
        cb.set_ticks(np.linspace(vmin, vmax, ticks))

    # >>> Format to two decimals (use the colorbar's own formatter) <<<
    cb.formatter = mticker.FormatStrFormatter('%.2f')
    cb.update_ticks()

    # Optional horizontal label placed beside the bar
    if label:
        side = "right" if str(label_side).lower().startswith("r") else "left"
        cb.ax.set_ylabel(label, rotation=0, labelpad=10)
        cb.ax.yaxis.set_label_position(side)
        x = 1.0 + float(label_offset) if side == "right" else -float(label_offset)
        cb.ax.yaxis.set_label_coords(x, 0.5)

    fig.savefig(outfile, dpi=dpi, bbox_inches="tight")
    plt.close(fig)

def stitch_right(mosaic_path, bar_path, out_path, bar_rel_width=0.06, pad_px=24, bg=(255, 255, 255)):
    base = Image.open(mosaic_path).convert("RGB")
    bar  = Image.open(bar_path).convert("RGB")
    H = base.height
    bar_w = max(60, int(base.width * bar_rel_width))
    bar = bar.resize((bar_w, H), Image.LANCZOS)

    canvas = Image.new("RGB", (base.width + pad_px + bar_w, H), bg)
    canvas.paste(base, (0, 0))
    ImageDraw.Draw(canvas).line([(base.width + pad_px // 2, 0), (base.width + pad_px // 2, H)],
                                fill=(200, 200, 200), width=1)
    canvas.paste(bar, (base.width + pad_px, 0))
    canvas.save(out_path)

def main():
    ap = argparse.ArgumentParser(description="Vertical jet colorbar with horizontal label; vmin from u_threshold.txt, vmax from NIfTI max.")
    ap.add_argument("--uthresh", required=True, help="Path to u_threshold.txt (lower bound).")
    ap.add_argument("--tmap", required=True, help="Path to T-map NIfTI (upper bound from its max).")
    ap.add_argument("--mosaic", default=None, help="Optional MRIcroGL mosaic PNG to stitch onto.")
    ap.add_argument("--out", default=None, help="Output PNG when stitching (requires --mosaic).")
    ap.add_argument("--bar-out", default=None, help="Also save the colorbar alone to this file.")
    ap.add_argument("--label", default="", help="Colorbar label text (leave empty to hide).")
    ap.add_argument("--label-side", default="right", choices=["right", "left"], help="Place label on right or left of bar.")
    ap.add_argument("--label-offset", type=float, default=0.22, help="Offset from bar spine (axes fraction).")
    ap.add_argument("--ticks", type=int, default=5, help="Number of tick marks (>1).")
    ap.add_argument("--height", type=int, default=None, help="Bar height in pixels (default = mosaic height or 800).")
    ap.add_argument("--bar-rel-width", type=float, default=0.06, help="Relative bar width when stitching.")
    ap.add_argument("--pad", type=int, default=24, help="Padding between mosaic and bar when stitching.")
    args = ap.parse_args()

    try:
        vmin = read_first_float_from_text(args.uthresh)
        vmax = nifti_max(args.tmap)
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr); sys.exit(1)
    if vmax <= vmin:
        vmax = vmin + 1e-6

    height_px = args.height
    if height_px is None and args.mosaic and os.path.isfile(args.mosaic):
        try:
            height_px = Image.open(args.mosaic).height
        except Exception:
            height_px = 800
    if height_px is None:
        height_px = 800

    tmp_bar = None
    if args.mosaic:
        tmp_bar = (os.path.splitext(args.out or "bar_tmp.png")[0] + "_bar_tmp.png")
        save_vertical_colorbar(vmin, vmax, tmp_bar, height_px=height_px, ticks=args.ticks,
                               label=args.label, label_side=args.label_side, label_offset=args.label_offset)

    if args.bar_out:
        save_vertical_colorbar(vmin, vmax, args.bar_out, height_px=height_px, ticks=args.ticks,
                               label=args.label, label_side=args.label_side, label_offset=args.label_offset)
        print(f"[OK] Saved standalone colorbar: {args.bar_out}")

    if args.mosaic:
        if not args.out:
            print("[ERROR] --out is required when using --mosaic", file=sys.stderr); sys.exit(2)
        if not os.path.isfile(args.mosaic):
            print(f"[ERROR] Mosaic not found: {args.mosaic}", file=sys.stderr); sys.exit(2)
        stitch_right(args.mosaic, tmp_bar, args.out, bar_rel_width=args.bar_rel_width, pad_px=args.pad)
        try:
            os.remove(tmp_bar)
        except Exception:
            pass
        print(f"[OK] Saved stitched mosaic: {args.out}")

    if not args.mosaic and not args.bar_out:
        print(f"vmin = {vmin}, vmax = {vmax} (no outputs requested)")

if __name__ == "__main__":
    main()