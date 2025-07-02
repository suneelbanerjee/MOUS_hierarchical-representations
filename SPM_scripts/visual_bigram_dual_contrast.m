%1st Level Visual Word Frequency Script, with Bigram Frequency as a control
%Replace with directory containing preprocessed subject data.
subject_path = '/media/neel/MOUS/MOUS/MOUS/fmriprep_fresh'; 
%replace with directory containing source data.
source = '/media/neel/MOUS/MOUS/MOUS/SynologyDrive/source'
%replace with directory for output.  
outdir = '/media/neel/MOUS/MOUS/MOUS/SPM_results/mean_centered/visual_WF0_minBG1'

cd(subject_path) 
subjects = dir('sub-V*');
subjNames = extractfield(subjects, 'name');



for v=1:length(subjNames)
    currentName = char(subjNames(v))
    if exist(fullfile(subject_path,currentName,'func'))
        %%LEXICAL REGRESSORS
        word_regressors = readtable(char(fullfile(source, currentName, 'func',strcat(currentName,'_word_frequencies.csv'))),'Delimiter',',');
        % Remove rows with NaN values
        %regressors = rmmissing(regressors); %one way of dealing with missing frequency values
        numericVars = varfun(@isnumeric, word_regressors, 'OutputFormat', 'uniform');
        word_regressors{:, numericVars} = fillmissing(word_regressors{:, numericVars}, 'constant', 0);
        %%SUBLEXICAL REGRESSORS

        sublex_regressors = readtable(char(fullfile(source, currentName, 'func', strcat(currentName,'_bigrams_processed.csv'))),'Delimiter',',');

        
        %1. File Selection
        %ims = cellstr(spm_select('expand',[fullfile(subject_path, currentName, '/func/', strcat(currentName, '_task-visual_space-MNI152NLin6Asym_res-2_desc-preproc_bold.nii'))]));
        %disp('Scans located')
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
        SmoothedScan = dir('G*.nii')
        if isempty(SmoothedScan)
            disp(['No smoothed scans found for subject: ', currentName]);
            continue;
        end
        cd(subject_path)
        %Return to Batch
        matlabbatch{1}.spm.stats.fmri_spec.sess.scans = cellstr(spm_select('expand', [fullfile(SmoothedScan.folder, SmoothedScan.name)]));
        matlabbatch{1}.spm.stats.fmri_spec.sess.cond(1).name = 'Word';
        %Get master document of word data
        %REGRESSOR 0: ONSET
        matlabbatch{1}.spm.stats.fmri_spec.sess.cond(1).onset = word_regressors.Onset
        matlabbatch{1}.spm.stats.fmri_spec.sess.cond(1).duration = 0;
        matlabbatch{1}.spm.stats.fmri_spec.sess.cond(1).tmod = 0;

        %REGRESSOR 1: WORD LENGTH
        %matlabbatch{1}.spm.stats.fmri_spec.sess.cond(1).pmod(1).name = 'Word Length';
        %matlabbatch{1}.spm.stats.fmri_spec.sess.cond(1).pmod(1).param = word_regressors.WordLength - mean(word_regressors.WordLength);
        %matlabbatch{1}.spm.stats.fmri_spec.sess.cond(1).pmod(1).poly = 1;

        %REGRESSOR 2: ZIPF Word Frequency
        matlabbatch{1}.spm.stats.fmri_spec.sess.cond(1).pmod(1).name = 'Word Frequency';
        matlabbatch{1}.spm.stats.fmri_spec.sess.cond(1).pmod(1).param = 0- (word_regressors.Zipf - mean(word_regressors.Zipf));
        matlabbatch{1}.spm.stats.fmri_spec.sess.cond(1).pmod(1).poly = 1;

        %REGRESSOR 3: BIGRAM FREQUENCY (MIN). Do confirm the r2 between minBGfreq and Zipf before usng it as a regressor here- don't want to destroy the entire effect!
        matlabbatch{1}.spm.stats.fmri_spec.sess.cond(1).pmod(2).name = 'Min BG Frequency';
        matlabbatch{1}.spm.stats.fmri_spec.sess.cond(1).pmod(2).param = 0-(sublex_regressors.log10_Min_Bigram -mean(sublex_regressors.log10_Min_Bigram));
        matlabbatch{1}.spm.stats.fmri_spec.sess.cond(1).pmod(2).poly = 1;

        %Settings
        matlabbatch{1}.spm.stats.fmri_spec.sess.cond(1).orth = 0;
        matlabbatch{1}.spm.stats.fmri_spec.sess.multi = {''};
        matlabbatch{1}.spm.stats.fmri_spec.sess.regress = struct('name', {}, 'val', {});
        %REGRESSOR 4: Motion regressors
        ConfoundsRegressors = tdfread(fullfile(subject_path, currentName, '/func/', strcat(currentName, '_task-visual_desc-confounds_regressors.tsv')));
        motion_regressors = [ConfoundsRegressors.trans_x, ConfoundsRegressors.rot_x, ConfoundsRegressors.trans_y, ConfoundsRegressors.rot_y, ConfoundsRegressors.trans_z, ConfoundsRegressors.rot_z];
        % Define the output file name
        output_file = fullfile(subject_path, currentName, '/func/', strcat(currentName, '_motion_regressors.txt'));
        % Write the motion regressors to a text file
        if ~isfile(output_file)
            dlmwrite(char(output_file), motion_regressors, 'delimiter', '\t', 'precision', 6);
            disp(['Motion regressors written to: ', output_file]);
        end
        matlabbatch{1}.spm.stats.fmri_spec.sess.multi_reg = {char(fullfile(subject_path, currentName, '/func/', strcat(currentName, '_motion_regressors.txt')))};
        %end of motion regressor lines
        %matlabbatch{1}.spm.stats.fmri_spec.sess.multi_reg = {''};
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
        matlabbatch{1}.spm.stats.con.consess{1}.tcon.name = char(strcat("Bigram Frequency Correlation (regressing out word frequency, no length control)"));
        matlabbatch{1}.spm.stats.con.consess{1}.tcon.weights = [0 0 1 0];
        matlabbatch{1}.spm.stats.con.consess{1}.tcon.sessrep = 'none';
        matlabbatch{1}.spm.stats.con.delete = 0;
        spm_jobman('run',matlabbatch)
        disp('Contrast tested!')
        clear matlabbatch
    end
end

