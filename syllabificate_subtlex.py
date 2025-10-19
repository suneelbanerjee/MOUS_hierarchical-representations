import pandas as pd
from main import syllabificate_word
import re

subtlex = pd.read_excel('subtlex_v2_cleaned_no_drop3.xlsx')
#print(subtlex)


def is_valid(word):
    return isinstance(word, str) and re.fullmatch(r"[a-zA-Zäëïöüáéíóúâêîôûç\-']+", word)

invalid_words = []
error_words = []

for i, row in subtlex.iterrows():
    word = row['Word']
    if is_valid(word):
        try:
            syll = syllabificate_word(word, alg='n', language='nl')
            #print(f"Syllabifying {word}, result = {syll}")
        except Exception as e:
            error_words.append((word, str(e)))
            syll = ''
    else:
        invalid_words.append(word)
        syll = ''
    subtlex.loc[i, 'Syllabification'] = syll
    
#subtlex.to_csv('subtlex_syllabified.csv')
print("Invalid words (bad characters):", invalid_words[:10])
#['hè', 'carrière', 'scène', 'señor', 'èèn', 'okè', 'première', 'crème', 'scènes', 'voilà']
print("Words that caused exceptions:", error_words[:10])
# Save invalid words to a CSV
pd.DataFrame({'Invalid Words': invalid_words}).to_csv('invalid_words.csv', index=False)

# Save error words to a CSV
pd.DataFrame({'Word': [e[0] for e in error_words], 'Error': [e[1] for e in error_words]}).to_csv('error_words.csv', index=False)
pd.DataFrame({'Word': [f[0] for f in invalid_words], 'Error': [f[1] for f in invalid_words]}).to_csv('error_words.csv', index=False)
