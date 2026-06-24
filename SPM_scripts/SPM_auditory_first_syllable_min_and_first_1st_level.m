%SPM12 First-level analysis. Requires an 'outdir' to save output, a 'sourcedir' where the regressor data (frequency tables) is saved, and a 'subject_path' where the preprocessed data is saved.
%This model places TWO parametric modulators on the word-onset condition:
%   pmod(1) = minimum syllable frequency (MinSyllZipf)
%   pmod(2) = first syllable frequency   (First_syllable_zipf)
%Both modulators are demeaned and sign-flipped (as in first_syllable_frequency_1st_level_guslatho.m), and pmods are NOT orthogonalised (orth = 0).
subject_path = '/mnt/MOUSnew/fmriprep_fresh';
outdir = '/mnt/MOUSnew/SPM_results/FIRST/first_syllable_min_and_first';
mkdir(outdir)
sourcedir = '/mnt/MOUSnew/SynologyDrive/source/SynologyDrive';
cd(subject_path)
subjects = dir('sub-A*');
subjNames = extractfield(subjects, 'name');
cd('/home/lillianchang/Documents/MOUS_hierarchical-representations')
for m = 1:length(subjNames)
    currentName = subjNames(m);
    regressors = readtable(char(fullfile(sourcedir, currentName, 'func', strcat(currentName,'_first_syllable_frequency.csv'))),'Delimiter',',');
    disp(strcat("Number of onsets  = ", num2str(height(regressors))));



    % replace rows with NaN values with 0s
    numericVars = varfun(@isnumeric, regressors, 'OutputFormat', 'uniform');
    regressors{:, numericVars} = fillmissing(regressors{:, numericVars}, 'constant', 0);

    % Identify rows with Inf values
    inf_rows = any(isinf(regressors{:, numericVars}), 2);

    % Replace Inf values with 0s within numeric variables
    regressors{inf_rows, numericVars} = 0;

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
    %parametric modulator 1, minimum syllable frequency (demeaned and sign-flipped)
    matlabbatch{1}.spm.stats.fmri_spec.sess.cond.pmod(1).name = 'Min Syllable Frequency';
    matlabbatch{1}.spm.stats.fmri_spec.sess.cond.pmod(1).param = 0 - (regressors.MinSyllZipf - mean(regressors.MinSyllZipf))
    matlabbatch{1}.spm.stats.fmri_spec.sess.cond.pmod(1).poly = 1;
    %parametric modulator 2, first syllable frequency (demeaned and sign-flipped)
    matlabbatch{1}.spm.stats.fmri_spec.sess.cond.pmod(2).name = 'First Syllable Frequency';
    matlabbatch{1}.spm.stats.fmri_spec.sess.cond.pmod(2).param = 0 - (regressors.First_syllable_zipf - mean(regressors.First_syllable_zipf))
    matlabbatch{1}.spm.stats.fmri_spec.sess.cond.pmod(2).poly = 1;
    matlabbatch{1}.spm.stats.fmri_spec.sess.cond.orth = 0;
    matlabbatch{1}.spm.stats.fmri_spec.sess.multi = {''};
    matlabbatch{1}.spm.stats.fmri_spec.sess.regress = struct('name', {}, 'val', {});
    %Motion regressors. These should be produced by fmriprep.
    ConfoundsRegressors = tdfread(char(fullfile(subject_path, currentName, '/func/', strcat(currentName, '_task-auditory_desc-confounds_regressors.tsv'))));
    % Extract the relevant columns
    motion_regressors = [ConfoundsRegressors.trans_x, ConfoundsRegressors.rot_x, ...
                        ConfoundsRegressors.trans_y, ConfoundsRegressors.rot_y, ...
                        ConfoundsRegressors.trans_z, ConfoundsRegressors.rot_z];

    % Define the output file name
    output_file = fullfile(subject_path, currentName, '/func/', strcat(currentName, '_motion_regressors.txt'));

    % Write the motion regressors to a text file
    if ~isfile(output_file)
        dlmwrite(char(output_file), motion_regressors, 'delimiter', '\t', 'precision', 6);
        disp(['Motion regressors written to: ', output_file]);
    end


    matlabbatch{1}.spm.stats.fmri_spec.sess.multi_reg = {char(fullfile(subject_path, currentName, '/func/', strcat(currentName, '_motion_regressors.txt')))};
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
    %5. Contrasts
    %Design matrix columns: [Onset  Min-Syll-Freq  First-Syll-Freq]
    matlabbatch{1}.spm.stats.con.spmmat(1) = {char(fullfile(AnalysisDirectory, 'SPM.mat'))};
    matlabbatch{1}.spm.stats.con.consess{1}.tcon.name = 'Min Syllable Frequency';
    matlabbatch{1}.spm.stats.con.consess{1}.tcon.weights = [0 1 0];
    matlabbatch{1}.spm.stats.con.consess{1}.tcon.sessrep = 'none';
    matlabbatch{1}.spm.stats.con.consess{2}.tcon.name = 'First Syllable Frequency';
    matlabbatch{1}.spm.stats.con.consess{2}.tcon.weights = [0 0 1];
    matlabbatch{1}.spm.stats.con.consess{2}.tcon.sessrep = 'none';
    matlabbatch{1}.spm.stats.con.delete = 0;
    spm_jobman('run',matlabbatch)
    disp('Contrasts tested')
    clear matlabbatch
end
