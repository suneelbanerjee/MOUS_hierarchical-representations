import pandas as pd
from eSpeakNG_IPA import get_phonetic_transcriptions_parallel
from syllabify_ipa_nl import syllabify_ipa
df = pd.read_excel('/home/neel/Desktop/MOUS_hierarchical-representations/subtlex_v2_cleaned_no_drop2.xlsx')

# Now, run the main function with a list of words
df['IPA'] = get_phonetic_transcriptions_parallel(list(df['Word']),max_workers=8)

df['Syllables'] = df['IPA'].apply(lambda x: syllabify_ipa(x))
#df.drop(columns = ['CDcount', 'FREQlow', 'CDlow','FREQlemma'], inplace = True)
#save the dataframe to a csv file
df.to_csv('/home/neel/Desktop/MOUS_hierarchical-representations/subtlex_v2_IPA_syllables.csv', index = False)
df = pd.read_csv('/home/neel/Desktop/MOUS_hierarchical-representations/subtlex_v2_IPA_syllables.csv')