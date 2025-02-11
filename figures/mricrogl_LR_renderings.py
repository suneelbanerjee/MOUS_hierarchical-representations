import gl
import os

# Set the master directory
master_dir = "/Users/neel/Desktop/second_level"

# Loop through all subdirectories
for subdir in os.listdir(master_dir):
    subdir_path = os.path.join(master_dir, subdir)
    if os.path.isdir(subdir_path):  # Ensure it's a directory
        # Paths to left and right hemisphere T-maps
        left_nii_path = os.path.join(subdir_path, 'spmT_0001_left.nii.gz')
        right_nii_path = os.path.join(subdir_path, 'spmT_0001_right.nii.gz')
        u_threshold_path = os.path.join(subdir_path, 'u_threshold.txt')
        cluster_centroids_path = os.path.join(subdir_path, 'cluster_centroids.csv')

        # Print debugging info
        print(f"Processing: {subdir_path}")
        print(f"Checking {left_nii_path}: {'Exists' if os.path.exists(left_nii_path) else 'MISSING'}")
        print(f"Checking {right_nii_path}: {'Exists' if os.path.exists(right_nii_path) else 'MISSING'}")
        print(f"Checking {u_threshold_path}: {'Exists' if os.path.exists(u_threshold_path) else 'MISSING'}")
        print(f"Checking {cluster_centroids_path}: {'Exists' if os.path.exists(cluster_centroids_path) else 'MISSING'}")

        # Check that all required files exist
        if os.path.exists(left_nii_path) and os.path.exists(right_nii_path) and os.path.exists(u_threshold_path) and os.path.exists(cluster_centroids_path):

            # Read minimum threshold from u_threshold.txt
            with open(u_threshold_path, 'r') as f:
                min_threshold = float(f.readline().strip())

            # Read Peak T-value (value between last and penultimate comma) from cluster_centroids.csv
            with open(cluster_centroids_path, 'r') as f:
                lines = f.readlines()
                first_data_row = lines[1].strip().split(",")  # Read first data row (skip header)

                # Extract Peak T-value dynamically (between last and penultimate commas)
                peak_t_value = first_data_row[-2].strip()  # Second-to-last value
                max_threshold = float(peak_t_value)  # Convert to float

            print(f"Using thresholds: min={min_threshold}, max={max_threshold}")

            # ---- Left Hemisphere ----
            gl.resetdefaults()
            gl.loadimage('mni152')  # Load default MNI152 template
            gl.overlayload(left_nii_path)  # Load the left hemisphere T-map

            # Set colormap and thresholds
            gl.colorname(1, 'jet')  # Set jet colormap
            gl.minmax(1, min_threshold, max_threshold)  # Set intensity range
            gl.backcolor(255, 255, 255)  # Set white background
            gl.shaderadjust('overlayDepth', 10)

            # Set colorbar settings
            gl.colorbarposition(1)  # Ensure the colorbar is visible
            gl.colorbarcolor(255, 255, 255, 255)  # Set colorbar background to white

            # Save Left Hemisphere View
            gl.azimuthelevation(90, 0)  # Left view
            left_view_path = os.path.join(subdir_path, 'left_tmap_view.png')
            gl.savebmp(left_view_path)
            print(f"Saved Left Hemisphere View: {left_view_path}")

            # ---- Right Hemisphere ----
            gl.resetdefaults()
            gl.loadimage('mni152')  # Load default MNI152 template
            gl.overlayload(right_nii_path)  # Load the right hemisphere T-map

            # Set colormap and thresholds
            gl.colorname(1, 'jet')  # Set jet colormap
            gl.minmax(1, min_threshold, max_threshold)  # Set intensity range
            gl.backcolor(255, 255, 255)  # Set white background
            gl.shaderadjust('overlayDepth', 10)

            # Set colorbar settings
            gl.colorbarposition(1)  # Ensure the colorbar is visible
            gl.colorbarcolor(255, 255, 255, 255)  # Set colorbar background to white

            # Save Right Hemisphere View
            gl.azimuthelevation(270, 0)  # Right view
            right_view_path = os.path.join(subdir_path, 'right_tmap_view.png')
            gl.savebmp(right_view_path)
            print(f"Saved Right Hemisphere View: {right_view_path}")