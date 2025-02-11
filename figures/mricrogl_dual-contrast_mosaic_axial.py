import gl

gl.resetdefaults()
gl.backcolor(0, 0, 0)  # Set dark background

# Load MNI template
gl.loadimage('mni152')

# Load first contrast (red)
gl.overlayload('/Users/neel/Desktop/second_level/SPM-A_II_syllables_IPA_eSpeak_ijfix2/spmT_0001_peak-scaled.nii.gz')  
gl.minmax(1, 0.7, 1)  
gl.colorname(1, '1red')  
gl.opacity(1, 100)  # Fully opaque

# Load second contrast (blue)
gl.overlayload('/Users/neel/Desktop/second_level/SPM-A_II_multireg_test (FINAL)/spmT_0001_peak-scaled.nii.gz')  
gl.minmax(2, 0.7, 1)  
gl.colorname(2, '3blue')  
gl.opacity(2, 100)  # Fully opaque

# Ensure the cross-slice view is OFF
gl.shaderadjust('crosshairs', 0)  # Disable crosshairs

# Turn off the colorbar
gl.colorbarposition(0)

# Generate mosaic (axial slices only, no cross-slice view)
gl.mosaic("A -24 -16 -8 0 8 16 24 32 40 48 56;")  # Axial-only, single row

# Save the mosaic
gl.savebmp("/Users/neel/Desktop/mosaic_dual_contrast.png")