# *Evidence for hierarchical representations of written and spoken words from an open-science human neuroimaging dataset*


**Tables and text files**

`SUBTLEX-NL with pos and Zipf.xlsx` Contains word frequency measures of Dutch words in the SUBTLEX database, the most up-to-date version of the CELEX database. `Zipf` contains log-transformed values of `FREQCOUNT`, the number of word occurrences in the corpus. For more information, visit [OSF](https://osf.io/3d8cx/).

`subtlex_v2_cleaned_no_drop3.xlsx` Screens the raw SUBTLEX database for entries that are not real words and contains a column suggesting whether to keep or drop an entry.

`MOUS_audio_onset_offsets.xlsx` Onset times of words in each audio file play in the speech listening part of the experiment.

`MOUS_audio_onset_offsets_with_duration.csv` Includes the durations of each spoken word in seconds.

`stimuli.txt` The sentences and word lists used in both the reading and speech listening experiments of the MOUS study.

`bigram_counts.csv` Cumulative bigram occurrences (per million) in the SUBTLEX text corpus.

**CELEX (used to confirm validity of syllabified IPA transcriptions)**

`dutch_celex_database_updatedv2.csv` Contains phonetic pronunciations of Dutch words in the CELEX database. For more information, see supplement to [Sun &amp; Poeppel 2023](https://www.pnas.org/doi/10.1073/pnas.2215710120?utm_source=TOC&utm_medium=ealert&TOC_v120_i36=&ref=d8253441).

`subtlex_phonetics.xlsx` The intersection of the CELEX database and SUBTLEX databases, contains phonetics and occurrence counts of most words in Dutch.

`syllable_counts.csv` Cumulative CELEX syllable occurrences (per million) in the SUBTLEX text corpus.

**[eSpeakNG](https://github.com/espeak-ng/espeak-ng?tab=readme-ov-file) (used to generate IPA syllabifications)**

`subtlex_v3_IPA_syllables_ijfix2.csv` The cleaned SUBTLEX database, now including IPA syllabifications.

`IPA_individual_syllable_frequencies_ijfix2.csv` Tabulates frequency counts of every unique Dutch syllable generated from running eSpeakNG on the SUBTLEX database.

`merged-IPA_CELEX.csv` Merges the above with CELEX to yield a side-by-side comparison of the two syllabification schemes.

`MOUS_IPA_transcriptions_ijfix2.csv` Includes syllabified IPA transcriptions of all study words.

`MOUS_IPA_SyllableFrequencies_ijfix2.csv` Includes syllabified IPA transcriptions and frequency statistics (mean, min, max) of all study words.

`n_syllable_conflict_ijfix2.csv` Lists words whose IPA-syllabified forms differ from CELEX in the # of syllables.

**Code**

`master_table IPA.ipynb `Generates bigram, syllable, and word frequency statistics for every word presented in the MOUS experiments.

*Auditory - Word Frequency*

`source_auditory_trancription.py` Takes in an auditory subject's `events.tsv` file and an output filename and tabulates the onset times and words played during that subject's scan. Generates transcription files that are saved in each subject's source subdirectory, e.g. `sub-A2002_transcription.csv`.

`source_auditory_transcription_loop.ipynb` Runs the above over all auditory subjects.

`SPM_auditory_word_frequency_1st_level.m` Runs SPM12 first-level analysis for Word Frequency across all auditory subjects. For a primer on this technique, see [Andy&#39;s Brain Book](https://andysbrainbook.readthedocs.io/en/latest/PM/PM_Overview.html)

`SPM_auditory_word_frequency_2nd_level.m`  Runs SPM12 group-level analysis for word frequency.

`SPM_auditory_word_frequency_1st_level_Positive.m `Tests for a positive correlation with word frequency.

*Auditory - Syllable Frequency*

`eSpeakNG_IPA.py` Functions to generate and parallelize command-line calls to eSpeak text-to-speech engine.

`run_subtlex_IPA_syllables_chunks.py` Runs eSpeakNG on the SUBTLEX database.

`syllabify_ipa_nl.py` Functions called upon by the above script that split an IPA transcription into its constituent syllables on the basis of syllabification rules.

`celex_vs_IPA_script.py` Generates regressor files for each subject. `celex_vs_IPA.ipynb` compares the eSpeak-generated syllabifications with CELEX, finding that 99% of the IPA-syllabified SUBTLEX words agree with CELEX in # of syllables.

`SPM_auditory_syllable_frequency_1st_level_IPA.m` Runs SPM12 first-level analysis for Syllable Frequency across all auditory subjects.

`SPM_auditory_syllable_frequency_2nd_level.m` Runs group-level analysis for syllable frequency.

`SPM_auditory_syllable_max_mean_frequency_1st_level_IPA.m` Tests max/mean syllable frequency as an alternate parameter.

*Visual - Word Frequency*

`source_visual_transcription.m` converts an events.tsv file to a cleaned CSV containing onset time and word presented.

`source_visual_transcription_loop.ipynb` Runs the above function in a loop over all visual subjects.

`calculate_word_frequencies_visual.ipynb` generates CSV files containing both word frequency and minimum bigram frequency info for all words in the study.

`SPM_visual_word_frequency_1st_level.m` Runs SPM12 first-level analysis for Word Frequency across all visual subjects.

`SPM_visual_word_frequency_2nd_level.m` Runs SPM12 group-level analysis for Word Frequency.

`SPM_visual_word_frequency_1st_level_Positive.m` Tests for a positive correlation with word frequency.

*Visual - Bigram Frequency*

`SPM_visual_bigram_frequency_1st_level.m` Runs SPM12 first-level analysis for Bigam Frequency across all visual subjects.

`SPM_visual_bigram_frequency_2nd_level.m` Runs SPM12 group-level analysis for bigram frequency.

`SPM_visual_max_bigram_frequency_1st_level.m` and `SPM_visual_mean_bigram_frequency_1st_level.m` test for correlations with max/mean bigram frequency respectively.

**`/figures`**

    `cluster_separation.ipynb` Thresholds a T-map, reports cluster peaks and calculates locations of cluster centers of mass.

    `min_sublexical_vs_zipf_frequency.ipynb` Generates scatterplots (reported in supplement) comparing different frequency statistics.

    `peak-scale_tmap.ipynb` divides all the voxels in a T-map by the peak T-stat in the map, making the T-map into a 'percent of peak activation' (PPA) )map.

    `LR_tmap_split.ipynb` Splits a T-map down the middle into left and right halves. Makes for easier visualizations.

    `mricrogl_renderings.py` Script that generates 3D renderings of T-maps. To run this script and the following, paste this code into the scripting interface of [MRIcroGL](https://www.nitrc.org/projects/mricrogl).

    `mricrogl_LR_renderings.py` Fetches left/right views of a T-map and renders them separately.

    `mricrogl_dual-contrast_mosaic_axial.py` Juxtaposes two PPA maps in axial slices.

    `mricrogl_dual-contrast_mosaic_sagittal.py` Does the above in sagittal slices.
