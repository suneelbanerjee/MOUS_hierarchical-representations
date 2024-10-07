import re

# Define a list of IPA vowels in Dutch, including multi-character vowels
IPA_VOWELS = ['eː', 'oː', 'aː', 'øː', 'yː', 'ɛ', 'œ', 'ɪ', 'ʏ', 'ə', 'i', 'e', 'a', 'ɑ', 'o', 'ɔ', 'u', 'y', 'ø', 'ʌʊ', 'ɛɪ', 'œy', 'ʌʊ', 'ɪː']

# Define stress markers
STRESS_MARKERS = ['ˈ', 'ˌ']

# Define permissible onset clusters in Dutch IPA
# Each cluster is represented as a tuple of tokens
ONSETS = [
    ('p',), ('t',), ('k',), ('b',), ('d',), ('f',), ('v',), ('s',), ('z',), ('ʃ',), ('ʒ',),
    ('m',), ('n',), ('l',), ('r',), ('j',), ('ʋ',),
    ('s', 'p'), ('s', 't'), ('s', 'k'),
    ('p', 'l'), ('p', 'r'), ('t', 'r'), ('k', 'l'), ('k', 'r'),
    ('b', 'l'), ('b', 'r'), ('d', 'r'), ('ɣ', 'l'), ('ɣ', 'r'),
    ('f', 'l'), ('f', 'r'),
    ('s', 'l'), ('s', 'm'), ('s', 'n'),
    # Add more clusters if necessary
]

def tokenize_transcription(transcription):
    # Sort vowels by length in descending order to match multi-character vowels first
    sorted_vowels = sorted(IPA_VOWELS + STRESS_MARKERS, key=len, reverse=True)
    tokens = []
    i = 0
    while i < len(transcription):
        # Check for multi-character vowels or stress markers
        matched = False
        for symbol in sorted_vowels:
            if transcription[i:i+len(symbol)] == symbol:
                tokens.append(symbol)
                i += len(symbol)
                matched = True
                break
        if not matched:
            # Single character (consonant)
            tokens.append(transcription[i])
            i += 1
    return tokens

def maximal_onset(inter_consonants):
    # Find the maximal onset cluster permissible in Dutch
    for i in range(len(inter_consonants)):
        onset_candidate = tuple(inter_consonants[i:])
        if onset_candidate in ONSETS:
            coda = inter_consonants[:i]
            onset = inter_consonants[i:]
            return coda, onset
    # If no permissible onset found, assign all to coda
    return inter_consonants, []

def syllabify_ipa(transcription):
    # Tokenize the transcription
    tokens = tokenize_transcription(transcription)
    
    # Identify vowel positions
    vowel_positions = [i for i, token in enumerate(tokens) if token in IPA_VOWELS]
    
    syllables = []
    start = 0
    
    for idx, vowel_pos in enumerate(vowel_positions):
        # Determine the end position of the syllable
        if idx + 1 < len(vowel_positions):
            next_vowel_pos = vowel_positions[idx + 1]
            # Consonants between vowels (excluding stress markers)
            inter_consonants = [token for token in tokens[vowel_pos + 1:next_vowel_pos] if token not in STRESS_MARKERS]
            # Apply Maximal Onset Principle
            coda, onset = maximal_onset(inter_consonants)
            # Build the syllable
            syllable = tokens[start:vowel_pos + 1] + coda
            syllables.append(''.join(syllable))
            # Include any stress markers between vowels in the onset of the next syllable
            start = vowel_pos + 1 + len(coda)
        else:
            # Last syllable
            syllable = tokens[start:]
            syllables.append(''.join(syllable))
    
    # Join syllables with ' - '
    return ' - '.join(syllables)
    
def main():
    # Sample words and their IPA transcriptions
    words_ipa = {
        "irritante": "ˌɪɾritˈɑntə",
        "wegliep": "ʋˈɛɣlˌip",
        "gingen": "ɣˈɪŋən",
        "deuren": "dˈøːrən",
        "manke": "mˈɑŋkə",
        "elektronisch": "ˌeːlɛktrˈoːnis",
        "woonplaats": "ʋˈoːnplaːts"
    }

    for word, ipa_transcription in words_ipa.items():
        syllabified = syllabify_ipa(ipa_transcription)
        print(f"{word}\t{syllabified}")

if __name__ == "__main__":
    main()