import gl

gl.resetdefaults()
gl.backcolor(255, 255, 255)  # Set dark background
height = 7 #darkest value, 
# Load MNI template
gl.loadimage('mni152')

# Load first contrast (jet, words)
gl.overlayload('/Users/neel/Desktop/SPM_Aug_2025/BIGRAMS/SPM-V_Lg10_plus1_BG_august_II/spmZ_0001_thr_p1e-12_k20vox.nii')  
gl.minmax(1, height, 8.126)  
gl.colorname(1, 'jet')  
gl.opacity(1, 100)  # Fully opaque


# Ensure the cross-slice view is OFF
gl.shaderadjust('crosshairs', 0)  # Disable crosshairs

# Turn off the colorbar
gl.colorbarposition(1)

# Generate mosaic (axial slices only, no cross-slice view)
gl.mosaic("A -18 -13 -8 -3 2")  # Axial-only, single row

# Save the mosaic
gl.savebmp("/Users/neel/Desktop/SPM_Aug_2025/BIGRAMS/renderings/bigrams_axial.png")

gl.resetdefaults()
gl.backcolor(0, 0, 0)  # Set dark background
height = 0.50 #darkest value, set to 50%
# Load MNI template
gl.loadimage('mni152')

# Load second contrast (jet, bigrams)
gl.overlayload('/Users/neel/Desktop/second_level/SPM-V_II_bigram/spmT_0001_peak-scaled.nii.gz')  
gl.minmax(1, height, 1)  
gl.colorname(1, 'jet')  
gl.opacity(1, 100)  # Fully opaque


# Ensure the cross-slice view is OFF
gl.shaderadjust('crosshairs', 0)  # Disable crosshairs

# Turn off the colorbar
gl.colorbarposition(0)

# Generate mosaic (axial slices only, no cross-slice view)
gl.mosaic("A -18 -13 -8 -3 2")  # Axial-only, single row

# Save the mosaic
gl.savebmp("/Users/neel/Desktop/second_level/visual_bigrams_axial.png")