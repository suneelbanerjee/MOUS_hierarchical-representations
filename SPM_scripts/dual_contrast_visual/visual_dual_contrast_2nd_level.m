%==========================================================================
% SPM12 BATCH SCRIPT: SIMPLE CONJUNCTION ANALYSIS
%
% This script uses the "Two-Sample T-test" module to create a simple
% model with two separate regressors for the conjunction analysis.
%==========================================================================

spm('defaults', 'fmri');
spm_jobman('initcfg');

%% 1. SETUP PATHS AND SUBJECTS
%--------------------------------------------------------------------------
firstlevel_dir = '/media/neel/MOUS/MOUS/MOUS/SPM_results/mean_centered/visual_len0_minBG1_WF1';
output_dir = '/media/neel/MOUS/MOUS/MOUS/SPM_results/mean_centered/second_level/visual_CONJUNCTION_simple';

if ~exist(output_dir, 'dir')
    mkdir(output_dir);
end

subjects = dir(fullfile(firstlevel_dir, 'sub-V*'));
subjNames = {subjects.name};
num_subjects = numel(subjNames);

% Prepare lists of contrast images for each "group"
scans1 = cell(num_subjects, 1); % Group 1: con_0001 (Bigram Freq)
scans2 = cell(num_subjects, 1); % Group 2: con_0002 (Word Freq)

for m = 1:num_subjects
    scans1{m} = fullfile(firstlevel_dir, subjNames{m}, 'con_0001.nii,1');
    scans2{m} = fullfile(firstlevel_dir, subjNames{m}, 'con_0002.nii,1');
end

%% 2. MODEL SPECIFICATION: Two-Sample T-test
%--------------------------------------------------------------------------
clear matlabbatch;
matlabbatch{1}.spm.stats.factorial_design.dir = {output_dir};
matlabbatch{1}.spm.stats.factorial_design.des.t2.scans1 = scans1;
matlabbatch{1}.spm.stats.factorial_design.des.t2.scans2 = scans2;
matlabbatch{1}.spm.stats.factorial_design.des.t2.dept = 0; % Independent
matlabbatch{1}.spm.stats.factorial_design.des.t2.variance = 1; % Unequal variance
matlabbatch{1}.spm.stats.factorial_design.des.t2.gmsca = 0;
matlabbatch{1}.spm.stats.factorial_design.des.t2.ancova = 0;

% --- Standard options ---
matlabbatch{1}.spm.stats.factorial_design.cov = struct('c', {}, 'cname', {}, 'iCFI', {}, 'iCC', {});
matlabbatch{1}.spm.stats.factorial_design.multi_cov = struct('files', {}, 'iCFI', {}, 'iCC', {});
matlabbatch{1}.spm.stats.factorial_design.masking.tm.tm_none = 1;
matlabbatch{1}.spm.stats.factorial_design.masking.im = 1;
matlabbatch{1}.spm.stats.factorial_design.masking.em = {''};
matlabbatch{1}.spm.stats.factorial_design.globalc.g_omit = 1;
matlabbatch{1}.spm.stats.factorial_design.globalm.gmsca.gmsca_no = 1;
matlabbatch{1}.spm.stats.factorial_design.globalm.glonorm = 1;

spm_jobman('run', matlabbatch);


%% 3. MODEL ESTIMATION
%--------------------------------------------------------------------------
clear matlabbatch;
matlabbatch{1}.spm.stats.fmri_est.spmmat = {fullfile(output_dir, 'SPM.mat')};
matlabbatch{1}.spm.stats.fmri_est.write_residuals = 0;
matlabbatch{1}.spm.stats.fmri_est.method.Classical = 1;

spm_jobman('run', matlabbatch);


%% 4. DEFINE INDIVIDUAL CONTRASTS
% The design matrix has two columns: Mean of Group 1 and Mean of Group 2
%--------------------------------------------------------------------------
clear matlabbatch;
matlabbatch{1}.spm.stats.con.spmmat = {fullfile(output_dir, 'SPM.mat')};

% Contrast 1: Positive effect of Group 1 (Bigram Freq)
matlabbatch{1}.spm.stats.con.consess{1}.tcon.name = 'Positive Bigram Effect';
matlabbatch{1}.spm.stats.con.consess{1}.tcon.weights = [1 0];
matlabbatch{1}.spm.stats.con.consess{1}.tcon.sessrep = 'none';

% Contrast 2: Positive effect of Group 2 (Word Freq)
matlabbatch{1}.spm.stats.con.consess{2}.tcon.name = 'Positive Word Freq Effect';
matlabbatch{1}.spm.stats.con.consess{2}.tcon.weights = [0 1];
matlabbatch{1}.spm.stats.con.consess{2}.tcon.sessrep = 'none';

matlabbatch{1}.spm.stats.con.delete = 1; % Overwrite existing contrasts

spm_jobman('run', matlabbatch);


%% 5. NEXT STEPS
%--------------------------------------------------------------------------
disp(' ');
disp('*******************************************************************');
disp('Model estimation and contrast definition complete.');
disp('You are now ready for the conjunction analysis.');
disp(' ');
disp('NEXT STEP: Open the SPM GUI, click "Results", and select the');
disp(['SPM.mat file located in: ' output_dir]);
disp('Then, select both T-contrasts simultaneously to run the conjunction.');
disp('*******************************************************************');
disp(' ');