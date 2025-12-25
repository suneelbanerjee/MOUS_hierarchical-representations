# %%
import sys
sys.path.append('/home/neel/Desktop/MOUS_hierarchical-representations/guslatho/syllabificator')
from syllabificator.main import syllabificate_word
import pandas as pd
import numpy as np


# %%
print(sys.executable)

# %%
subtlex = pd.read_excel('/home/neel/Desktop/MOUS_hierarchical-representations/subtlex_v2_cleaned_no_drop3.xlsx') #failing entries have already been dropped actually, despite filename

# %% [markdown]
# From master_table IPA.ipynb: Number of entries failing each criterion (independently):
# 
# 1) Invalid word pattern          : 153807
# 2) Exceeding length threshold    : 3055
# 3) Solely punctuation            : 37
# 4) SPEC with non-alphabetic chars: 106539
# 5) Single-letter + apostrophe    : 506
# 6) Entirely repeated characters  : 173
# 7) Triple consecutive letters    : 953
# 
# --- Final status counts ---
# Status
# keep    278061
# drop    159442

# %%
subtlex

# %%
subtlex['Word'] = subtlex['Word'].str.lower()
subtlex['Syllabification'] = ''

# %%
import re

def is_valid(word):
    return isinstance(word, str) and re.fullmatch(r"[a-zA-Zäëïöüáéíóúâêîôûç\-']+", word)

invalid_words = []
error_words = []

for i, row in subtlex.iterrows():
    word = row['Word']
    if is_valid(word):
        try:
            syll = syllabificate_word(word, alg='n', language='nl')
        except Exception as e:
            error_words.append((word, str(e)))
            syll = ''
    else:
        invalid_words.append(word)
        syll = ''
    subtlex.loc[i, 'Syllabification'] = syll

# %%
subtlex.to_csv("SUBTLEX-cleaned_guslatho-syllabificator.csv")

# %%


pd.Series(invalid_words).to_csv("invalid_words.csv", index=False)
pd.DataFrame(error_words, columns=["word", "error"]).to_csv("error_words.csv", index=False)


