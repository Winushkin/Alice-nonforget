def check_line(line):
    negative_words = ["нет", "ни", "не"]
    negatives_count = line.lower().count("не")
    if negatives_count % 2 != 0:
        for word in negative_words:
            if word in line.lower():
                return False
        return True
    return True


def words_in_string(words: list, s: str) -> str:
    for word in words:
        if word in s:
            return word
    return ""
