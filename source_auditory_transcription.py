# %%
import pandas as pd
from pathlib import Path
import os
import numpy as np

def source_auditory_transcription(events_tsv, audio_onsets_csv='MOUS_audio_onset_offsets_with_duration.csv', output_csv=None):
    # %%
    #Load in ForcedAligner output
    audio_onsets = pd.read_csv(audio_onsets_csv)

    # %%
    #filenames
    audio_onsets['TextGrid'] = audio_onsets['TextGrid'].apply(lambda x: x.split('/home/at/workdir/example_workbook.tg/EQ_Ramp_Int2_Int1LPF')[1].split('.TextGrid')[0])
    #audio_onsets

    # %%
    events_path = events_tsv
    events = pd.read_csv(events_path, sep='\t')
    #events

    # %%
    #block onsets
    block_onsets = events[events['value'].apply(lambda x: 'Start File' in x)]
    block_onsets = block_onsets.drop(columns=['duration'])
    #block_onsets

    # %%
    #sound file numbers
    block_onsets['value'] = block_onsets['value'].apply(lambda x: x.split('Start File ')[1].split('.wav')[0])
    #block_onsets

    # %%
    transcription = pd.DataFrame()
    for i, file in enumerate(block_onsets['value']):
        block_start = block_onsets['onset'].iloc[i]
        segment = audio_onsets[audio_onsets['TextGrid'].apply(lambda x: file in x)]
        segment = segment.drop(columns=['WordCount','NumWords','PresegBegin'])
        segment['AlignOnset'] = segment['AlignOnset'] + block_start
        #concatenate all segments
        transcription = pd.concat([transcription,segment])
    transcription = transcription.reset_index(drop=True)

    # %%
    if output_csv is not None:
        transcription.to_csv(output_csv)
    else:
        subject = Path(events_path).name.split('task-auditory_events.tsv')[0]
        output_csv = Path(events_path).parent / f'{subject}_transcription.csv'
        transcription.to_csv(output_csv)
        return transcription

    # %%



