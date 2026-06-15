"""
NLTK-based text preprocessor — replaces hardcoded word filters.

Pipeline:
  1. Strip HTML tags and entities
  2. Tokenize with NLTK word_tokenize
  3. Remove English stop words (NLTK corpus — not a hardcoded list)
  4. Lemmatize with WordNet
  5. Rejoin into clean text for TF-IDF / model input

SEC boilerplate phrases (table of contents, page numbers) are still removed
via regex because they are document structure, not vocabulary filters.
"""

from __future__ import annotations

import re
from functools import lru_cache

import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize

# Structural SEC/filing boilerplate — regex patterns, not vocabulary filters
BOILERPLATE_PATTERNS = (
    r"table of contents",
    r"forward[- ]looking statements",
    r"item\s+\d+[a-z]?\.?",
    r"page\s+\d+\s+of\s+\d+",
    r"sec\.gov",
    r"united states securities and exchange commission",
)

_HTML_TAG_PATTERN = re.compile(r"<[^>]+>")
_HTML_ENTITY_PATTERN = re.compile(r"&#\d+;")
_NOISE_PATTERN = re.compile(r"[^a-z0-9\s\.\,\;\:\-\%\$\(\)]+", re.IGNORECASE)
_WHITESPACE_PATTERN = re.compile(r"\s+")
_TOKEN_PATTERN = re.compile(r"^[a-z0-9][a-z0-9\-']*$")


def _ensure_nltk_data() -> None:
    """Download NLTK corpora on first use."""
    lookups = {
        "punkt": "tokenizers/punkt",
        "punkt_tab": "tokenizers/punkt_tab",
        "stopwords": "corpora/stopwords",
        "wordnet": "corpora/wordnet",
        "omw-1.4": "corpora/omw-1.4",
    }
    for package, path in lookups.items():
        try:
            nltk.data.find(path)
        except LookupError:
            nltk.download(package, quiet=True)


@lru_cache(maxsize=1)
def _get_stop_words() -> frozenset[str]:
    """Load English stop words from NLTK (cached)."""
    _ensure_nltk_data()
    return frozenset(stopwords.words("english"))


class TextPreprocessor:
    """
    Configurable NLP preprocessor for 10-K filing text.

    remove_stopwords: strip common English words via NLTK
    lemmatize: reduce inflected forms (losses → loss)
    min_token_length: minimum token length after tokenization
    """

    def __init__(
        self,
        *,
        remove_stopwords: bool = True,
        lemmatize: bool = True,
        min_token_length: int = 2,
    ) -> None:
        _ensure_nltk_data()
        self.remove_stopwords = remove_stopwords
        self.lemmatize = lemmatize
        self.min_token_length = min_token_length
        self._stop_words = _get_stop_words()
        self._lemmatizer = WordNetLemmatizer()

    def strip_markup(self, text: str) -> str:
        """Remove HTML tags, entities, and non-text characters."""
        cleaned = text.lower()
        cleaned = _HTML_TAG_PATTERN.sub(" ", cleaned)
        cleaned = _HTML_ENTITY_PATTERN.sub(" ", cleaned)
        cleaned = _NOISE_PATTERN.sub(" ", cleaned)
        for pattern in BOILERPLATE_PATTERNS:
            cleaned = re.sub(pattern, " ", cleaned, flags=re.IGNORECASE)
        return _WHITESPACE_PATTERN.sub(" ", cleaned).strip()

    def tokenize(self, text: str) -> list[str]:
        return word_tokenize(text.lower())

    def filter_tokens(self, tokens: list[str]) -> list[str]:
        """Remove stop words and noise tokens using NLTK (not hardcoded word lists)."""
        filtered: list[str] = []
        for token in tokens:
            if not _TOKEN_PATTERN.match(token):
                continue
            if len(token) < self.min_token_length:
                continue
            if self.remove_stopwords and token in self._stop_words:
                continue
            filtered.append(token)
        return filtered

    def lemmatize_tokens(self, tokens: list[str]) -> list[str]:
        if not self.lemmatize:
            return tokens
        return [self._lemmatizer.lemmatize(token) for token in tokens]

    def preprocess(self, text: str) -> str:
        """Full cleaning pipeline for filing text."""
        if not text or not isinstance(text, str):
            return ""

        normalized = self.strip_markup(text)
        tokens = self.tokenize(normalized)
        tokens = self.filter_tokens(tokens)
        tokens = self.lemmatize_tokens(tokens)
        return " ".join(tokens).strip()


_default_preprocessor: TextPreprocessor | None = None


def get_preprocessor() -> TextPreprocessor:
    """Return shared TextPreprocessor instance."""
    global _default_preprocessor
    if _default_preprocessor is None:
        _default_preprocessor = TextPreprocessor()
    return _default_preprocessor
