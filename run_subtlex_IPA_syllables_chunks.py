import pandas as pd
from eSpeakNG_IPA import get_phonetic_transcriptions_parallel
from syllabify_ipa_nl import syllabify_ipa
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

chunk_size = 10000  # Adjust the chunk size as needed
df = pd.read_excel('/home/neel/Desktop/MOUS_hierarchical-representations/subtlex_v2_cleaned_no_drop2.xlsx')

output_file = '/home/neel/Desktop/MOUS_hierarchical-representations/subtlex_v3_IPA_syllables_ijfix2.csv'

# Initialize the output file with new columns
with open(output_file, 'w') as f:
    # Add 'IPA' and 'Syllables' columns to the header
    header = list(df.columns) + ['IPA', 'Syllables']
    pd.DataFrame(columns=header).to_csv(f, index=False)

# Process the DataFrame in chunks
for i in range(0, len(df), chunk_size):
    chunk = df.iloc[i:i + chunk_size].copy()  # Create a copy of the slice
    logging.info(f'Processing chunk {i // chunk_size + 1}')

    # Replace NaN values in 'Word' column with an empty string
    chunk['Word'] = chunk['Word'].fillna('')
    logging.info(f'NaN values replaced in chunk {i // chunk_size + 1}')

    # Get phonetic transcriptions for words in the chunk
    words = list(chunk['Word'])

    try:
        ipa_transcriptions = get_phonetic_transcriptions_parallel(words, max_workers=8)

        # Since ipa_transcriptions is a dictionary with words as keys,
        # we need to map the 'Word' column to this dictionary
        chunk['IPA'] = chunk['Word'].map(ipa_transcriptions)

        logging.info(f"IPA transcriptions received for chunk {i // chunk_size + 1}")

        # Apply syllabification on non-empty IPA transcriptions
        chunk['Syllables'] = chunk['IPA'].apply(lambda x: syllabify_ipa(x) if isinstance(x, str) and x else None)

        logging.info(f'Chunk {i // chunk_size + 1} IPA transcriptions and syllabifications preview:\n{chunk[["Word", "IPA", "Syllables"]].head()}')

    except Exception as e:
        logging.error(f"Error processing chunk {i // chunk_size + 1}: {e}")
        continue  # Skip the chunk if any error occurs

    # Append the processed chunk to the CSV file
    chunk.to_csv(output_file, mode='a', header=False, index=False)
    logging.info(f'Chunk {i // chunk_size + 1} successfully appended to {output_file}')