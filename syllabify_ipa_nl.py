import re

# Define a set of IPA vowels in Dutch
IPA_VOWELS = "ɪɛʏɔəɑieːyːøːoːaːuɛiœyɔu"

# Define a set of stress markers
STRESS_MARKERS = "ˈˌ"

def syllabify_ipa(transcription):
    # Treat stress markers as part of the transcription
    transcription = transcription.replace('ˈ', '|ˈ').replace('ˌ', '|ˌ')
    
    # Preserve all characters in the IPA transcription, but break based on vowel boundaries
    syllable_pattern = re.compile(f"([^{IPA_VOWELS}]*[{IPA_VOWELS}]+[^{IPA_VOWELS}]*)")
    
    # Find all syllables
    syllables = syllable_pattern.findall(transcription)
    
    # Join syllables with a hyphen or a syllable boundary marker
    return ' - '.join(syllables)

def main():
    # Sample words and their IPA transcriptions
    words_ipa = {
        "irritante": "ˌɪɾritˈɑntə",
        "wegliep": "ʋˈɛɣlˌip",
        "gingen": "ɣˈɪŋən",
        "deuren": "dˈøːrən",
        "manke": "mˈɑŋkə",
        "elektronisch": "ˌɛlɛktrˈonis",
        "woonplaats": "ʋˈoːnplaːts"
    }

    for word, ipa_transcription in words_ipa.items():
        syllabified = syllabify_ipa(ipa_transcription)
        print(f"{word}\t{syllabified}")

if __name__ == "__main__":
    main()