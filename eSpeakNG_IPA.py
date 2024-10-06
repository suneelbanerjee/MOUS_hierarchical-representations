import subprocess
import tempfile
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

def process_word(word):
    """
    Process a single word with espeak-ng and return its phonetic transcription as a single string.
    """
    try:
        # Create a temporary file to store phoneme output
        with tempfile.NamedTemporaryFile(mode='r+', delete=False) as temp_file:
            phoneme_filename = temp_file.name

        # Command to run eSpeak NG with phoneme output written to a file
        command = ['espeak-ng', '-v', 'nl', '--ipa', f'--phonout={phoneme_filename}', '-q', word]

        # Run the command for this word
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        if result.returncode != 0:
            print(f"Error processing word '{word}': {result.stderr}")
            return word, 'error'

        # Read the full phonetic transcription output from the file
        with open(phoneme_filename, 'r', encoding='utf-8') as f:
            transcription = f.read().strip()

        return word, transcription

    except Exception as e:
        print(f"An error occurred while processing word '{word}': {e}")
        return word, 'error'

    finally:
        # Clean up the temporary file
        os.remove(phoneme_filename)

def get_phonetic_transcriptions_parallel(words, max_workers=8):
    """
    Function to get the IPA phonetic transcription for a list of words using parallel processing.
    Each word is processed individually in parallel to avoid issues with espeak-ng batch processing.
    Input:
        words (list): A list of words to generate IPA transcriptions for.
        max_workers (int): The number of parallel workers.
    Output:
        transcriptions (dict): A dictionary with words as keys and IPA transcriptions as values.
    """
    transcriptions = {}

    # Use ThreadPoolExecutor for parallel processing
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit tasks to process each word individually in parallel
        futures = {executor.submit(process_word, word): word for word in words}

        # Collect results as they are completed
        for future in as_completed(futures):
            word, transcription = future.result()
            transcriptions[word] = transcription

    return transcriptions


# Example usage (to be run from an external script or Jupyter notebook)
# from eSpeakNG_IPA import get_phonetic_transcriptions_parallel
# words = ["toen", "de", "barkeeper", "die", "irritante", "klant"]
# ipa_transcriptions = get_phonetic_transcriptions_parallel(words, max_workers=8)
# print(ipa_transcriptions)