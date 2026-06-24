%1st Level Visual analysis: TWO parametric modulators on the word-onset condition:
%   pmod(1) = minimum bigram frequency (Min_bigram_Zipf)
%   pmod(2) = first bigram frequency   (First_bigram_Zipf)
%Both modulators are demeaned and sign-flipped, and pmods are NOT orthogonalised (orth = 0),
%so each parameter estimate reflects variance unique to that modulator (after the other modulator,
%the word-onset main effect, and head motion). Mirrors first_bigram_1st_level.m.
subject_path = '/mnt/MOUSnew/fmriprep_fresh';
source = '/mnt/MOUSnew/SynologyDrive/source/SynologyDrive'
outdir = '/mnt/MOUSnew/SPM_results/FIRST/first_bigram_min_and_first'


cd(subject_path)
subjects = dir('sub-V*');
subjNames = extractfield(subjects, 'name');

for v=1:length(subjNames)
    currentName = char(subjNames(v))
    regressors = readtable(char(fullfile(source, currentName, 'func', strcat(currentName,'_first_and_min_bigram.csv'))),'Delimiter',',');
    %1. File Selection
    try
        ims = cellstr(spm_select('expand',[fullfile(subject_path, currentName, '/func/', strcat(currentName, '_task-visual_space-MNI152NLin6Asym_res-2_desc-preproc_bold.nii'))]));
    catch
        disp(strcat(currentName + " does not have task scans"))
        continue
    end
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
    mkdir(fullfile(outdir, currentName))
    disp('Directory Created')
    AnalysisDirectory = char(fullfile(outdir, currentName));
    if exist(fullfile(AnalysisDirectory, 'SPM.mat'))
        continue
    end
    matlabbatch{1}.spm.stats.fmri_spec.dir = {AnalysisDirectory};
    matlabbatch{1}.spm.stats.fmri_spec.timing.units = 'secs';
    matlabbatch{1}.spm.stats.fmri_spec.timing.RT = 2;
    matlabbatch{1}.spm.stats.fmri_spec.timing.fmri_t = 16;
    matlabbatch{1}.spm.stats.fmri_spec.timing.fmri_t0 = 8;
    %Load Smoothed Scans
    cd(strcat(subject_path, '/', currentName, '/func/'))
    SmoothedScan = dir('G*.nii') %either this or 'ssub-*'
    if isempty(SmoothedScan)
        disp(['No smoothed scans found for subject: ', currentName]);
        continue;
    end
    cd(subject_path)
    %Return to Batch
    matlabbatch{1}.spm.stats.fmri_spec.sess.scans = cellstr(spm_select('expand', [fullfile(SmoothedScan.folder, SmoothedScan.name)]));
    matlabbatch{1}.spm.stats.fmri_spec.sess.cond(1).name = 'Word Onset';
    matlabbatch{1}.spm.stats.fmri_spec.sess.cond(1).onset = regressors.Onset
    matlabbatch{1}.spm.stats.fmri_spec.sess.cond(1).duration = 0;
    matlabbatch{1}.spm.stats.fmri_spec.sess.cond(1).tmod = 0;

    %parametric modulator 1: minimum bigram frequency (demeaned, sign-flipped)
    matlabbatch{1}.spm.stats.fmri_spec.sess.cond(1).pmod(1).name = 'Min Bigram Frequency';
    matlabbatch{1}.spm.stats.fmri_spec.sess.cond(1).pmod(1).param = 0-(regressors.Min_bigram_Zipf - mean(regressors.Min_bigram_Zipf))
    matlabbatch{1}.spm.stats.fmri_spec.sess.cond(1).pmod(1).poly = 1;
    %parametric modulator 2: first bigram frequency (demeaned, sign-flipped)
    matlabbatch{1}.spm.stats.fmri_spec.sess.cond(1).pmod(2).name = 'First Bigram Frequency';
    matlabbatch{1}.spm.stats.fmri_spec.sess.cond(1).pmod(2).param = 0-(regressors.First_bigram_Zipf - mean(regressors.First_bigram_Zipf))
    matlabbatch{1}.spm.stats.fmri_spec.sess.cond(1).pmod(2).poly = 1;
    matlabbatch{1}.spm.stats.fmri_spec.sess.cond(1).orth = 0;

    matlabbatch{1}.spm.stats.fmri_spec.sess.multi = {''};
    matlabbatch{1}.spm.stats.fmri_spec.sess.regress = struct('name', {}, 'val', {});
    %Motion regressors (produced by fmriprep)
    ConfoundsRegressors = tdfread(fullfile(subject_path, currentName, '/func/', strcat(currentName, '_task-visual_desc-confounds_regressors.tsv')));
    motion_regressors = [ConfoundsRegressors.trans_x, ConfoundsRegressors.rot_x, ...
                        ConfoundsRegressors.trans_y, ConfoundsRegressors.rot_y, ...
                        ConfoundsRegressors.trans_z, ConfoundsRegressors.rot_z];
    output_file = fullfile(subject_path, currentName, '/func/', strcat(currentName, '_motion_regressors.txt'));
    if ~exist(output_file, 'file')
        dlmwrite(char(output_file), motion_regressors, 'delimiter', '\t', 'precision', 6);
        disp(['Motion regressors written to: ', output_file]);
    end
    matlabbatch{1}.spm.stats.fmri_spec.sess.multi_reg = {char(fullfile(subject_path, currentName, '/func/', strcat(currentName, '_motion_regressors.txt')))};
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
    %5. Contrasts. Design columns: [Word-Onset  Min-Bigram  First-Bigram]
    matlabbatch{1}.spm.stats.con.spmmat(1) = {fullfile(AnalysisDirectory, 'SPM.mat')};
    matlabbatch{1}.spm.stats.con.consess{1}.tcon.name = char(strcat("Min Bigram Frequency Correlation"));
    matlabbatch{1}.spm.stats.con.consess{1}.tcon.weights = [0 1 0];
    matlabbatch{1}.spm.stats.con.consess{1}.tcon.sessrep = 'none';
    matlabbatch{1}.spm.stats.con.consess{2}.tcon.name = char(strcat("First Bigram Frequency Correlation"));
    matlabbatch{1}.spm.stats.con.consess{2}.tcon.weights = [0 0 1];
    matlabbatch{1}.spm.stats.con.consess{2}.tcon.sessrep = 'none';
    matlabbatch{1}.spm.stats.con.delete = 0;
    spm_jobman('run',matlabbatch)
    disp('Contrasts tested!')
    clear matlabbatch
end
