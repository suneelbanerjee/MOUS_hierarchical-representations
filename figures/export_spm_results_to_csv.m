function export_spm_results_to_csv(spm_mat_file, pFWE)
    matlabbatch{1}.spm.stats.results.spmmat = {spm_mat_file};
    matlabbatch{1}.spm.stats.results.conspec.titlestr = '';
    matlabbatch{1}.spm.stats.results.conspec.contrasts = 1;
    matlabbatch{1}.spm.stats.results.conspec.threshdesc = 'FWE';
    matlabbatch{1}.spm.stats.results.conspec.thresh = pFWE;
    matlabbatch{1}.spm.stats.results.conspec.extent = 20;
    matlabbatch{1}.spm.stats.results.conspec.conjunction = 1;
    matlabbatch{1}.spm.stats.results.conspec.mask.none = 1;
    matlabbatch{1}.spm.stats.results.units = 1;
    matlabbatch{1}.spm.stats.results.export{1}.csv = true;
    spm_jobman('run', matlabbatch);
end

% export_spm_results_to_csv('SPM.mat', 0.01)
% spm_height_threshold = xSPM.u;
% writelines(strcat("u = ",num2str(spm_height_threshold)),'u_threshold.txt')