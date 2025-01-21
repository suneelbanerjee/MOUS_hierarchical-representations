import re

# Updated list of IPA vowels in Dutch, including diphthongs
IPA_VOWELS = [
    # Long vowels
    'aː', 'eː', 'iː', 'oː', 'uː', 'øː', 'yː',
    # Short vowels
    'ɑ', 'ɛ', 'ɪ', 'ɔ', 'ʏ', 'ə', 'œ', 'ɵ',  # Added 'ɵ' here
    # Diphthongs
    'ɛi', 'œy', 'ɑu', 'ɔu', 'ɛu',
    # Additional vowels
    'i', 'e', 'a', 'o', 'u', 'y', 'ø',
    # Additional diphthongs
    'ɪː', 'ʌʊ', 'ʌu', 'aɪ', 'aʊ', 'ɔɪ',
    # Rare or dialectal vowels (add as needed)
]

# Define stress markers
STRESS_MARKERS = ['ˈ', 'ˌ']

# Define permissible onset clusters in Dutch IPA
ONSETS = [
    ('p',), ('t',), ('k',), ('b',), ('d',), ('f',), ('v',), ('s',), ('z',),
    ('ʃ',), ('ʒ',), ('m',), ('n',), ('l',), ('r',), ('j',), ('ʋ',), ('ɣ',),
    # Common two-consonant clusters
    ('s', 'p'), ('s', 't'), ('s', 'k'), ('s', 'f'), ('s', 'x'),
    ('p', 'l'), ('p', 'r'), ('t', 'r'), ('k', 'l'), ('k', 'r'),
    ('b', 'l'), ('b', 'r'), ('d', 'r'), ('ɣ', 'l'), ('ɣ', 'r'),
    ('f', 'l'), ('f', 'r'), ('v', 'l'), ('v', 'r'),
    ('s', 'l'), ('s', 'm'), ('s', 'n'),
    ('ʃ', 'r'), ('ʃ', 'l'),
    # Three-consonant clusters
    ('s', 'p', 'l'), ('s', 'p', 'r'), ('s', 't', 'r'), ('s', 'k', 'l'), ('s', 'k', 'r'),
    # Add more clusters as needed
]

# Special cases to keep intact (e.g., "hɛɪt")
SPECIAL_UNITS = ['hɛɪt']

def tokenize_transcription(transcription):
    # Combine special units, vowels, and stress markers for tokenization
    sorted_symbols = sorted(SPECIAL_UNITS + IPA_VOWELS + STRESS_MARKERS, key=len, reverse=True)
    tokens = []
    i = 0
    while i < len(transcription):
        # Attempt to match special units, vowels, or stress markers
        matched = False
        for symbol in sorted_symbols:
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
    # Remove stress markers for processing
    transcription_clean = transcription.replace('ˈ', '').replace('ˌ', '')

    # Tokenize the transcription
    tokens = tokenize_transcription(transcription_clean)

    # Identify vowel positions (includes special units)
    vowel_positions = [i for i, token in enumerate(tokens) if token in IPA_VOWELS or token in SPECIAL_UNITS]

    syllables = []
    start = 0

    for idx, vowel_pos in enumerate(vowel_positions):
        # Determine the end position of the syllable
        if idx + 1 < len(vowel_positions):
            next_vowel_pos = vowel_positions[idx + 1]
            # Consonants between vowels
            inter_consonants = tokens[vowel_pos + 1:next_vowel_pos]
            # Apply Maximal Onset Principle
            coda, onset = maximal_onset(inter_consonants)
            # Build the syllable
            syllable = tokens[start:vowel_pos + 1] + coda
            syllables.append(''.join(syllable))
            # Start index for next syllable
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
        "indruk": "ɪndrɵk",
        "clowns": "klˈɔwns",
        "boskruid": "bˈɵskrœyt",
        "drukknop": "drˈɵknɔp",
        "irritante": "ˌɪɾritˈɑntə",
        "wegliep": "ʋˈɛɣlˌip",
        "gingen": "ɣˈɪŋən",
        "deuren": "dˈøːrən",
        "manke": "mˈɑŋkə",
        "elektronisch": "ˌeːlɛktrˈoːnis",
        "woonplaats": "ʋˈoːnplaːts",
        "koppigheid": "kɔpəxhɛɪt"
    }

    for word, ipa_transcription in words_ipa.items():
        syllabified = syllabify_ipa(ipa_transcription)
        print(f"{word}\t{syllabified}")

if __name__ == "__main__":
    main()