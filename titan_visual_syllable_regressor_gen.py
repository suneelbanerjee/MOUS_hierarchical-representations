# %%
import pandas as pd
import numpy as np


# %%
word_syllable_frequencies = pd.read_csv('MOUS_word_syllable_frequencies.csv')
word_syllable_frequencies

# %%
def get_presented_words(events_tsv):
    sample_events = pd.read_csv(events_tsv, sep='\t')
    sample_events = sample_events.dropna(subset=['onset'])
    sample_events = sample_events[sample_events['type'] == 'Picture']
    sample_events = sample_events.reset_index(drop=True)
    #remove rows where value is WOORDEN, ZINNEN, blank, FIX ___, or ISI
    sample_events = sample_events[sample_events['value'] != 'WOORDEN']
    sample_events = sample_events[sample_events['value'] != 'QUESTION']
    sample_events = sample_events[sample_events['value'] != '']
    sample_events = sample_events[sample_events['value'] != 'ZINNEN']
    sample_events = sample_events[sample_events['value'] != 'blank']
    sample_events = sample_events[sample_events['value'].str.startswith('FIX') == False]
    sample_events = sample_events[sample_events['value'] != 'ISI']
    sample_events = sample_events.reset_index(drop=True)
    #clean all the values in the value column: only keep the letters
    sample_events['value'] = sample_events['value'].str.replace(r'[^a-zA-Z]', '')
    return sample_events
    

def make_params_csv(sample_events,path):
    onset, frequency, words = [], [], []

    for idx, word in enumerate(sample_events['value'].values):
        #get the row in word_syllable_frequencies that corresponds to the word
        row = word_syllable_frequencies[word_syllable_frequencies['Word'] == word]
        if not row.empty:
            words.append(word)
            frequency.append(row['minSyll'].values[0])
            onset.append(sample_events['onset'].values[idx])
        else:
            print(f"No match found for word: {word}")

    # %%
    #new df with onset and frequency
    df = pd.DataFrame({'word' : words, 'onset': onset, 'min_syll_frequency': frequency})
    df.to_csv(path, index=False)

from pathlib import Path
#subjects_path = Path('')
#for subject in subjects_path.iterdir():
#    if subject.is_dir():
#        if subject.name.startswith('sub-V'):
#            events = subject / 'func' / f'{subject.name}_task-visual_events.tsv'
#            if events.exists():
#                sample_events = get_presented_words(events)
#                make_params_csv(sample_events, subject / 'func' / f'{subject.name}_task-visual_syllable_params.csv')
