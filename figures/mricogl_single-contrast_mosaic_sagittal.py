import gl

gl.resetdefaults()
gl.backcolor(0, 0, 0)  # Set dark background
height = 0.70 #darkest value, set to 70%
# Load MNI template
gl.loadimage('mni152')

# Load contrast (jet)
gl.overlayload('/Users/neel/Desktop/second_level/SPM-A_II_multireg_test (FINAL)/spmT_0001_peak-scaled.nii.gz')  
gl.minmax(1, height, 1)  
gl.colorname(1, 'jet')  
gl.opacity(1, 100)  # Fully opaque


# Ensure the cross-slice view is OFF
gl.shaderadjust('crosshairs', 0)  # Disable crosshairs

# Turn off the colorbar
gl.colorbarposition(0)

# Generate mosaic (axial slices only, no cross-slice view)
gl.mosaic("S H -0.3 62 60 58 56 54 52")

# Save the mosaic
gl.savebmp("/Users/neel/Desktop/auditory_words_sagR.png")

gl.mosaic("Z H -0.3 -62 -60 -58 -56 -54 -52")  # Axial-only, single row")

gl.savebmp("/Users/neel/Desktop/auditory_words_sagL.png")