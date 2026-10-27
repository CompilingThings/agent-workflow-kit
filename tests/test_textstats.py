from textstats import word_count


def test_word_count_counts_words():
    assert word_count("one two  three") == 3


def test_word_count_empty():
    assert word_count("") == 0
