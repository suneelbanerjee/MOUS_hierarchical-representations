%SPM12 Group-level analysis script. Takes in an 'output' directory to save output, and a 'firstlevel_dir' that contains all first-level results folders as input.

output = '/home/neel/Documents/SPM_results/SPM-V_II_Lg10_mean_bigram';
firstlevel_dir = fullfile('/home/neel/Documents/SPM_results/SPM-V_Lg10_mean_bigram');
%default = '/home/neel/Documents/SPM_results/SPM-V_Lg10BG_multireg_november'

matlabbatch{1}.spm.stats.factorial_design.dir = {output};
cd(char(firstlevel_dir))
subjects = dir('sub-V*');
subjNames = extractfield(subjects, 'name');
scans = {};

for m = 1:length(subjNames)
    scan = fullfile(firstlevel_dir, char(subjNames{m}), 'con_0001.nii');
    if isfile(scan)
        scans{m} = scan;
    end
end

scans = transpose(scans);
matlabbatch{1}.spm.stats.factorial_design.des.t1.scans = scans(~cellfun('isempty',scans));

matlabbatch{1}.spm.stats.factorial_design.cov = struct('c', {}, 'cname', {}, 'iCFI', {}, 'iCC', {});
matlabbatch{1}.spm.stats.factorial_design.multi_cov = struct('files', {}, 'iCFI', {}, 'iCC', {});
matlabbatch{1}.spm.stats.factorial_design.masking.tm.tm_none = 1;
matlabbatch{1}.spm.stats.factorial_design.masking.im = 1;
matlabbatch{1}.spm.stats.factorial_design.masking.em = {''};
matlabbatch{1}.spm.stats.factorial_design.globalc.g_omit = 1;
matlabbatch{1}.spm.stats.factorial_design.globalm.gmsca.gmsca_no = 1;
matlabbatch{1}.spm.stats.factorial_design.globalm.glonorm = 1;

spm_jobman('run',matlabbatch)
clear matlabbatch

matlabbatch{1}.spm.stats.fmri_est.spmmat = {fullfile(output, 'SPM.mat')};
matlabbatch{1}.spm.stats.fmri_est.write_residuals = 0;
matlabbatch{1}.spm.stats.fmri_est.method.Classical = 1;
spm_jobman('run',matlabbatch)
clear matlabbatch

matlabbatch{1}.spm.stats.con.spmmat = {fullfile(output, 'SPM.mat')};
matlabbatch{1}.spm.stats.con.consess{1}.tcon.name = 'Bigram Frequency Correlation';
matlabbatch{1}.spm.stats.con.consess{1}.tcon.weights = 1;
matlabbatch{1}.spm.stats.con.consess{1}.tcon.sessrep = 'none';
matlabbatch{1}.spm.stats.con.delete = 0;
spm_jobman('run',matlabbatch)
clear matlabbatch
spm('defaults','fmri')
matlabbatch{1}.spm.stats.results.spmmat = {fullfile(output, 'SPM.mat')};
matlabbatch{1}.spm.stats.results.conspec.titlestr = '';
matlabbatch{1}.spm.stats.results.conspec.contrasts = 1;
matlabbatch{1}.spm.stats.results.conspec.threshdesc = 'none';
matlabbatch{1}.spm.stats.results.conspec.thresh = 1e-02;
matlabbatch{1}.spm.stats.results.conspec.extent = 10;
matlabbatch{1}.spm.stats.results.conspec.conjunction = 1;
matlabbatch{1}.spm.stats.results.conspec.mask.none = 1;
matlabbatch{1}.spm.stats.results.units = 1;
matlabbatch{1}.spm.stats.results.export{1}.jpg = false;
spm_jobman('run',matlabbatch)
clear matlabbatch
disp('done')
%end
