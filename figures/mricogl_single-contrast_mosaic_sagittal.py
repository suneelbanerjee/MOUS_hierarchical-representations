import gl

gl.resetdefaults()
gl.backcolor(255, 255, 255)        # white background
gl.loadimage('mni152')

gl.overlayload('/Users/neel/Desktop/SPM_Aug_2025/SYLLABLES/SPM_syllables_guslatho_Log10/spmZ_0001_thr_p1e-12_k20vox.nii')   # unthresholded Z (or thresholded with NaNs)
gl.colorname(1, 'jet')
gl.opacity(1, 100)

gl.minmax(1, 7, 8.126)           # FULL image range (will include negatives if present)
gl.colorbarposition(1)

gl.shaderadjust('crosshairs', 0)
gl.mosaic("S H -0.3 64 62 60 58 56 54 52")
gl.savebmp("/Users/neel/Desktop/SPM_Aug_2025/SYLLABLES/renderings/right.png")
gl.mosaic("Z H -0.3 -64 -62 -60 -58 -56 -54 -52")
gl.savebmp("/Users/neel/Desktop/SPM_Aug_2025/SYLLABLES/renderings/left.png")

gl.resetdefaults()

import gl

gl.resetdefaults()
gl.backcolor(255, 255, 255)        # white background
gl.loadimage('mni152')

gl.overlayload('/Users/neel/Desktop/SPM_Aug_2025/AUDITORY/SPM-A_II/spmZ_0001_thr_p1e-12_k20vox.nii')   # unthresholded Z (or thresholded with NaNs)
gl.colorname(1, 'jet')
gl.opacity(1, 100)

gl.minmax(1, 7, 8.126)           # FULL image range (will include negatives if present)
gl.colorbarposition(1)

gl.shaderadjust('crosshairs', 0)
gl.mosaic("S H -0.3 64 62 60 58 56 54 52")
gl.savebmp("/Users/neel/Desktop/SPM_Aug_2025/AUDITORY/renderings/right.png")
gl.mosaic("Z H -0.3 -64 -62 -60 -58 -56 -54 -52")
gl.savebmp("/Users/neel/Desktop/SPM_Aug_2025/AUDITORY/renderings/left.png")