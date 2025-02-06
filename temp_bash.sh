python run_subtlex_IPA_syllables_chunks.py | tee run_subtlex_IPA_syllables_chunks.log
python celex_vs_IPA_script.py | tee celex_vs_IPA_script.log
matlab -nodisplay -nosplash -r "run('/home/neel/Desktop/MOUS_hierarchical-representations/SPM_auditory_syllable_frequency_1st_level_IPA.m'); exit;" | tee spm12_syllables_ijfix_script.log