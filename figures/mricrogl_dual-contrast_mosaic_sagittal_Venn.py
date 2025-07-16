import gl

gl.resetdefaults()
gl.backcolor(0, 0, 0)  # Set dark background
height = 0.70 #darkest value, set to 70%
# Load MNI template
gl.loadimage('mni152')

# Load first contrast (sublexical, blue)
gl.overlayload('/Users/neel/Desktop/second_level/SPM-A_II_syllables_IPA_eSpeak_ijfix2/spmT_0001_Ke_20_peak-scaled.nii.gz')  
gl.minmax(1, height, 1)  
gl.colorname(1, '7cool')  
gl.opacity(1, 100)  # Fully opaque
gl.colorfromzero(1, 1)  # Set color range to start from zero for the first overlay


# Load second contrast (lexical, red
gl.overlayload('/Users/neel/Desktop/second_level/SPM-A_II/spmT_0001_Ke_20_peak-scaled.nii.gz')  
gl.minmax(2, height, 1)  
gl.colorname(2, '1red')  
gl.opacity(2, 100)  # Fully opaque

# Load intersection mask (binary)
gl.overlayload('/Users/neel/Desktop/intersection_masks/syllable_word_intersection.nii.gz')
gl.colorname(3, 'Plasma')     # Set a distinct color
gl.opacity(3, 100)             # Fully opaque
gl.minmax(3, 0.5, 1)           # Binary mask range for visibility
gl.colorfromzero(3, 0)         # Don't shift colormap for binary mask


# Ensure the cross-slice view is OFF
gl.shaderadjust('crosshairs', 0)  # Disable crosshairs

# Turn off the colorbar
gl.colorbarposition(0)

# Generate mosaic (axial slices only, no cross-slice view)
gl.mosaic("S H -0.3 62 60 58 56 54 52")

# Save the mosaic
gl.savebmp("/Users/neel/Desktop/second_level/mosaic_dual_contrast_sagR.png")

gl.mosaic("Z H -0.3 -62 -60 -58 -56 -54 -52")  # Axial-only, single row")

gl.savebmp("/Users/neel/Desktop/second_level/mosaic_dual_contrast_sagL.png")