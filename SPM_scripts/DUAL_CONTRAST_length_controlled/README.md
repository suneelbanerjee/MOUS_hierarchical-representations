# DUAL-CONTRAST VISUAL (length-controlled)  --  ACTIVE / CANONICAL

These are the corrected dual-contrast first-level scripts (word length now
controlled in BOTH scripts). Paths point at the reachable /mnt/MOUSnew mounts.

FIRST-LEVEL MODEL (3 parametric modulators, orth=0, mean-centered):
  pmod(1) Word Length
  pmod(2) Min BG Frequency  (log10_Min_plus1_Bigram, sign-flipped)
  pmod(3) Word Frequency    (Zipf, sign-flipped)
  Design cols: 1=Word 2=Length 3=MinBG 4=WordFreq 5..=motion

  visual_word_dual_contrast.m   -> con_0001 'Word Frequency'   [0 0 0 1 0]
                                   con_0002 'Bigram Frequency'  [0 0 1 0 0]
       out: /mnt/MOUSnew/SPM_results/DUAL_CONTRAST_length_controlled/visual_word_len1_plus1minBG1_WF1

  visual_bigram_dual_contrast.m -> standalone bigram model (order Length,WF,MinBG)
       out: .../visual_bigram_len1_minBG1_WF1   (NOTE: uses non-plus1 log10_Min_Bigram)

SECOND-LEVEL:
  visual_dual_contrast_2nd_level.m  reads con_0001 (Word) + con_0002 (Bigram)
  from the WORD first-level dir; label swap fixed.
       out: .../second_level/visual_CONJUNCTION_len1

RUN: matlab -nodisplay -nosplash -batch "run_word_firstlevel"
Resumable: subjects with an existing SPM.mat are skipped.
