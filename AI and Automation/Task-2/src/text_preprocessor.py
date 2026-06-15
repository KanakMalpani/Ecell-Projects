"""
NLTK-based text preprocessor — replaces hardcoded word filters.

Pipeline:
  1. Normalize whitespace and lowercase
  2. Tokenize with NLTK word_tokenize
  3. Remove punctuation-only tokens
  4. Remove English stop words (NLTK corpus — not a hardcoded list)
  5. Lemmatize tokens with WordNet

Use preprocess() for full normalization, or extract_keywords() when you
only need meaningful terms (e.g. query matching in the RAG fallback).
"""

from __future__ import annotations

import re
from functools import lru_cache

import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize

# Structural boilerplate (page headers, doc metadata) — regex only, not word filters
_BOILERPLATE_LINE_PATTERNS = [
    re.compile(r"^Page \d+ of \d+\s*$", re.MULTILINE | re.IGNORECASE),
    re.compile(r"^Confidential\s*[-|]\s*Internal Use Only\s*$", re.MULTILINE | re.IGNORECASE),
    re.compile(r"^\s*Document ID:.*$", re.MULTILINE | re.IGNORECASE),
    re.compile(r"^\s*Version \d+\.\d+.*$", re.MULTILINE | re.IGNORECASE),
    re.compile(r"^\s*Effective:.*$", re.MULTILINE | re.IGNORECASE),
    re.compile(r"^\s*Last Updated:.*$", re.MULTILINE | re.IGNORECASE),
    re.compile(r"^\s*Owner:.*$", re.MULTILINE | re.IGNORECASE),
]

_WHITESPACE_PATTERN = re.compile(r"\n{3,}")
_MULTISPACE_PATTERN = re.compile(r"[ \t]{2,}")
_TOKEN_PATTERN = re.compile(r"^[a-z0-9][a-z0-9\-']*$")


def _ensure_nltk_data() -> None:
    """Download NLTK corpora on first use (punkt, stopwords, wordnet)."""
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
    """Load English stop words from NLTK (cached after first call)."""
    _ensure_nltk_data()
    return frozenset(stopwords.words("english"))


class TextPreprocessor:
    """
    Configurable NLP preprocessor backed by NLTK.

    remove_stopwords: strip common English words (the, is, at, …)
    lemmatize: reduce words to base form (running → run)
    min_token_length: drop very short tokens after tokenization
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

    def strip_boilerplate(self, text: str) -> str:
        """Remove structural PDF/header lines before token-level processing."""
        cleaned = text.replace("\r\n", "\n").replace("\r", "\n")
        for pattern in _BOILERPLATE_LINE_PATTERNS:
            cleaned = pattern.sub("", cleaned)
        cleaned = _MULTISPACE_PATTERN.sub(" ", cleaned)
        cleaned = _WHITESPACE_PATTERN.sub("\n\n", cleaned)
        return cleaned.strip()

    def tokenize(self, text: str) -> list[str]:
        """Split text into normalized word tokens."""
        return word_tokenize(text.lower())

    def filter_tokens(self, tokens: list[str]) -> list[str]:
        """
        Keep only meaningful tokens using NLTK stop words (not hardcoded lists).

        Drops stop words, punctuation-only tokens, and tokens shorter than min_token_length.
        """
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
        """Reduce tokens to dictionary form (e.g. policies → policy)."""
        if not self.lemmatize:
            return tokens
        return [self._lemmatizer.lemmatize(token) for token in tokens]

    def preprocess(self, text: str) -> str:
        """
        Full pipeline: strip boilerplate → tokenize → filter → lemmatize → rejoin.

        Returns a single space-separated string ready for embedding or TF-IDF.
        """
        if not text or not isinstance(text, str):
            return ""

        normalized = self.strip_boilerplate(text)
        tokens = self.tokenize(normalized)
        tokens = self.filter_tokens(tokens)
        tokens = self.lemmatize_tokens(tokens)
        return " ".join(tokens).strip()

    def extract_keywords(self, text: str) -> set[str]:
        """
        Return meaningful keywords for matching (stop words already removed).

        Used instead of hardcoded rules like len(token) > 3.
        """
        normalized = self.strip_boilerplate(text)
        tokens = self.tokenize(normalized)
        tokens = self.filter_tokens(tokens)
        tokens = self.lemmatize_tokens(tokens)
        return set(tokens)


_default_preprocessor: TextPreprocessor | None = None


def get_preprocessor(
    *,
    remove_stopwords: bool = True,
    lemmatize: bool = True,
    min_token_length: int = 2,
) -> TextPreprocessor:
    """Return a shared TextPreprocessor instance (lazy singleton)."""
    global _default_preprocessor
    if _default_preprocessor is None:
        _default_preprocessor = TextPreprocessor(
            remove_stopwords=remove_stopwords,
            lemmatize=lemmatize,
            min_token_length=min_token_length,
        )
    return _default_preprocessor
