# %%
import pandas as pd
import re 
import numpy as np
from pathlib import Path

# %% [markdown]
# 1. Lining up and mapping between CELEX and IPA syllables
tag = 'ijfix2'
# %%
#subtlex = pd.read_csv('/home/neel/Desktop/MOUS_hierarchical-representations/subtlex_v3_IPA_syllables.csv')
subtlex = pd.read_csv(f'/home/neel/Desktop/MOUS_hierarchical-representations/subtlex_v3_IPA_syllables_{tag}.csv')
subtlex

# %%
subtlex_IPA = subtlex[['Word','Syllables','FREQcount','Zipf']]
subtlex_IPA.head()

# # %%
# # Load the CSV file
# celex = pd.read_csv('/home/neel/Desktop/MOUS_hierarchical-representations/dutch_celex_database_updatedv2.csv')

# # Check the columns of the DataFrame
# print(celex.columns)

# # Assuming the correct column name is 'phone_full', if it is not, replace 'phone_full' with the correct column name
# celex_syllables = celex[['Head', 'phone_full']]   

# # Rename columns
# celex_syllables = celex_syllables.rename(columns={'Head': 'Word', 'phone_full': 'CELEX'})

# # Remove apostrophes (stress marks) from every entry in 'CELEX'
# celex_syllables['CELEX'] = celex_syllables['CELEX'].str.replace("'", "")

# # Display the first few rows
# celex_syllables.head()

# # %%
# #merge the two dataframes on Word
# merged = pd.merge(subtlex_IPA, celex_syllables, on='Word', how='inner')
# #insert a space before and after every dash in the phone_full column
# merged['CELEX'] = merged['CELEX'].str.replace("-", " - ")
# #rename Syllables to IPA
# merged = merged.rename(columns={'Syllables': 'IPA'})
# #merged.to_csv('/home/neel/Desktop/MOUS_hierarchical-representations/merged-IPA_CELEX.csv', index=False)
# merged

# # %%
# #create an empty column for whether the number of syllables matches
# merged['Equal # of Syllables'] = np.nan



# %% [markdown]
# Syllable comparison

# %%

# syllables_mapping_master = {}
# conflict_mapping_master = []
# for row, word in enumerate(merged.iterrows()):
#     Celex2IPA_syllables_mapping = {}
#     IPA = word[1]['IPA']
#     CELEX = word[1]['CELEX']
#     # Split the IPA and CELEX strings into lists
#     IPA_list = IPA.split(" - ")
#     CELEX_list = CELEX.split(" - ")
#     # If the number of syllables in the lists is equal, create a mapping
#     if len(IPA_list) == len(CELEX_list):
#         merged.at[row, 'Equal # of Syllables'] = True
#         for i in range(len(IPA_list)):
#             Celex2IPA_syllables_mapping[CELEX_list[i]] = IPA_list[i]
#         # Concatenate the mappings for all words
#         # If an entry already exists in the dictionary, check if the mapping is the same
#         for key, value in Celex2IPA_syllables_mapping.items():
#             if key in syllables_mapping_master:
#                 if syllables_mapping_master[key] != value:
#                     print(f"Key {key} already exists in syllables_mapping_master with a different value.")
#                     conflict_mapping_master.append((key, syllables_mapping_master[key], value))
#             else:
#                 syllables_mapping_master[key] = value
#     else:
#         merged.at[row, 'Equal # of Syllables'] = False

# # %%
# #Check for convergence of syllable mapping conflicts (n = 37565)
# #e.g if the same CELEX syllable maps to different IPA syllables
# #eventually, pool: combine the frequency counts of all the IPA syllables that map to the same CELEX syllable
# conflict_mapping_master # (CELEX, IPA1, IPA2)
# #REFORMAT into a dictionary, where the first value in each tuple is the key, and the second and third values are the values. Merge all the entries which have the same key
# conflict_mapping_dict = {}
# for conflict in conflict_mapping_master:
#     if conflict[0] in conflict_mapping_dict:
#         conflict_mapping_dict[conflict[0]].append(conflict[1:])
#     else:
#         conflict_mapping_dict[conflict[0]] = [conflict[1:]]
# #only keep unique values for each key
# for key, value in conflict_mapping_dict.items():
#     conflict_mapping_dict[key] = list(set(value))

