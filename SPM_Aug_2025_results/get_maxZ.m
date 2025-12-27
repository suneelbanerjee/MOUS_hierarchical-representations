% Quick: max value (and location) of a Z-map using SPM12
file = 'spmZ_0001.nii';           % or .nii.gz
V = spm_vol(file);
[Z,~] = spm_read_vols(V);

[zmax, linidx] = max(Z(:));        % max Z (includes negatives if any)
[i,j,k] = ind2sub(size(Z), linidx);
xyz_mm = V.mat * [i; j; k; 1];

fprintf('Max Z = %.3f at voxel [%d %d %d], MNI = [%.1f %.1f %.1f] mm\n', ...
        zmax, i, j, k, xyz_mm(1), xyz_mm(2), xyz_mm(3));