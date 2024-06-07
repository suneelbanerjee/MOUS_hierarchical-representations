%1st Level Group Analysis Script
%Replace with directory containing subjects
addpath(genpath('home/neelbanerjee/Downloads'))
subject_path = '/media/MOUS/MOUS/SynologyDrive/derivatives/fmriprep-20.1.1/fmriprep';
cd(subject_path)
subjects = dir('sub-v*');
subjNames = extractfield(subjects, 'name');


analyses = ["MeanPM", "MaxPM", "MinPM", "dmMeanPM", "dmMaxPM", "dmMinPM","LogMean", "LogMax", "LogMin", "dmLogMean", "dmLogMax", "dmLogMin"];
columns = [8,9,10,14,15,16,11,12,13,17,18,19];

for i = 1:length(analyses)
    cd('/media/MOUS/MOUS/SynologyDrive/derivatives/SPM-V')
    mkdir(analyses(i))
end

cd(subject_path)
for j = 1:length(analyses)
    for v=1:length(subjNames)
        currentName = char(subjNames(v));
        %1. File Selection
        ims = cellstr(spm_select('expand',[fullfile(subject_path, currentName, '/func/', strcat(currentName, '_task-visual_space-MNI152NLin6Asym_res-2_desc-preproc_bold.nii'))]));
        disp('Scans located')
        %2. Smoothing
        % matlabbatch{1}.spm.spatial.smooth.data = ims;
        % matlabbatch{1}.spm.spatial.smooth.fwhm = [6 6 6];
        % matlabbatch{1}.spm.spatial.smooth.dtype = 0;
        % matlabbatch{1}.spm.spatial.smooth.im = 0;
        % matlabbatch{1}.spm.spatial.smooth.prefix = 'z';
        % spm_jobman('run',matlabbatch)
        % disp('Smoothing Complete')
        clear matlabbatch
        %3. 1stLevel Analysis
        mkdir(strcat('/media/MOUS/MOUS/SynologyDrive/derivatives/SPM-V/', analyses(j),'/', currentName, '-1stLevel'))
        disp('Directory Created')
        AnalysisDirectory = char(fullfile(strcat('/media/MOUS/MOUS/SynologyDrive/derivatives/SPM-V/', analyses(j),'/',currentName, '-1stLevel')));
        matlabbatch{1}.spm.stats.fmri_spec.dir = {AnalysisDirectory};
        matlabbatch{1}.spm.stats.fmri_spec.timing.units = 'secs';
        matlabbatch{1}.spm.stats.fmri_spec.timing.RT = 2;
        matlabbatch{1}.spm.stats.fmri_spec.timing.fmri_t = 16;
        matlabbatch{1}.spm.stats.fmri_spec.timing.fmri_t0 = 8;
        %Load Smoothed Scans
        cd(strcat(subject_path, '/', currentName, '/func/'))
        SmoothedScan = dir('z*.nii');
        cd(subject_path)
        %Return to Batch
        matlabbatch{1}.spm.stats.fmri_spec.sess.scans = cellstr(spm_select('expand', [fullfile(SmoothedScan.folder, SmoothedScan.name)]));
        matlabbatch{1}.spm.stats.fmri_spec.sess.cond(1).name = 'Word';
        %Get master document of word data
        WordInfo=readmatrix(strcat(subject_path, '/', currentName, '/func/', 'Neel_DigramFreq-', currentName, '.xls'));
        matlabbatch{1}.spm.stats.fmri_spec.sess.cond(1).onset = WordInfo(:,1);
        matlabbatch{1}.spm.stats.fmri_spec.sess.cond(1).duration = 0;
        matlabbatch{1}.spm.stats.fmri_spec.sess.cond(1).tmod = 0;
        matlabbatch{1}.spm.stats.fmri_spec.sess.cond(1).pmod(1).name = analyses(j);
        matlabbatch{1}.spm.stats.fmri_spec.sess.cond(1).pmod(1).param = WordInfo(:,columns(j));
        matlabbatch{1}.spm.stats.fmri_spec.sess.cond(1).pmod(1).poly = 1;
        matlabbatch{1}.spm.stats.fmri_spec.sess.cond(1).orth = 0;
        
        matlabbatch{1}.spm.stats.fmri_spec.sess.multi = {''};
        matlabbatch{1}.spm.stats.fmri_spec.sess.regress = struct('name', {}, 'val', {});
        %Motion regressors
        ConfoundsRegressors = tdfread(fullfile(subject_path, currentName, '/func/', strcat(currentName, '_task-visual_desc-confounds_regressors.tsv')));
        rp_name = [ConfoundsRegressors.trans_x, ConfoundsRegressors.rot_x, ConfoundsRegressors.trans_y, ConfoundsRegressors.rot_y, ConfoundsRegressors.trans_z, ConfoundsRegressors.rot_z];
        matlabbatch{1}.spm.stats.fmri_spec.sess(1).multi_reg = {rp_name};
        %end of motion regressor lines
        matlabbatch{1}.spm.stats.fmri_spec.sess.multi_reg = {''};
        matlabbatch{1}.spm.stats.fmri_spec.sess.hpf = 128;
        matlabbatch{1}.spm.stats.fmri_spec.fact = struct('name', {}, 'levels', {});
        matlabbatch{1}.spm.stats.fmri_spec.bases.hrf.derivs = [0 0];
        matlabbatch{1}.spm.stats.fmri_spec.volt = 1;
        matlabbatch{1}.spm.stats.fmri_spec.global = 'None';
        matlabbatch{1}.spm.stats.fmri_spec.mthresh = 0.8;
        matlabbatch{1}.spm.stats.fmri_spec.mask = {''};
        matlabbatch{1}.spm.stats.fmri_spec.cvi = 'AR(1)';
        spm_jobman('run',matlabbatch)
        disp('Model Specified')
        clear matlabbatch
        %4. Estimation
        matlabbatch{1}.spm.stats.fmri_est.spmmat = {fullfile(AnalysisDirectory, 'SPM.mat')};
        matlabbatch{1}.spm.stats.fmri_est.write_residuals = 0;
        matlabbatch{1}.spm.stats.fmri_est.method.Classical = 1;
        spm_jobman('run',matlabbatch)
        disp('Model Estimated')
        clear matlabbatch
        %5. Contrast
        matlabbatch{1}.spm.stats.con.spmmat(1) = {fullfile(AnalysisDirectory, 'SPM.mat')};
        matlabbatch{1}.spm.stats.con.consess{1}.tcon.name = char(strcat(analyses(j), " Bigram Frequency Correlation"));
        matlabbatch{1}.spm.stats.con.consess{1}.tcon.weights = [0 1 0];
        matlabbatch{1}.spm.stats.con.consess{1}.tcon.sessrep = 'none';
        matlabbatch{1}.spm.stats.con.delete = 0;
        spm_jobman('run',matlabbatch)
        disp('Contrast tested!')
        clear matlabbatch
    end
end