# #combine all the values for each key into a single list, then keep the unique elements
# for key, value in conflict_mapping_dict.items():
#     conflict_mapping_dict[key] = list(set([item for sublist in value for item in sublist]))
# conflict_mapping_dict


# # %%
# num_keys = len(conflict_mapping_dict)
# print(num_keys)

# # %%
# #Number of syllabification conflicts (n = 6292)
# #with heid fix, n = 5340
# #with ei fix, n = 544.
# n_syllable_conflict_df = merged[merged['Equal # of Syllables'] == False]
# n_syllable_conflict_df.to_csv(f'/home/neel/Desktop/MOUS_hierarchical-representations/n_syllable_conflict_{tag}.csv', index=False)
# n_syllable_conflict_df


# %% [markdown]
# 2. Frequencies of IPA Syllables

# %%
# subtlex

# %%
IPA_syllables = subtlex['Syllables']
all_ipa_syllables = set()
for index, value in IPA_syllables.items():
    if pd.isna(value):
        continue
    word_syllables = [syl for syl in value.split("-") if isinstance(syl,str)]
    all_ipa_syllables.update(word_syllables)
IPA_syllables = pd.DataFrame(all_ipa_syllables, columns=['Syllables'])
IPA_syllables

# %%
# #quick check to see how many CELEX syllables there are
# celex_syllables 

# # %%
# all_celex_syllables = set()
# for index, row in celex_syllables.iterrows():
#     value = row['CELEX']  # Replace 'Syllables' with the actual column name if different
#     if pd.isna(value):
#         continue
#     word_syllables = [syl for syl in value.split("-") if isinstance(syl, str)]
#     all_celex_syllables.update(word_syllables)

# CELEX_syllables_df = pd.DataFrame(list(all_celex_syllables), columns=['Syllables'])
# CELEX_syllables_df


# %% [markdown]
# 37526 > 8751. Interesting. 

# %% [markdown]
# Calculating Frequencies.

# %%
IPA_syllables['Cumulative FREQcount'] = None
IPA_syllables

# %%
for index, row in IPA_syllables.iterrows():
    syllable = row['Syllables']
    contains_syllable = subtlex_IPA['Syllables'].str.contains(syllable, na=False, regex=False)
    cumulative_FREQcount = subtlex_IPA[contains_syllable]['FREQcount'].sum()
    IPA_syllables.at[index,'Cumulative FREQcount'] = cumulative_FREQcount
# %%

# Save IPA_syllables to a CSV file
IPA_syllables.to_csv(f'IPA_individual_syllable_frequencies_{tag}.csv', index=False)

# %% [markdown]
# 3. Calculate minimum syllable frequencies for all MOUS study words

# %%

IPA_syllables  = pd.read_csv(f'IPA_individual_syllable_frequencies_{tag}.csv')
# Read the file
file_path = '/home/neel/Desktop/MOUS_hierarchical-representations/stimuli.txt'
with open(file_path, 'r', encoding='utf-8') as file:
    lines = file.readlines()

# Process the text
words = set()
for line in lines:
    # Remove the numbers and lowercase the words
    line = ''.join([i for i in line if not i.isdigit()]).lower()
    # Split the line into words and add them to the set
    words.update(line.split())

# Convert the set to a list and create a dataframe
unique_words = list(words)
mous_words_df = pd.DataFrame(unique_words, columns=['Word'])

#merge with subtlex
mous_ipa = pd.merge(mous_words_df, subtlex, on='Word', how='inner')
mous_ipa = mous_ipa[['Word','IPA','Syllables']]
mous_ipa.to_csv(f'MOUS_IPA_transcriptions_{tag}.csv', index=False)



