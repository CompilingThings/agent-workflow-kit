"""Tiny sample project for the agent workflow trial."""


def word_count(text: str) -> int:
    """Return the number of whitespace-separated words in text."""
    return len([word for word in text.split(" ") if word])
