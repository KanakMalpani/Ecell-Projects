"""
NLTK-based text preprocessor for SEC 10-K filing text.

WHAT THIS FILE DOES
-------------------
Provides a reusable TextPreprocessor class that converts messy raw filing HTML
into clean, tokenized, lemmatized text suitable for TF-IDF vectorization.

WHY IT EXISTS
-------------
Raw 10-K text contains HTML tags, SEC boilerplate, page numbers, and noisy
characters. Hardcoding word filters is brittle; NLTK gives standard NLP tools
(stop words corpus, WordNet lemmatizer, punkt tokenizer) used across the
industry.

HOW IT FITS IN THE PIPELINE
---------------------------
  Used by preprocess.py via get_preprocessor() singleton.
  clean_text() → TextPreprocessor.preprocess() on every section.
  strip_markup() also used separately for keyword scoring (preserves phrases
  before aggressive token filtering).

Processing pipeline:
  raw HTML → strip_markup → tokenize → filter_tokens → lemmatize → join

KEY CONCEPTS FOR INTERVIEW
--------------------------
  1. Stop word removal: "the", "is", "of" add no discriminative signal for TF-IDF.
  2. Lemmatization vs stemming: lemmatization uses WordNet → valid words
     ("losses" → "loss"); more interpretable than Porter stemmer ("losses" → "loss").
  3. Boilerplate regex vs stop words: SEC structural phrases (table of contents,
     item numbers) removed by regex — they are document structure, not vocabulary.
  4. Singleton pattern (get_preprocessor): avoids re-downloading NLTK data and
     re-instantiating lemmatizer on every filing.
  5. Two cleaning depths: full preprocess for model; strip_markup only for
     keyword label scoring (keeps "going concern" intact as substring).
"""

from __future__ import annotations

import re
from functools import lru_cache

import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize

# ---------------------------------------------------------------------------
# Regex patterns for SEC/filing structural boilerplate
#
# These are NOT stop words — they are recurring document scaffolding that
# would inflate TF-IDF if left in. Removed before tokenization.
# ---------------------------------------------------------------------------
BOILERPLATE_PATTERNS = (
    r"table of contents",
    r"forward[- ]looking statements",
    r"item\s+\d+[a-z]?\.?",
    r"page\s+\d+\s+of\s+\d+",
    r"sec\.gov",
    r"united states securities and exchange commission",
)

# Compiled regex for performance — applied on every document
_HTML_TAG_PATTERN = re.compile(r"<[^>]+>")
_HTML_ENTITY_PATTERN = re.compile(r"&#\d+;")
_NOISE_PATTERN = re.compile(r"[^a-z0-9\s\.\,\;\:\-\%\$\(\)]+", re.IGNORECASE)
_WHITESPACE_PATTERN = re.compile(r"\s+")
_TOKEN_PATTERN = re.compile(r"^[a-z0-9][a-z0-9\-']*$")


# ---------------------------------------------------------------------------
# NLTK data bootstrap — lazy download on first use
# ---------------------------------------------------------------------------
def _ensure_nltk_data() -> None:
    """
    Download required NLTK corpora if not already present locally.

    Packages: punkt (tokenizer), stopwords, wordnet (lemmatizer), omw-1.4.
    quiet=True suppresses download progress spam in pipeline logs.
    """
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
    """
    Load English stop words from NLTK corpus (cached after first call).

    Returns immutable frozenset for O(1) membership checks during filtering.
    """
    _ensure_nltk_data()
    return frozenset(stopwords.words("english"))


# ---------------------------------------------------------------------------
# TextPreprocessor — configurable NLP cleaning pipeline
# ---------------------------------------------------------------------------
class TextPreprocessor:
    """
    Configurable NLP preprocessor for 10-K filing text.

    Designed as a pipeline of composable steps so each stage can be explained
    independently in an interview (tokenization theory, stop words, lemmatization).

    Attributes:
        remove_stopwords: If True, drop NLTK English stop words.
        lemmatize: If True, apply WordNet lemmatization to remaining tokens.
        min_token_length: Drop tokens shorter than this (default 2).
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
        """
        Remove HTML tags, entities, non-text characters, and SEC boilerplate.

        Lighter than full preprocess() — used when substring keyword matching
        needs intact phrases (e.g. "going concern", "may not").

        Args:
            text: Raw filing section text (may contain HTML).

        Returns:
            Lowercased, whitespace-normalized plain text.
        """
        cleaned = text.lower()
        cleaned = _HTML_TAG_PATTERN.sub(" ", cleaned)
        cleaned = _HTML_ENTITY_PATTERN.sub(" ", cleaned)
        cleaned = _NOISE_PATTERN.sub(" ", cleaned)
        for pattern in BOILERPLATE_PATTERNS:
            cleaned = re.sub(pattern, " ", cleaned, flags=re.IGNORECASE)
        return _WHITESPACE_PATTERN.sub(" ", cleaned).strip()

    def tokenize(self, text: str) -> list[str]:
        """
        Split normalized text into word tokens using NLTK punkt tokenizer.

        Args:
            text: Output of strip_markup() or similar normalized string.

        Returns:
            List of lowercase token strings.
        """
        return word_tokenize(text.lower())

    def filter_tokens(self, tokens: list[str]) -> list[str]:
        """
        Remove stop words, punctuation-like tokens, and overly short tokens.

        Uses _TOKEN_PATTERN to keep only alphanumeric/hyphen tokens suitable
        for TF-IDF vocabulary (filters pure punctuation artifacts).

        Args:
            tokens: Output of tokenize().

        Returns:
            Filtered token list.
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
        """
        Reduce inflected word forms to base lemmas via WordNet.

        Example: "losses" → "loss", "operating" → "operating" (or "operate"
        depending on POS — default noun lemmatization here).

        Args:
            tokens: Output of filter_tokens().

        Returns:
            Lemmatized token list (unchanged if self.lemmatize is False).
        """
        if not self.lemmatize:
            return tokens
        return [self._lemmatizer.lemmatize(token) for token in tokens]

    def preprocess(self, text: str) -> str:
        """
        Run the full cleaning pipeline: markup → tokenize → filter → lemmatize → join.

        This is the main entry point called by preprocess.clean_text().

        Args:
            text: Raw filing text (any section).

        Returns:
            Single space-separated string ready for TfidfVectorizer, or ""
            for empty/non-string input.
        """
        if not text or not isinstance(text, str):
            return ""

        normalized = self.strip_markup(text)
        tokens = self.tokenize(normalized)
        tokens = self.filter_tokens(tokens)
        tokens = self.lemmatize_tokens(tokens)
        return " ".join(tokens).strip()


# ---------------------------------------------------------------------------
# Singleton accessor — shared instance across preprocess.py
# ---------------------------------------------------------------------------
_default_preprocessor: TextPreprocessor | None = None


def get_preprocessor() -> TextPreprocessor:
    """
    Return a shared TextPreprocessor instance (lazy singleton).

    Avoids re-initializing NLTK resources and re-downloading corpora for
    every one of ~800 filing records.

    Returns:
        Module-level TextPreprocessor with default settings.
    """
    global _default_preprocessor
    if _default_preprocessor is None:
        _default_preprocessor = TextPreprocessor()
    return _default_preprocessor