# %%
for index, row in mous_ipa.iterrows():
    word = row['Word']
    transcription = row['Syllables']
    print(f'{word} in IPA is {transcription}')
    
    # Split transcription into syllables
    transcription_syllables = transcription.split(" - ")
    
    longest_matches = {}
    for syllable in transcription_syllables:
        # Find rows in IPA_syllables where 'Syllables' is exactly the current syllable
        matches = IPA_syllables[IPA_syllables['Syllables'] == syllable]
        
        # Find the longest match (though in this case, it will be the same as the syllable)
        if not matches.empty:
            longest_match = matches.iloc[0]['Syllables']
            longest_matches[syllable] = longest_match
    
    for syllable in transcription_syllables:
        match = longest_matches.get(syllable, "")
        print(f'Syllable: {syllable}, Longest match: {match}')

# %%
# Iterate over each row in mous_ipa
for index, row in mous_ipa.iterrows():
    word = row['Word']
    transcription = row['Syllables'].strip()
    print(f"{word} in IPA is {transcription}")
    
    # Split transcription into syllables and strip whitespace
    transcription_syllables = [syllable.strip() for syllable in transcription.split(" - ")]
    
    freq_counts = []  # List to store Cumulative FREQcount values
    for syllable in transcription_syllables:
        # Find the row in IPA_syllables where 'Syllables' equals the current syllable
        match = IPA_syllables[IPA_syllables['Syllables'].str.strip() == syllable]
        
        if not match.empty:
            # Get the 'Cumulative FREQcount' value
            freq_count = match.iloc[0]['Cumulative FREQcount']
            freq_counts.append(freq_count)
        else:
            # If no match is found, append 0 or None
            freq_counts.append(0)
            print(f"No match found for syllable: '{syllable}'")
    
    # Print the word and the array of Cumulative FREQcount values
    print(f"Word: '{word}', Cumulative FREQcounts: {freq_counts}")

# %%
# Initialize lists to store min, max, and mean frequency counts
min_freq_counts = []
max_freq_counts = []
mean_freq_counts = []

# Iterate over each row in mous_ipa
for index, row in mous_ipa.iterrows():
    word = row['Word']
    transcription = row['Syllables'].strip()
    print(f"{word} in IPA is {transcription}")
    
    # Split transcription into syllables and strip whitespace
    transcription_syllables = [syllable.strip() for syllable in transcription.split(" - ")]
    
    freq_counts = []  # List to store Cumulative FREQcount values
    for syllable in transcription_syllables:
        # Find the row in IPA_syllables where 'Syllables' equals the current syllable
        match = IPA_syllables[IPA_syllables['Syllables'].str.strip() == syllable]
        
        if not match.empty:
            # Get the 'CumulativeFREQcount' value
            freq_count = match.iloc[0]['Cumulative FREQcount']
            freq_counts.append(freq_count)
        else:
            # If no match is found, append 0
            freq_counts.append(0)
            print(f"No match found for syllable: '{syllable}'")
    
    # Calculate min, max, and mean of freq_counts
    if freq_counts:
        min_freq = min(freq_counts)
        max_freq = max(freq_counts)
        mean_freq = sum(freq_counts) / len(freq_counts)
    else:
        min_freq = max_freq = mean_freq = 0
    
    # Append the results to the lists
    min_freq_counts.append(min_freq)
    max_freq_counts.append(max_freq)
    mean_freq_counts.append(mean_freq)
    
    # Print the word and the array of Cumulative FREQcount values
    print(f"Word: '{word}', Cumulative FREQcounts: {freq_counts}")

# Add the min, max, and mean frequency counts as new columns to mous_ipa
mous_ipa['Min_Freq_Count'] = min_freq_counts
mous_ipa['Max_Freq_Count'] = max_freq_counts
mous_ipa['Mean_Freq_Count'] = mean_freq_counts

# %%
mous_ipa.to_csv(f'MOUS_IPA_SyllableFrequencies_{tag}.csv')


# %%
mous_ipa

# %%
#Generate regressor files for every subject.

# %%

source = Path('/media/neel/MOUS/MOUS/MOUS/SynologyDrive/source')
for subject in source.iterdir():
    if subject.name.startswith('sub-A'):
        events = subject / 'func' / f'{subject.name}_transcription.csv'
        events_df = pd.read_csv(events)
        events_df = events_df.rename(columns={'Transcription': 'Word'})
        combined_events = pd.merge(events_df, mous_ipa, on='Word')
        combined_events = combined_events.sort_values(by='AlignOnset', ascending=True)
        combined_events.to_csv(str(events.parent / f'{subject.name}_IPA_syllable_frequency_{tag}.csv'))

