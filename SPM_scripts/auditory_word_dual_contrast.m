
%SPM12 First-level analysis. Requires an 'outdir' to save output, a 'sourcedir' where the regressor data (frequency tables) is saved, and a 'subject_path' where the preprocessed data is saved. 


%The DUAL-CONTRAST series of analyses enters sublexical and lexical frequency regressors in the same model. 
%This one controls for sublexical frequency (min) when testing word frequency.

subject_path = '/media/neel/MOUS/MOUS/MOUS/fmriprep_fresh';
outdir = '/media/neel/MOUS/MOUS/MOUS/SPM_results/mean_centered/auditory_dur0_syll1_WF1';
mkdir(outdir)
sourcedir = '/media/neel/MOUS/MOUS/MOUS/SynologyDrive/source'; 
cd(subject_path)
subjects = dir('sub-A*');
subjNames = extractfield(subjects, 'name');
cd('/home/neel/Desktop/MOUS_hierarchical-representations') %change this to the location of the cloned code repo. 
%keep in mind the sufffix used in finding regressors
for m = 1:length(subjNames)
    currentName = subjNames(m);

    %SUBLEXICAL REGRESSORS
    regressors = readtable(char(fullfile(sourcedir, currentName, 'func', strcat(currentName, '_IPA_syllable_frequency_ijfix2.csv'))),'Delimiter',',');
    disp(strcat("Number of onsets  = ", num2str(height(regressors))));
    % Log transform the specified column
    regressors.Min_Freq_Count = log10(regressors.Min_Freq_Count);
    % replace rows with NaN values with 0s
    numericVars = varfun(@isnumeric, regressors, 'OutputFormat', 'uniform');
    regressors{:, numericVars} = fillmissing(regressors{:, numericVars}, 'constant', 0);
    % Identify rows with Inf values
    inf_rows = any(isinf(regressors{:, numericVars}), 2);
    % Replace Inf values with 0s within numeric variables
    regressors{inf_rows, numericVars} = 0;

    %LEXICAL REGRESSORS
    word_regressors = readtable(char(fullfile(sourcedir, currentName, 'func',strcat(currentName,'_word_frequencies.csv'))));
    transcription = readtable(char(fullfile(sourcedir,currentName,'func',strcat(currentName,'_transcription.csv'))));
    word_numericVars = varfun(@isnumeric, word_regressors, 'OutputFormat', 'uniform');
    word_regressors{:, word_numericVars} = fillmissing(word_regressors{:, word_numericVars}, 'constant', 0);
    word_regressors_edited = word_regressors;
    %check if length is equal
