restoredefaultpath;
addpath('/home/lillianchang/AnalysisPrograms/spm12');
spm('defaults','fmri');
spm_jobman('initcfg');
fprintf('=== SPM %s initialised, starting word first-level %s ===\n', spm('Ver'), datestr(now));
run('/home/lillianchang/Documents/MOUS_hierarchical-representations/SPM_scripts/DUAL_CONTRAST_length_controlled/visual_word_dual_contrast.m');
fprintf('=== DONE %s ===\n', datestr(now));
