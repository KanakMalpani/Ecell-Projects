"""
=============================================================================
NLTK Text Preprocessor — Query-Side NLP Normalization
=============================================================================

PURPOSE
-------
Provides configurable natural-language preprocessing for user queries before
embedding and retrieval. Uses NLTK corpora (stop words, WordNet) instead of
hardcoded word lists — a deliberate design choice for maintainability.

ROLE IN THE RAG PIPELINE
------------------------
  Used by orchestrate.py RAGPipeline._retrieve() to normalize queries:
    raw query → preprocess() → embedding → ChromaDB search

  IMPORTANT: Document chunks are NOT preprocessed this way during ingestion.
  Full vocabulary is preserved in the index for embedding quality; only queries
  are normalized to improve match against indexed prose.

PIPELINE (preprocess method):
  1. strip_boilerplate()  — remove PDF header/footer lines (regex)
  2. tokenize()           — NLTK word_tokenize + lowercase
  3. filter_tokens()      — drop stop words, punctuation, short tokens
  4. lemmatize_tokens()   — WordNet lemmatization (running → run)
  5. Rejoin → space-separated string for embedding

INTERVIEW TALKING POINTS
------------------------
1. **Query-only preprocessing:** Index stores raw chunk text; query gets
   stop-word stripped + lemmatized form — asymmetric but effective for retrieval.
2. **NLTK over hardcoded lists:** stopwords.words("english") is maintained corpus;
   avoids brittle custom filter lists that miss domain terms.
3. **extract_keywords():** Returns set[str] for keyword overlap in Ollama fallback
   (_fallback_answer) — used when LLM is offline.
4. **Lazy NLTK data download:** _ensure_nltk_data() downloads punkt/stopwords/wordnet
   on first use — smooth first-run experience without manual setup steps.
5. **Singleton via get_preprocessor():** Avoids re-downloading corpora and
   re-instantiating lemmatizer across requests.
6. **Boilerplate regex vs word filters:** Structural lines (Page X of Y, Document ID)
   removed via regex — not confused with semantic stop-word removal.
"""

from __future__ import annotations

import re
from functools import lru_cache

import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize

# -----------------------------------------------------------------------------
# Regex patterns — structural boilerplate (NOT semantic stop words)
# -----------------------------------------------------------------------------
# Interview: These target PDF layout artifacts, not content vocabulary.
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


# -----------------------------------------------------------------------------
# NLTK data bootstrap — auto-download corpora on first use
# -----------------------------------------------------------------------------
def _ensure_nltk_data() -> None:
    """
    Download required NLTK packages if not already present.

    Packages: punkt (tokenizer), stopwords, wordnet (lemmatizer), omw-1.4 (multilingual WordNet).
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
    """Load and cache English stop words from NLTK corpora."""
    _ensure_nltk_data()
    return frozenset(stopwords.words("english"))


# -----------------------------------------------------------------------------
# TextPreprocessor — configurable NLP pipeline class
# -----------------------------------------------------------------------------
class TextPreprocessor:
    """
    Configurable NLP preprocessor backed by NLTK.

    Parameters (from settings.yaml preprocessing section):
      remove_stopwords: strip common English words (the, is, at, …)
      lemmatize:        reduce to dictionary form (policies → policy)
      min_token_length: drop tokens shorter than this after tokenization
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
        """Split text into lowercase word tokens via NLTK word_tokenize."""
        return word_tokenize(text.lower())

    def filter_tokens(self, tokens: list[str]) -> list[str]:
        """
        Keep only meaningful tokens.

        Drops: punctuation-only tokens, stop words (if enabled), tokens below min_token_length.
        Uses NLTK stop word corpus — not a hardcoded list.
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
        """Reduce tokens to base form via WordNet lemmatizer (if lemmatize=True)."""
        if not self.lemmatize:
            return tokens
        return [self._lemmatizer.lemmatize(token) for token in tokens]

    def preprocess(self, text: str) -> str:
        """
        Full pipeline: strip → tokenize → filter → lemmatize → rejoin.

        Returns space-separated string ready for SentenceTransformer encoding.
        Used on user queries in RAGPipeline._retrieve().
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
        Return meaningful keyword set for overlap matching.

        Used in orchestrate._fallback_answer() when Ollama is offline —
        scores context lines by keyword intersection with query.
        """
        normalized = self.strip_boilerplate(text)
        tokens = self.tokenize(normalized)
        tokens = self.filter_tokens(tokens)
        tokens = self.lemmatize_tokens(tokens)
        return set(tokens)


# -----------------------------------------------------------------------------
# Module-level singleton accessor
# -----------------------------------------------------------------------------
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