%     if height(regressors) ~= height(word_regressors)
%         error('The number of rows in the regressors table does not match the number of rows in the transcription table.');
%     end
    del_idx = [];
    for row = 1:height(word_regressors)
        onset = word_regressors.AlignOnset(row);
        if ~ismember(onset,regressors.AlignOnset)
            del_idx = [del_idx,row];
        end
    end
        
    word_regressors_edited(del_idx,:) = [];
    transcription(del_idx,:) = [];




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
  
    %2. FIRST LEVEL ANALYSIS
    %directory setup and scanning parameters
    mkdir(char(fullfile(outdir, currentName)))
    disp('Directory Created')
    AnalysisDirectory = fullfile(outdir, currentName);
    if exist(char(fullfile(AnalysisDirectory, 'SPM.mat')),'file')
        continue
    end
    matlabbatch{1}.spm.stats.fmri_spec.dir = AnalysisDirectory;
    matlabbatch{1}.spm.stats.fmri_spec.timing.units = 'secs';
    matlabbatch{1}.spm.stats.fmri_spec.timing.RT = 2;
    matlabbatch{1}.spm.stats.fmri_spec.timing.fmri_t = 16;
    matlabbatch{1}.spm.stats.fmri_spec.timing.fmri_t0 = 8;
    %load smoothed scans
    cd(char(fullfile(subject_path,currentName, 'func')))
    SmoothedScan = dir('J*.nii');
    if isempty(SmoothedScan)
        disp(['No smoothed scans found for subject: ', currentName]);
        continue;
    end
    cd(subject_path)
   %%%%%%%%%%REGRESSOR DEFINITION
    %regressor 0, onset
    matlabbatch{1}.spm.stats.fmri_spec.sess.scans = cellstr(spm_select('expand', [fullfile(SmoothedScan.folder, SmoothedScan.name)]));
    matlabbatch{1}.spm.stats.fmri_spec.sess.cond.name = 'Onset';
    matlabbatch{1}.spm.stats.fmri_spec.sess.cond.onset= regressors.AlignOnset;
    matlabbatch{1}.spm.stats.fmri_spec.sess.cond.duration = 0;
    matlabbatch{1}.spm.stats.fmri_spec.sess.cond.tmod = 0;
    %regressor 1, length control. used to test effects of word length/duration, but not part of final analysis. 
    %matlabbatch{1}.spm.stats.fmri_spec.sess.cond.pmod(1).name = 'Word Length (seconds)';
    %matlabbatch{1}.spm.stats.fmri_spec.sess.cond.pmod(1).param = transcription.Duration - mean(transcription.Duration)%demean
    %matlabbatch{1}.spm.stats.fmri_spec.sess.cond.pmod(1).poly = 1;

    %regressor 2, sublexical frequency
    matlabbatch{1}.spm.stats.fmri_spec.sess.cond.pmod(1).name = 'Syllable Frequency';
    matlabbatch{1}.spm.stats.fmri_spec.sess.cond.pmod(1).param = 0 - (regressors.Min_Freq_Count - mean(regressors.Min_Freq_Count));
    matlabbatch{1}.spm.stats.fmri_spec.sess.cond.pmod(1).poly = 1;
    %regressor 3, word frequency
    matlabbatch{1}.spm.stats.fmri_spec.sess.cond.pmod(2).name = 'Word Frequency';
    matlabbatch{1}.spm.stats.fmri_spec.sess.cond.pmod(2).param = 0 - (word_regressors_edited.Zipf - mean(word_regressors_edited.Zipf)); %Lg10WF and Zipf represent two alternate logarithmic measures of word frequency. 
    matlabbatch{1}.spm.stats.fmri_spec.sess.cond.pmod(2).poly = 1;
    %settings
    matlabbatch{1}.spm.stats.fmri_spec.sess.cond.orth = 0;
    matlabbatch{1}.spm.stats.fmri_spec.sess.multi = {''};
    matlabbatch{1}.spm.stats.fmri_spec.sess.regress = struct('name', {}, 'val', {});
    %regressor 4, Motion regressors. These should be produced by fmriprep. 
    ConfoundsRegressors = tdfread(char(fullfile(subject_path, currentName, '/func/', strcat(currentName, '_task-auditory_desc-confounds_regressors.tsv'))));
    %rp_name = [ConfoundsRegressors.trans_x, ConfoundsRegressors.rot_x, ConfoundsRegressors.trans_y, ConfoundsRegressors.rot_y, ConfoundsRegressors.trans_z, ConfoundsRegressors.rot_z];

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
    %5. Contrast
    matlabbatch{1}.spm.stats.con.spmmat(1) = {char(fullfile(AnalysisDirectory, 'SPM.mat'))};
    matlabbatch{1}.spm.stats.con.consess{1}.tcon.name = 'Word Frequency';
    matlabbatch{1}.spm.stats.con.consess{1}.tcon.weights = [0 0 0 1 0]; 
    matlabbatch{1}.spm.stats.con.consess{1}.tcon.sessrep = 'none';
    matlabbatch{1}.spm.stats.con.consess{1}.tcon.name = 'Syllable Frequency';
    matlabbatch{1}.spm.stats.con.consess{1}.tcon.weights = [0 0 1 0 0]; 
    matlabbatch{1}.spm.stats.con.consess{1}.tcon.sessrep = 'none';
    matlabbatch{1}.spm.stats.con.delete = 0;
    spm_jobman('run',matlabbatch)
    disp('Contrast tested')
    clear matlabbatch
end



