import gl

gl.resetdefaults()
gl.backcolor(255, 255, 255)  # Set dark background
height = 7 #darkest value
# Load MNI template
gl.loadimage('mni152')

# Load first contrast (sublexical, blue)
gl.overlayload('/Users/neel/Desktop/SPM_Aug_2025/SYLLABLES/SPM_syllables_guslatho_Log10/spmZ_0001_thr_p1e-12_k20vox.nii')  
gl.minmax(1, height, 1)  
gl.colorname(1, '7cool')  
gl.opacity(1, 100)  # Fully opaque
gl.colorfromzero(1, 1)  # Set color range to start from zero for the first overlay


# Load second contrast (lexical, red
gl.overlayload('/Users/neel/Desktop/SPM_Aug_2025/AUDITORY/SPM-A_II/spmZ_0001_thr_p1e-12_k20vox.nii')  
gl.minmax(2, height, 1)  
gl.colorname(2, '1red')  
gl.opacity(2, 100)  # Fully opaque

# Load intersection mask (binary)
gl.overlayload('/Users/neel/Desktop/SPM_Aug_2025/intersection_masks/syllable_word_intersection.nii.gz')
gl.colorname(3, 'Plasma')     # Set a distinct color
gl.opacity(3, 100)             # Fully opaque
gl.minmax(3, 0.5, 1)           # Binary mask range for visibility
gl.colorfromzero(3, 0)         # Don't shift colormap for binary mask


# Ensure the cross-slice view is OFF
gl.shaderadjust('crosshairs', 0)  # Disable crosshairs

# Turn off the colorbar
gl.colorbarposition(0)

# Generate mosaic (axial slices only, no cross-slice view)
gl.mosaic("S H -0.3 64 62 60 58 56 54")

# Save the mosaic
gl.savebmp("/Users/neel/Desktop/SPM_Aug_2025/SYLLABLES/renderings/mosaic_dual_contrast_sagR.png")

gl.mosaic("Z H -0.3 -64 -62 -60 -58 -56 -54")  # Axial-only, single row")

gl.savebmp("/Users/neel/Desktop/SPM_Aug_2025/SYLLABLES/renderings/mosaic_dual_contrast_sagL.png")