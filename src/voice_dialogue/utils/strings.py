import re

__all__ = ('remove_emojis', 'convert_uppercase_words_to_lowercase', 'convert_comma_separated_numbers',)

emoji_pattern = re.compile(
    "["
    u"\U0001F600-\U0001F64F"  # emoticons
    u"\U0001F300-\U0001F5FF"  # symbols & pictographs
    u"\U0001F680-\U0001F6FF"  # transport & map symbols
    u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
    u"\U0001F900-\U0001F9FF"  # supplemental symbols and pictographs
    "]+", re.UNICODE
)

stars_pattern = re.compile(r'\*[\w\s]+\*', re.UNICODE)
bracket_pattern = re.compile(r'\(*[\w\s]+\)', re.UNICODE)


def remove_emojis(data):
    text = re.sub(stars_pattern, '', data)
    text = re.sub(bracket_pattern, '', text)
    text = re.sub(emoji_pattern, '', text).strip()
    return text.strip()


def convert_uppercase_words_to_lowercase(text):
    uppercase_words = re.findall(r'\b[A-Z]+\b', text)

    for word in uppercase_words:
        text = text.replace(word, word.lower())

    return text


def convert_comma_separated_numbers(text):
    comma_separated_numbers = re.findall(r'\b\d{1,3}(,\d{3})+\b', text)

    for number in comma_separated_numbers:
        text = text.replace(number, number.replace(',', ''))

    return text
