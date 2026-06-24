%SPM12 Group-level (2nd-level) analysis for the min-and-first first-level model.
% Takes a 'firstlevel_dir' containing all first-level results folders as input
% and saves each one-sample t-test to its own 'output' directory under SPM_results/FIRST.
%
% The first-level model (SPM_auditory_first_syllable_min_and_first_1st_level.m) has TWO contrasts:
%   con_0001 = Min Syllable Frequency
%   con_0002 = First Syllable Frequency
% A separate one-sample t-test is run for each.

firstlevel_dir = '/mnt/MOUSnew/SPM_results/FIRST/first_syllable_min_and_first';

% {con image, contrast name, output dir}
analyses = {
    'con_0001.nii', 'Min Syllable Frequency',   '/mnt/MOUSnew/SPM_results/FIRST/first_syllable_min_and_first_2nd_level_minsyll';
    'con_0002.nii', 'First Syllable Frequency', '/mnt/MOUSnew/SPM_results/FIRST/first_syllable_min_and_first_2nd_level_firstsyll'
};

for a = 1:size(analyses,1)
    conimg  = analyses{a,1};
    conname = analyses{a,2};
    output  = analyses{a,3};

    %build the list of first-level contrast images
    cd(char(firstlevel_dir))
    subjects = dir('sub-A*');
    subjNames = extractfield(subjects, 'name');
    scans = {};
    for m = 1:length(subjNames)
        scan = fullfile(firstlevel_dir, char(subjNames{m}), conimg);
        if isfile(scan)
            scans{m} = scan;
        end
    end
    scans = transpose(scans);

    %1. Factorial design (one-sample t-test)
    matlabbatch{1}.spm.stats.factorial_design.dir = {output};
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

    %2. Estimation
    matlabbatch{1}.spm.stats.fmri_est.spmmat = {fullfile(output, 'SPM.mat')};
    matlabbatch{1}.spm.stats.fmri_est.write_residuals = 0;
    matlabbatch{1}.spm.stats.fmri_est.method.Classical = 1;
    spm_jobman('run',matlabbatch)
    clear matlabbatch

    %3. Contrast
    matlabbatch{1}.spm.stats.con.spmmat = {fullfile(output, 'SPM.mat')};
    matlabbatch{1}.spm.stats.con.consess{1}.tcon.name = conname;
    matlabbatch{1}.spm.stats.con.consess{1}.tcon.weights = 1;
    matlabbatch{1}.spm.stats.con.consess{1}.tcon.sessrep = 'none';
    matlabbatch{1}.spm.stats.con.delete = 0;
    spm_jobman('run',matlabbatch)
    clear matlabbatch

    %4. Results
    spm('defaults','fmri')
    matlabbatch{1}.spm.stats.results.spmmat = {fullfile(output, 'SPM.mat')};
    matlabbatch{1}.spm.stats.results.conspec.titlestr = '';
    matlabbatch{1}.spm.stats.results.conspec.contrasts = 1;
    matlabbatch{1}.spm.stats.results.conspec.threshdesc = 'none';
    matlabbatch{1}.spm.stats.results.conspec.thresh = 0.0001;
    matlabbatch{1}.spm.stats.results.conspec.extent = 10;
    matlabbatch{1}.spm.stats.results.conspec.conjunction = 1;
    matlabbatch{1}.spm.stats.results.conspec.mask.none = 1;
    matlabbatch{1}.spm.stats.results.units = 1;
    matlabbatch{1}.spm.stats.results.export{1}.jpg = false;
    spm_jobman('run',matlabbatch)
    clear matlabbatch
    disp(['done: ' conname])
end
