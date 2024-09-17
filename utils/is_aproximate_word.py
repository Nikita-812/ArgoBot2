import csv
import difflib
from internet_parsers.towns import towns


def is_word_approx_in_string(word: str, cutoff: float = 0.7) -> str:
    with open("clean_name_links.csv", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter=',')

        for row in reader:
            goods_name = row[0]  # GOODS_NAME is the first column
            goods_url = row[1]  # GOODS_URL is the second column

            words_in_string = word.lower().split()
            goods_name = goods_name.lower()

            for string_word in words_in_string:
                for goods_word in goods_name.split():
                    if string_word not in towns:
                        close_matches = difflib.get_close_matches(string_word, [goods_word], n=1, cutoff=cutoff)
                        if close_matches:
                            return f"Для более подробной информации, пожалуйста, посетите страницу продукта: {goods_url}"
    return ''


def is_town_approx_in_string(word: str) -> str:
    words_in_string = word.split()
    best_match = None
    highest_similarity = 0

    for string_word in words_in_string:
        for town in towns:
            similarity = difflib.SequenceMatcher(None, string_word, town).ratio()
            if similarity > highest_similarity:
                best_match = town
                highest_similarity = similarity

    return best_match


if __name__ == '__main__':
    query = ('расскажи про полимедел')
    result = is_word_approx_in_string(query)
    print(result)
