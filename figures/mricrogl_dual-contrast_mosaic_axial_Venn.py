import gl

gl.resetdefaults()
gl.backcolor(255, 255, 255)  # Set dark background
height = 7  # darkest value, set to 50%

# Load MNI template
gl.loadimage('mni152')

# Load first contrast (red, words)
gl.overlayload('/Users/neel/Desktop/SPM_Aug_2025/VISUAL/SPM-V_II/spmZ_0001_thr_p1e-12_k20vox.nii')
gl.minmax(1, height, 1)
gl.colorname(1, '1red')
gl.opacity(1, 100)
gl.colorfromzero(1, 1)

# Load second contrast (blue, sublexical)
gl.overlayload('/Users/neel/Desktop/SPM_Aug_2025/BIGRAMS/SPM-V_Lg10_plus1_BG_august_II/spmZ_0001_thr_p1e-12_k20vox.nii')
gl.minmax(2, height, 1)
gl.colorname(2, '7cool')
gl.opacity(2, 100)
gl.colorfromzero(2, 1)

# Load intersection mask (binary)
gl.overlayload('/Users/neel/Desktop/SPM_Aug_2025/intersection_masks/bigram_word_intersection.nii.gz')
gl.colorname(3, 'Plasma')     # Set a distinct color
gl.opacity(3, 100)             # Fully opaque
gl.minmax(3, 0.5, 1)           # Binary mask range for visibility
gl.colorfromzero(3, 0)         # Don't shift colormap for binary mask

# Hide cross-slice view and colorbar
gl.shaderadjust('crosshairs', 0)
gl.colorbarposition(0)

# Generate mosaic (axial slices only)
gl.mosaic("A -18 -13 -8 -3 2")

# Save the image
gl.savebmp("/Users/neel/Desktop/SPM_Aug_2025/BIGRAMS/renderings/visual_dual_contrast_with_intersection.png")