import pickledb
import data

EN = "en"
CURSE = "我:sunny:死你的:horse:"
word_keys = {}
for key in data.word_keys.getall():
    word_keys = {**word_keys, **data.word_keys.get(key)}


def get_word(key: str, language: str):
    """
    Get the localization word, given word key and language
    """
    if key not in word_keys:
        return "LOCALIZATION KEY {} NOT FOUND FOR LANGUAGE {}".format(key, language)
    words = word_keys[key]

    # If the word doesn't exist, just show word in English
    if language not in words or words[language] == "":
        return words[EN]
    else:
        return words[language]