# %% [markdown]
# Generate histograms of syllable frequencies.

# # %%
# celex_syllable_frequencies = pd.read_csv('/home/neel/Desktop/MOUS_hierarchical-representations/syllable_counts.csv')
# celex_syllable_frequencies.rename(columns={'Unnamed: 0': 'Syllable'}, inplace=True)
# celex_syllable_frequencies['Lg10'] = np.log10(celex_syllable_frequencies['Count'])
# celex_syllable_frequencies['Lg10'] = celex_syllable_frequencies['Lg10'].replace(-np.inf, 0)
# #drop values with Count = 0
# celex_syllable_frequencies = celex_syllable_frequencies[celex_syllable_frequencies['Count'] != 0]
# celex_syllable_frequencies

# # %%
# #histogram of celex_syllable_frequencies['Count']
# import matplotlib.pyplot as plt

# plt.hist(celex_syllable_frequencies['Lg10'].dropna(), bins=20, edgecolor='black')
# plt.xlabel('Lg10 Syllable Frequency')
# plt.ylabel('Occurrence')
# plt.title('Histogram of CELEX Syllable Frequencies')
# plt.grid(axis='y', linestyle='--', alpha=0.7)
# plt.show()


# # %%
# conflict_mapping_dict

# # %%
# IPA_syllables = pd.read_csv(f'IPA_individual_syllable_frequencies_{tag}.csv')
# IPA_syllables

# # %%
# IPA_syllables['Lg10'] = np.log10(IPA_syllables['Cumulative FREQcount'])
# IPA_syllables['Lg10'] = IPA_syllables['Lg10'].replace(-np.inf, 0)
# IPA_syllables = IPA_syllables[IPA_syllables['Cumulative FREQcount'] != 0]
# IPA_syllables

# # %%
# plt.hist(IPA_syllables['Lg10'].dropna(), bins=20, edgecolor='black')
# plt.xlabel('Lg10 IPA Syllable Frequency')
# plt.ylabel('Occurrence')
# plt.title('Histogram of IPA Syllable Frequencies')
# plt.grid(axis='y', linestyle='--', alpha=0.7)
# plt.show()

# # %%


# # %%
# #turn conflict_mapping_dict into a dataframe, with CELEX as the index and the values as a list in the second column
# conflict_mapping_df = pd.DataFrame(conflict_mapping_dict.items(), columns=['CELEX', 'Possible IPA Mappings'])
# conflict_mapping_df

# # %%
# conflict_mapping_df['Sum of IPA FREQcounts'] = np.nan
# for index, row in conflict_mapping_df.iterrows():
#     sum_FREQcount = 0
#     for IPA_syllable in row['Possible IPA Mappings']:
#         frequency = IPA_syllables[IPA_syllables['Syllables'] == IPA_syllable]['Cumulative FREQcount']
#         if not frequency.empty:
#             sum_FREQcount += frequency.iloc[0]
#     conflict_mapping_df.at[index, 'Sum of IPA FREQcounts'] = sum_FREQcount
    


# # %%

# conflict_mapping_df['Lg10 Sum of IPA FREQcounts'] = np.log10(conflict_mapping_df['Sum of IPA FREQcounts'])
# conflict_mapping_df['Lg10 Sum of IPA FREQcounts'] = conflict_mapping_df['Lg10 Sum of IPA FREQcounts'].replace(-np.inf, 0)
# conflict_mapping_df = conflict_mapping_df[conflict_mapping_df['Sum of IPA FREQcounts'] != 0]
# conflict_mapping_df

# # %%
# plt.hist(conflict_mapping_df['Lg10 Sum of IPA FREQcounts'].dropna(), bins=20, edgecolor='black')
# plt.xlabel('Lg10 Sum of IPA FREQcounts')
# plt.ylabel('Occurrence')
# plt.title('Histogram of CELEX-IPA Neighbor Syllable Frequencies')
# plt.grid(axis='y', linestyle='--', alpha=0.7)
# plt.show()


