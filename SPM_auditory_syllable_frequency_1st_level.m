%SPM12 First-level analysis. Requires an 'outdir' to save output, a 'sourcedir' where the regressor data (frequency tables) is saved, and a 'subject_path' where the preprocessed data is saved. 
subject_path = '/media/neel/MOUS/MOUS/MOUS/fmriprep_fresh';
outdir = '/home/neel/Documents/SPM_results/SPM-A_syllables_centered';
mkdir(outdir)
sourcedir = '/media/neel/MOUS/MOUS/MOUS/SynologyDrive/source'; 
cd(subject_path)
subjects = dir('sub-A*');
subjNames = extractfield(subjects, 'name');
cd('/home/neel/Desktop/MOUS_hierarchical-representations') %change this to the location of the cloned code repo. 
for m = 1:length(subjNames) %subj index
    currentName = subjNames(m);
    regressors = readtable(char(fullfile(sourcedir, currentName, 'func', strcat(currentName, '_transcription_syllables_processed.csv'))),'Delimiter',',');
    disp(strcat("Number of onsets  = ", num2str(height(regressors))));

    % Log transform the specified column
    regressors.Minimum_Syllable_Frequency = log10(regressors.Minimum_Syllable_Frequency);

    % replace rows with NaN values with 0s
    numericVars = varfun(@isnumeric, regressors, 'OutputFormat', 'uniform');
    regressors{:, numericVars} = fillmissing(regressors{:, numericVars}, 'constant', 0);

    % % Remove rows with Inf values
    % regressors = regressors(~isinf(regressors.Minimum_Syllable_Frequency), :);

    disp(strcat("Number of onsets after log transform, removing NaNs and Infs = ", num2str(height(regressors))));

    %%0. Coregister. Uncomment and modify the below if this was not done by fmriprep. 
    
    % matlabbatch{1}.spm.spatial.coreg.estwrite.ref = {'/media/MOUS/MOUS/SynologyDrive/source/sub-A2124/func/sub-A2124_task-auditory_bold.nii,1'}; %functional. expand.
    % matlabbatch{1}.spm.spatial.coreg.estwrite.source = {'/media/MOUS/MOUS/SynologyDrive/source/sub-A2124/anat/sub-A2124_T1w.nii,1'}; %anatomical.
    % matlabbatch{1}.spm.spatial.coreg.estwrite.other = {''};
    % matlabbatch{1}.spm.spatial.coreg.estwrite.eoptions.cost_fun = 'nmi';
    % matlabbatch{1}.spm.spatial.coreg.estwrite.eoptions.sep = [4 2];
    % matlabbatch{1}.spm.spatial.coreg.estwrite.eoptions.tol = [0.02 0.02 0.02 0.001 0.001 0.001 0.01 0.01 0.01 0.001 0.001 0.001];
    % matlabbatch{1}.spm.spatial.coreg.estwrite.eoptions.fwhm = [7 7];
    % matlabbatch{1}.spm.spatial.coreg.estwrite.roptions.interp = 4;
    % matlabbatch{1}.spm.spatial.coreg.estwrite.roptions.wrap = [0 0 0];
    % matlabbatch{1}.spm.spatial.coreg.estwrite.roptions.mask = 0;
    % matlabbatch{1}.spm.spatial.coreg.estwrite.roptions.prefix = 'april_coreg';
    %
    % %Segmentation (necessary for normalization)
    % matlabbatch{1}.spm.spatial.preproc.channel.vols = {'april_coreg'};
    % matlabbatch{1}.spm.spatial.preproc.channel.biasreg = 0.001;
    % matlabbatch{1}.spm.spatial.preproc.channel.biasfwhm = 60;
    % matlabbatch{1}.spm.spatial.preproc.channel.write = [0 1];
    % matlabbatch{1}.spm.spatial.preproc.tissue(1).tpm = {'/home/neelbanerjee/Documents/spm12/tpm/TPM.nii,1'};
    % matlabbatch{1}.spm.spatial.preproc.tissue(1).ngaus = 1;
    % matlabbatch{1}.spm.spatial.preproc.tissue(1).native = [1 0];
    % matlabbatch{1}.spm.spatial.preproc.tissue(1).warped = [0 0];
    % matlabbatch{1}.spm.spatial.preproc.tissue(2).tpm = {'/home/neelbanerjee/Documents/spm12/tpm/TPM.nii,2'};
    % matlabbatch{1}.spm.spatial.preproc.tissue(2).ngaus = 1;
    % matlabbatch{1}.spm.spatial.preproc.tissue(2).native = [1 0];
    % matlabbatch{1}.spm.spatial.preproc.tissue(2).warped = [0 0];
    % matlabbatch{1}.spm.spatial.preproc.tissue(3).tpm = {'/home/neelbanerjee/Documents/spm12/tpm/TPM.nii,3'};
    % matlabbatch{1}.spm.spatial.preproc.tissue(3).ngaus = 2;
    % matlabbatch{1}.spm.spatial.preproc.tissue(3).native = [1 0];
    % matlabbatch{1}.spm.spatial.preproc.tissue(3).warped = [0 0];
    % matlabbatch{1}.spm.spatial.preproc.tissue(4).tpm = {'/home/neelbanerjee/Documents/spm12/tpm/TPM.nii,4'};
    % matlabbatch{1}.spm.spatial.preproc.tissue(4).ngaus = 3;
    % matlabbatch{1}.spm.spatial.preproc.tissue(4).native = [1 0];
    % matlabbatch{1}.spm.spatial.preproc.tissue(4).warped = [0 0];
    % matlabbatch{1}.spm.spatial.preproc.tissue(5).tpm = {'/home/neelbanerjee/Documents/spm12/tpm/TPM.nii,5'};
    % matlabbatch{1}.spm.spatial.preproc.tissue(5).ngaus = 4;
    % matlabbatch{1}.spm.spatial.preproc.tissue(5).native = [1 0];
    % matlabbatch{1}.spm.spatial.preproc.tissue(5).warped = [0 0];
    % matlabbatch{1}.spm.spatial.preproc.tissue(6).tpm = {'/home/neelbanerjee/Documents/spm12/tpm/TPM.nii,6'};
    % matlabbatch{1}.spm.spatial.preproc.tissue(6).ngaus = 2;
    % matlabbatch{1}.spm.spatial.preproc.tissue(6).native = [0 0];
    % matlabbatch{1}.spm.spatial.preproc.tissue(6).warped = [0 0];
    % matlabbatch{1}.spm.spatial.preproc.warp.mrf = 1;
    % matlabbatch{1}.spm.spatial.preproc.warp.cleanup = 1;
    % matlabbatch{1}.spm.spatial.preproc.warp.reg = [0 0.001 0.5 0.05 0.2];
    % matlabbatch{1}.spm.spatial.preproc.warp.affreg = 'mni';
    % matlabbatch{1}.spm.spatial.preproc.warp.fwhm = 0;
    % matlabbatch{1}.spm.spatial.preproc.warp.samp = 3;
    % matlabbatch{1}.spm.spatial.preproc.warp.write = [0 1];
    % matlabbatch{1}.spm.spatial.preproc.warp.vox = NaN;
    % matlabbatch{1}.spm.spatial.preproc.warp.bb = [NaN NaN NaN
    %                                               NaN NaN NaN];
 
    %1. FILE FINDING
    %gunzip
    if isfile(char(fullfile(subject_path,currentName,'func',strcat(currentName,'_task-auditory_space-MNI152NLin6Asym_res-2_desc-preproc_bold.nii.gz'))))
        gunzip(char(fullfile(subject_path,currentName,'func',strcat(currentName,'_task-auditory_space-MNI152NLin6Asym_res-2_desc-preproc_bold.nii.gz'))))
        delete(char(fullfile(subject_path,currentName,'func',strcat(currentName,'_task-auditory_space-MNI152NLin6Asym_res-2_desc-preproc_bold.nii.gz'))))
    end
    try
        ims = cellstr(spm_select('expand',[fullfile(subject_path, currentName, '/func/', strcat(currentName, '_task-auditory_space-MNI152NLin6Asym_res-2_desc-preproc_bold.nii'))]));
        disp('Scans located')
    catch
        continue 
    end
    %2. SMOOTHING
    %%uncomment if running for the first time!
    % matlabbatch{1}.spm.spatial.smooth.data = ims;
    % matlabbatch{1}.spm.spatial.smooth.fwhm = [6 6 6];
    % matlabbatch{1}.spm.spatial.smooth.dtype = 0;
    % matlabbatch{1}.spm.spatial.smooth.im = 0;
    % matlabbatch{1}.spm.spatial.smooth.prefix = 'J';
    % spm_jobman('run',matlabbatch)
    % disp('Smoothing Complete')
    % clear matlabbatch
    %3. FIRST LEVEL ANALYSIS
    %directory setup and scanning parameters
    mkdir(char(fullfile(outdir, currentName)))
    disp('Directory Created')
    AnalysisDirectory = fullfile(outdir, currentName);
    matlabbatch{1}.spm.stats.fmri_spec.dir = AnalysisDirectory;
    matlabbatch{1}.spm.stats.fmri_spec.timing.units = 'secs';
    matlabbatch{1}.spm.stats.fmri_spec.timing.RT = 2;
    matlabbatch{1}.spm.stats.fmri_spec.timing.fmri_t = 16;
    matlabbatch{1}.spm.stats.fmri_spec.timing.fmri_t0 = 8;
    %load smoothed scans
    cd(char(fullfile(subject_path,currentName, 'func')))
    SmoothedScan = dir('J*.nii');
    cd(subject_path)
    %regressor 1, onset
    matlabbatch{1}.spm.stats.fmri_spec.sess.scans = cellstr(spm_select('expand', [fullfile(SmoothedScan.folder, SmoothedScan.name)]));
    matlabbatch{1}.spm.stats.fmri_spec.sess.cond.name = 'Onset';
    matlabbatch{1}.spm.stats.fmri_spec.sess.cond.onset= regressors.AlignOnset;
    matlabbatch{1}.spm.stats.fmri_spec.sess.cond.duration = 0;
    matlabbatch{1}.spm.stats.fmri_spec.sess.cond.tmod = 0;
    length control. used to test effects of word length/duration, but not part of final analysis. 
    % matlabbatch{1}.spm.stats.fmri_spec.sess.cond.pmod(1).name = 'Length';
    % matlabbatch{1}.spm.stats.fmri_spec.sess.cond.pmod(1).param = regressors.Duration %demean
    % matlabbatch{1}.spm.stats.fmri_spec.sess.cond.pmod(1).poly = 1;
    regressor 2, frequency
    matlabbatch{1}.spm.stats.fmri_spec.sess.cond.pmod(1).name = 'Syllable Frequency';
    matlabbatch{1}.spm.stats.fmri_spec.sess.cond.pmod(1).param = 0 - regressors.Minimum_Syllable_Frequency
    matlabbatch{1}.spm.stats.fmri_spec.sess.cond.pmod(1).poly = 1;
    matlabbatch{1}.spm.stats.fmri_spec.sess.cond.orth = 0;
    matlabbatch{1}.spm.stats.fmri_spec.sess.multi = {''};
    matlabbatch{1}.spm.stats.fmri_spec.sess.regress = struct('name', {}, 'val', {});
    %Motion regressors. These should be produced by fmriprep. 
    ConfoundsRegressors = tdfread(char(fullfile(subject_path, currentName, '/func/', strcat(currentName, '_task-auditory_desc-confounds_regressors.tsv'))));
    rp_name = [ConfoundsRegressors.trans_x, ConfoundsRegressors.rot_x, ConfoundsRegressors.trans_y, ConfoundsRegressors.rot_y, ConfoundsRegressors.trans_z, ConfoundsRegressors.rot_z];
    matlabbatch{1}.spm.stats.fmri_spec.sess(1).multi_reg = {rp_name};
    matlabbatch{1}.spm.stats.fmri_spec.sess.multi_reg = {''};
    matlabbatch{1}.spm.stats.fmri_spec.sess.hpf = 128;
    matlabbatch{1}.spm.stats.fmri_spec.fact = struct('name', {}, 'levels', {});
    matlabbatch{1}.spm.stats.fmri_spec.bases.hrf.derivs = [0 0];
    matlabbatch{1}.spm.stats.fmri_spec.volt = 1;
    matlabbatch{1}.spm.stats.fmri_spec.global = 'None';
    matlabbatch{1}.spm.stats.fmri_spec.mthresh = -Inf; %default is 0.8
    matlabbatch{1}.spm.stats.fmri_spec.mask = {''};
    matlabbatch{1}.spm.stats.fmri_spec.cvi = 'AR(1)';
    spm_jobman('run',matlabbatch)
    disp('Model Specified')
    clear matlabbatch
    %4. Estimation
    matlabbatch{1}.spm.stats.fmri_est.spmmat = {char(fullfile(AnalysisDirectory, 'SPM.mat'))};
    matlabbatch{1}.spm.stats.fmri_est.write_residuals = 0;
    matlabbatch{1}.spm.stats.fmri_est.method.Classical = 1;
    spm_jobman('run',matlabbatch)
    disp('Model Estimated')
    clear matlabbatch
    %5. Contrast
    matlabbatch{1}.spm.stats.con.spmmat(1) = {char(fullfile(AnalysisDirectory, 'SPM.mat'))};
    matlabbatch{1}.spm.stats.con.consess{1}.tcon.name = 'Syllable Frequency';
    matlabbatch{1}.spm.stats.con.consess{1}.tcon.weights = [0 1 0]; %edit if including duration control. 
    matlabbatch{1}.spm.stats.con.consess{1}.tcon.sessrep = 'none';
    matlabbatch{1}.spm.stats.con.delete = 0;
    spm_jobman('run',matlabbatch)
    disp('Contrast tested')
    clear matlabbatch
end
