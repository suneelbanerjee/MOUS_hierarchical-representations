import pandas as pd
from pathlib import Path
import os
import argparse

def source_auditory_transcription(events_tsv, audio_onsets_csv='MOUS_audio_onset_offsets_with_duration.csv', output_csv=None):
    # Load in ForcedAligner output
    audio_onsets = pd.read_csv(audio_onsets_csv)

    # Filenames
    audio_onsets['TextGrid'] = audio_onsets['TextGrid'].apply(lambda x: x.split('/home/at/workdir/example_workbook.tg/EQ_Ramp_Int2_Int1LPF')[1].split('.TextGrid')[0])

    # Load events TSV
    events_path = events_tsv
    events = pd.read_csv(events_path, sep='\t')

    # Block onsets
    block_onsets = events[events['value'].apply(lambda x: 'Start File' in x)]
    block_onsets = block_onsets.drop(columns=['duration'])

    # Sound file numbers
    block_onsets['value'] = block_onsets['value'].apply(lambda x: x.split('Start File ')[1].split('.wav')[0])

    # Transcription
    transcription = pd.DataFrame()
    for i, file in enumerate(block_onsets['value']):
        block_start = block_onsets['onset'].iloc[i]
        segment = audio_onsets[audio_onsets['TextGrid'].apply(lambda x: file in x)]
        segment = segment.drop(columns=['WordCount', 'NumWords', 'PresegBegin'])
        segment['AlignOnset'] = segment['AlignOnset'] + block_start
        # Concatenate all segments
        transcription = pd.concat([transcription, segment])
    transcription = transcription.reset_index(drop=True)

    # Save output CSV
    if output_csv is not None:
        transcription.to_csv(output_csv, index=False)
    else:
        subject = Path(events_path).name.split('_task-auditory_events.tsv')[0]
        output_csv = Path(events_path).parent / f'{subject}_transcription.csv'
        transcription.to_csv(output_csv, index=False)
    
    return transcription

def main():
    parser = argparse.ArgumentParser(description='Process auditory transcription data.')
    parser.add_argument('events_tsv', type=str, help='Path to the events TSV file.')
    parser.add_argument('--audio_onsets_csv', type=str, default='MOUS_audio_onset_offsets_with_duration.csv', help='Path to the audio onsets CSV file.')
    parser.add_argument('--output_csv', type=str, help='Path to save the output CSV file.')

    args = parser.parse_args()

    source_auditory_transcription(args.events_tsv, args.audio_onsets_csv, args.output_csv)

if __name__ == "__main__":
    main()
