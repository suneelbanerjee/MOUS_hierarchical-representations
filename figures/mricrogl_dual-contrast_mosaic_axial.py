import gl

gl.resetdefaults()
gl.backcolor(0, 0, 0)  # Set dark background
height = 0.50 #darkest value, set to 50%
# Load MNI template
gl.loadimage('mni152')

# Load first contrast (red, words)
gl.overlayload('/Users/neel/Desktop/second_level/SPM-V_II/spmT_0001_Ke_20_peak-scaled.nii.gz')  
gl.minmax(1, height, 1)  
gl.colorname(1, '1red')  
gl.opacity(1, 100)  # Fully opaque
gl.colorfromzero(1, 1)  # Set color range to start from zero for the first overlay


# Load second contrast (blue, sublexical)
gl.overlayload('/Users/neel/Desktop/second_level/SPM-V_II_bigram/spmT_0001_Ke_20_peak-scaled.nii.gz')  
gl.minmax(2, height, 1)  
gl.colorname(2, '7cool')  
gl.opacity(2, 100)  # Fully opaque
gl.colorfromzero(2, 1)  # Set color range to start from zero for the first overlay

# Ensure the cross-slice view is OFF
gl.shaderadjust('crosshairs', 0)  # Disable crosshairs

# Turn off the colorbar
gl.colorbarposition(0)

# Generate mosaic (axial slices only, no cross-slice view)
gl.mosaic("A -18 -13 -8 -3 2")  # Axial-only, single row

#set the colormap range to start fro
# Save the mosaic
gl.savebmp("/Users/neel/Desktop/second_level/visual_dual_contrast.png")