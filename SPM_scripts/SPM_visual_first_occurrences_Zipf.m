%1st Level Visual Word Frequency Script
%Replace with directory containing preprocessed subject data.
subject_path = '/media/neel/MOUS1/MOUS/MOUS/fmriprep_fresh'; 
%replace with directory containing source data.
source = '/media/neel/MOUS1/MOUS/MOUS/SynologyDrive/source'
%replace with directory for output.  
outdir = '/home/neel/Documents/SPM_results/mean_centered/SPM-V_Zipf_first_occurrences' %MEAN-CENTERED! 6/25/25

cd(subject_path) 
subjects = dir('sub-V*');
subjNames = extractfield(subjects, 'name');



for v=1:length(subjNames)
    currentName = char(subjNames(v))
    if exist(fullfile(subject_path,currentName,'func'))
        regressors = readtable(char(fullfile(source, currentName, 'func',strcat(currentName,'_first_occurrences_frequencies.csv'))),'Delimiter',',');
        % Remove rows with NaN values
        %regressors = rmmissing(regressors); %one way of dealing with missing frequency values
        numericVars = varfun(@isnumeric, regressors, 'OutputFormat', 'uniform');
        regressors{:, numericVars} = fillmissing(regressors{:, numericVars}, 'constant', 0);
        
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
    
        matlabbatch{1}.spm.stats.fmri_spec.sess.cond(1).onset = regressors.Onset
        matlabbatch{1}.spm.stats.fmri_spec.sess.cond(1).duration = 0;
        matlabbatch{1}.spm.stats.fmri_spec.sess.cond(1).tmod = 0;
        matlabbatch{1}.spm.stats.fmri_spec.sess.cond(1).pmod(1).name = 'Word Length';
        matlabbatch{1}.spm.stats.fmri_spec.sess.cond(1).pmod(1).param = regressors.WordLength - mean(regressors.WordLength);
        matlabbatch{1}.spm.stats.fmri_spec.sess.cond(1).pmod(1).poly = 1;
        matlabbatch{1}.spm.stats.fmri_spec.sess.cond(1).pmod(2).name = 'Word Frequency';
        matlabbatch{1}.spm.stats.fmri_spec.sess.cond(1).pmod(2).param = 0-(regressors.Zipf - mean(regressors.Zipf));
        matlabbatch{1}.spm.stats.fmri_spec.sess.cond(1).pmod(2).poly = 1;
        matlabbatch{1}.spm.stats.fmri_spec.sess.cond(1).orth = 0;
        
        matlabbatch{1}.spm.stats.fmri_spec.sess.multi = {''};
        matlabbatch{1}.spm.stats.fmri_spec.sess.regress = struct('name', {}, 'val', {});
        %Motion regressors
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
        matlabbatch{1}.spm.stats.con.consess{1}.tcon.name = char(strcat("Word Frequency Correlation"));
        matlabbatch{1}.spm.stats.con.consess{1}.tcon.weights = [0 0 1 0];
        matlabbatch{1}.spm.stats.con.consess{1}.tcon.sessrep = 'none';
        matlabbatch{1}.spm.stats.con.delete = 0;
        spm_jobman('run',matlabbatch)
        disp('Contrast tested!')
        clear matlabbatch
    end
end

