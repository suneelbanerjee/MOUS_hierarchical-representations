import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as colors
from matplotlib import colormaps

# Set the master directory
master_dir = "/home/neel/Documents/SPM_results/second_level"

# Loop through all subdirectories
for subdir in os.listdir(master_dir):
    subdir_path = os.path.join(master_dir, subdir)
    if os.path.isdir(subdir_path):  # Ensure it's a directory
        # Paths to required files
        u_threshold_path = os.path.join(subdir_path, 'u_threshold.txt')
        cluster_centroids_path = os.path.join(subdir_path, 'cluster_centroids.csv')

        # Check if required files exist
        if os.path.exists(u_threshold_path) and os.path.exists(cluster_centroids_path):
            try:
                # Read minimum threshold from u_threshold.txt
                with open(u_threshold_path, 'r') as f:
                    min_threshold = float(f.readline().strip())

                # Read max threshold from cluster_centroids.csv
                with open(cluster_centroids_path, 'r') as f:
                    lines = f.readlines()
                    first_data_row = lines[1].strip().split(",")  # Read first data row (skip header)
                    peak_t_value = first_data_row[-2].strip()  # Second-to-last value
                    max_threshold = float(peak_t_value)  # Convert to float

                print(f"Generating colorbar for: {subdir_path}")
                print(f"Using thresholds: min={min_threshold}, max={max_threshold}")

                # Generate exactly 5 evenly spaced tick values
                tick_values = np.linspace(min_threshold, max_threshold, 5)

                # Create a narrow, elegant colormap
                fig, ax = plt.subplots(figsize=(0.6, 5))  # Slim width
                cmap = colormaps.get_cmap("jet")  # MRIcroGL's jet colormap
                norm = colors.Normalize(vmin=min_threshold, vmax=max_threshold)

                # Create colorbar
                cb = plt.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=cmap),
                                  cax=ax, orientation='vertical')

                # Apply 5 tick labels
                cb.set_ticks(tick_values)
                cb.set_ticklabels([f"{tick:.1f}" if tick % 1 else str(int(tick)) for tick in tick_values],fontsize=16)

                # cb.set_label("T-value", labelpad=-35)  # Reduce space between label and colorbar

                # Save colorbar
                colorbar_path = os.path.join(subdir_path, 'colorbar.png')
                plt.savefig(colorbar_path, dpi=300, bbox_inches='tight', transparent=False, pad_inches=0.05)
                plt.close()
                
                print(f"Saved colorbar: {colorbar_path}")

            except Exception as e:
                print(f"Error processing {subdir_path}: {str(e)}")