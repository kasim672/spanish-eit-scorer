"""
eit_scorer/core/idea_units.py
==============================
Idea unit extraction and analysis.

Idea units are the meaningful propositional chunks of a sentence.
In EIT scoring, we approximate idea units using content words
(nouns, verbs, adjectives, adverbs) vs. function words
(articles, prepositions, conjunctions, clitics).

Ortega (2000) defines idea units as the semantic building blocks
that carry propositional meaning. Without a formal IU parser,
content-word coverage is the best deterministic proxy.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class IdeaUnitConfig:
    """Configuration for idea unit extraction."""
    
    # Function words (low semantic content)
    function_words: set[str] = field(default_factory=lambda: {
        # Articles
        "el", "la", "los", "las", "un", "una", "unos", "unas",
        # Prepositions
        "a", "de", "en", "con", "por", "para", "sin", "sobre",
        "entre", "hasta", "desde", "hacia", "durante", "ante",
        # Contractions (pre-expansion)
        "del", "al",
        # Conjunctions
        "que", "y", "e", "o", "u", "pero", "sino", "si",
        "aunque", "cuando", "donde", "como", "porque",
        "mientras", "después", "antes", "para",
        # Clitics & pronouns
        "me", "te", "se", "lo", "la", "le", "nos", "os",
        "los", "las", "les", "mi", "tu", "su", "mí", "ti",
        # Common determiners / quantifiers treated as function
        "este", "ese", "aquel", "esta", "esa", "aquella",
        "estos", "esos", "aquellos", "estas", "esas", "aquellas",
        # Auxiliaries
        "ha", "han", "he", "has", "había", "habían",
        "ser", "estar", "haber", "es", "está", "son", "están",
        # Adverbs of manner/time (often function-like)
        "muy", "más", "menos", "bien", "mal", "aquí", "allí",
        "ahora", "entonces", "siempre", "nunca", "jamás",
    })
    
    # Near-synonym pairs: morphological variants and lexical near-synonyms
    # Stored as frozensets for O(1) lookup
    near_synonym_pairs: list[frozenset[str]] = field(default_factory=lambda: [
        # Tense/aspect variants of common verbs
        frozenset({"tiene", "tenía"}),
        frozenset({"tiene", "tuvo"}),
        frozenset({"es", "era"}),
        frozenset({"es", "fue"}),
        frozenset({"está", "estaba"}),
        frozenset({"hace", "hacía"}),
        frozenset({"va", "iba"}),
        frozenset({"puede", "podía"}),
        frozenset({"quiere", "quería"}),
        frozenset({"sabe", "sabía"}),
        frozenset({"dice", "decía"}),
        frozenset({"viene", "venía"}),
        frozenset({"pone", "ponía"}),
        frozenset({"come", "comía"}),
        frozenset({"bebe", "bebía"}),
        frozenset({"duerme", "dormía"}),
        frozenset({"juega", "jugaba"}),
        frozenset({"corre", "corría"}),
        frozenset({"salta", "saltaba"}),
        frozenset({"habla", "hablaba"}),
        # Number variants (singular/plural)
        frozenset({"niño", "niños"}),
        frozenset({"niña", "niñas"}),
        frozenset({"libro", "libros"}),
        frozenset({"casa", "casas"}),
        frozenset({"amigo", "amigos"}),
        frozenset({"amiga", "amigas"}),
        frozenset({"ciudad", "ciudades"}),
        frozenset({"país", "países"}),
        frozenset({"gato", "gatos"}),
        frozenset({"perro", "perros"}),
        frozenset({"persona", "personas"}),
        frozenset({"calle", "calles"}),
        frozenset({"mesa", "mesas"}),
        frozenset({"silla", "sillas"}),
        # Gender variants
        frozenset({"bueno", "buena"}),
        frozenset({"malo", "mala"}),
        frozenset({"nuevo", "nueva"}),
        frozenset({"viejo", "vieja"}),
        frozenset({"pequeño", "pequeña"}),
        frozenset({"grande", "grandes"}),
        frozenset({"hermoso", "hermosa"}),
        frozenset({"feo", "fea"}),
        frozenset({"joven", "jóvenes"}),
        frozenset({"alto", "alta"}),
        frozenset({"bajo", "baja"}),
        frozenset({"largo", "larga"}),
        frozenset({"corto", "corta"}),
        # Common lexical near-synonyms
        frozenset({"hablar", "decir"}),
        frozenset({"mirar", "ver"}),
        frozenset({"querer", "desear"}),
        frozenset({"empezar", "comenzar"}),
        frozenset({"terminar", "acabar"}),
        frozenset({"caminar", "andar"}),
        frozenset({"rápido", "rápidamente"}),
        frozenset({"lento", "lentamente"}),
        frozenset({"bonito", "hermoso"}),
        frozenset({"feo", "horrible"}),
        frozenset({"grande", "enorme"}),
        frozenset({"pequeño", "diminuto"}),
        frozenset({"triste", "infeliz"}),
        frozenset({"feliz", "alegre"}),
        frozenset({"cansado", "fatigado"}),
        frozenset({"asustado", "aterrado"}),
    ])


def extract_content_tokens(tokens: list[str], cfg: IdeaUnitConfig) -> list[str]:
    """
    Extract content tokens (idea units) from a token list.
    
    Content tokens are those that are NOT function words.
    These carry the propositional meaning of the sentence.
    """
    return [t for t in tokens if t.lower() not in cfg.function_words]


def extract_function_tokens(tokens: list[str], cfg: IdeaUnitConfig) -> list[str]:
    """
    Extract function tokens from a token list.
    
    Function tokens are articles, prepositions, conjunctions, etc.
    These provide grammatical structure but less semantic content.
    """
    return [t for t in tokens if t.lower() in cfg.function_words]


def count_idea_units(tokens: list[str], cfg: IdeaUnitConfig) -> int:
    """
    Count the number of idea units (content tokens) in a token list.
    """
    return len(extract_content_tokens(tokens, cfg))


def is_near_synonym(token1: str, token2: str, cfg: IdeaUnitConfig) -> bool:
    """
    Check if two tokens are near-synonyms (morphological variants or lexical near-synonyms).
    """
    t1_lower = token1.lower()
    t2_lower = token2.lower()
    
    if t1_lower == t2_lower:
        return True
    
    pair = frozenset({t1_lower, t2_lower})
    return pair in set(cfg.near_synonym_pairs)


def get_near_synonyms(token: str, cfg: IdeaUnitConfig) -> set[str]:
    """
    Get all near-synonyms of a token.
    """
    token_lower = token.lower()
    synonyms = set()
    
    for pair in cfg.near_synonym_pairs:
        if token_lower in pair:
            synonyms.update(pair - {token_lower})
    
    return synonyms
